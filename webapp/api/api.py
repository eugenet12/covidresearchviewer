import os

import json
import pickle
import requests
import time
from cachetools import TTLCache, cached
from datetime import datetime, timedelta
from functools import lru_cache
from io import StringIO

import numpy as np
import pandas as pd
from elasticsearch import Elasticsearch
from flask import Flask, request, json, jsonify
from gensim.models import FastText
from nltk import ngrams
from s3fs.core import S3FileSystem

app = Flask(__name__)

COLS_TO_KEEP = [
    "cord_uid",
    "title",
    "abstract",
    "url",
    "text",
    "authors",
    "publish_date_for_web",
    "scibert_summary_short",
    "scibert_summary_short_cleaned",
    "topics",
    "journal",
    "top_keywords",
    "is_peer_reviewed",
    "is_clinical_paper",
]

# elasticsearch settings
ES_CLUSTER_URL = "https://search-es-covid-research-n6etnstkyvx6k2oxrlavq66sia.us-east-2.es.amazonaws.com/"
INDEX = "cord19-docs"
TREATMENT_INDEX = "cord19-treatments"
es = Elasticsearch(ES_CLUSTER_URL)

# local cache of data
DATA_DIR = os.environ.get("COVID_WEBAPP_DATA_DIR", "/home/ubuntu/efs-mnt/latest")

# s3 client
ACCESS_KEY = "AKIAT7JLV7IH5TNZAUTR"
SECRET_ACCESS_KEY = "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"
BUCKET = "covid-research-data"
s3_client = S3FileSystem(key=ACCESS_KEY, secret=SECRET_ACCESS_KEY)

STOPWORDS = {
    "ourselves",
    "hers",
    "between",
    "yourself",
    "but",
    "again",
    "there",
    "about",
    "once",
    "during",
    "out",
    "very",
    "having",
    "with",
    "they",
    "own",
    "an",
    "be",
    "some",
    "for",
    "do",
    "its",
    "yours",
    "such",
    "into",
    "of",
    "most",
    "itself",
    "other",
    "off",
    "is",
    "s",
    "am",
    "or",
    "who",
    "as",
    "from",
    "him",
    "each",
    "the",
    "themselves",
    "until",
    "below",
    "are",
    "we",
    "these",
    "your",
    "his",
    "through",
    "don",
    "nor",
    "me",
    "were",
    "her",
    "more",
    "himself",
    "this",
    "down",
    "should",
    "our",
    "their",
    "while",
    "above",
    "both",
    "up",
    "to",
    "ours",
    "had",
    "she",
    "all",
    "no",
    "when",
    "at",
    "any",
    "before",
    "them",
    "same",
    "and",
    "been",
    "have",
    "in",
    "will",
    "on",
    "does",
    "yourselves",
    "then",
    "that",
    "because",
    "what",
    "over",
    "why",
    "so",
    "can",
    "did",
    "not",
    "now",
    "under",
    "he",
    "you",
    "herself",
    "has",
    "just",
    "where",
    "too",
    "only",
    "myself",
    "which",
    "those",
    "i",
    "after",
    "few",
    "whom",
    "t",
    "being",
    "if",
    "theirs",
    "my",
    "against",
    "a",
    "by",
    "doing",
    "it",
    "how",
    "further",
    "was",
    "here",
    "than",
}


def _load_pkl_from_s3(path):
    """Loads pickle file from s3 given the path"""
    if not os.path.exists(os.path.join(DATA_DIR, path)):
        s3_client.get(os.path.join(BUCKET, path), os.path.join(DATA_DIR, path))
    with open(os.path.join(DATA_DIR, path), "rb") as f:
        return pickle.load(f)


@cached(cache=TTLCache(maxsize=1, ttl=60 * 60))
def _load_covid_df():
    """Load covid df"""
    return _load_pkl_from_s3("web_data_v2.pkl")["raw"]


@cached(cache=TTLCache(maxsize=1, ttl=60 * 60))
def _load_semantic_index():
    """Load semantic index"""
    return _load_pkl_from_s3("semantic_index_text_only.pkl")


@cached(cache=TTLCache(maxsize=1, ttl=60 * 60))
def _load_text_embedding():
    """Load embedding on the text"""
    files_to_copy = [
        "fasttext_textonly_embeddings.ft",
        "fasttext_textonly_embeddings.ft.wv.vectors_ngrams.npy",
        "fasttext_textonly_embeddings.ft.trainables.vectors_ngrams_lockf.npy",
    ]
    for f in files_to_copy:
        if not os.path.exists(os.path.join(DATA_DIR, f)):
            s3_client.get(os.path.join(BUCKET, f), os.path.join(DATA_DIR, f))
    return FastText.load(os.path.join(DATA_DIR, "fasttext_textonly_embeddings.ft"))


@app.route("/api/healthcheck")
def healthcheck():
    """Healthcheck api
    
    Returns
    ------
    dict
        a response containing the word "success"
    """
    return {"isHealthy": True}


@app.route("/api/get-recent-topic-research-papers")
def get_recent_topic_papers():
    """Get recent papers based on query

    Returns
    -------
    dict
        a response containing research papers in the right format

    """
    query = request.args.get("query")
    query_filter = request.args.get("filters")
    size = int(request.args.get("size", 10))
    papers = _get_search_results(query, query_filter, size)
    return {"data": [row["_source"] for row in papers]}


@app.route("/api/get-recent-paper-distribution")
def get_recent_paper_distribution():
    """Get paper distribution based on query"""
    query = request.args.get("query")
    query_filters = request.args.get("filters")
    lucene_query = _get_lucene_query(query, query_filters, ngram_length=1)

    aggregation = {
        "query": {"query_string": {"query": lucene_query}},
        "aggs": {
            "papers_over_time": {
                "date_histogram": {"field": "publish_date", "calendar_interval": "week"}
            }
        },
        "size": 0,
    }
    res = es.search(body=aggregation, index=INDEX)

    # return aggregation for last 60 days
    return {
        "data": [
            (row["key"], row["doc_count"])
            for row in res["aggregations"]["papers_over_time"]["buckets"][-60:]
        ]
    }


def _create_search_query(query, size):
    """Get search results based on the provided query / size"""
    query = {
        "_source": COLS_TO_KEEP,
        "query": {"query_string": {"query": query}},
        "highlight": {
            "fields": {
                "text": {"fragment_size": 300, "pre_tags": "<b>", "post_tags": "</b>"},
                "title": {"fragment_size": 300, "pre_tags": "<b>", "post_tags": "</b>"},
                "abstract": {
                    "fragment_size": 300,
                    "pre_tags": "<b>",
                    "post_tags": "</b>",
                },
            }
        },
        "size": size,
        "sort": [{"publish_date": {"order": "desc"}}],
    }
    return query


def _is_text_query(query):
    """Returns whether the query is querying the text"""
    return not (
        query.startswith("cord_uid:")
        or query.startswith("title:")
        or query.startswith("topics:")
    )


def _get_lucene_query(query, query_filters, ngram_length=None):
    """Get lucene query given the query and query filters"""
    is_text_query = _is_text_query(query)
    if is_text_query:
        if ngram_length is not None:
            tokens = [token for token in query.split(" ") if token not in STOPWORDS]
            tokens = [" ".join(ngram) for ngram in ngrams(tokens, ngram_length)]
            new_query = '("' + '" "'.join(tokens) + '")'
            lucene_query = (
                f"text:{new_query} OR title:{new_query} OR abstract:{new_query}"
            )
        else:
            # normal case
            lucene_query = f'text:"{query}" OR title:"{query}" OR abstract:"{query}"'
    else:
        # special case to allow us to search for topics by cord uid
        lucene_query = f"{query}"
    return f"(({lucene_query}) {query_filters}) AND summary_length:>0"


def _get_search_results(query, query_filters, size):
    """Get search results given the query and query filters"""
    is_text_query = _is_text_query(query)
    lucene_query = _get_lucene_query(query, query_filters)
    res = es.search(body=_create_search_query(lucene_query, size), index=INDEX)

    # try a more flexible text query
    papers = res["hits"]["hits"]
    for ngram_length in [3, 2, 1]:
        if len(papers) < size and is_text_query and len(query.split(" ")) > ngram_length:
            lucene_query = _get_lucene_query(query, query_filters, ngram_length)
            res = es.search(body=_create_search_query(lucene_query, size), index=INDEX)
            papers += res["hits"]["hits"]

    return papers


@app.route("/api/get-paper-search-results")
def get_search_results():
    """Get search results based on user query"""
    query = request.args.get("query")
    query_filters = request.args.get("filters")
    size = int(request.args.get("size", 10))
    papers = _get_search_results(query, query_filters, size)

    to_return = []
    for row in papers[0 : min(size, len(papers))]:
        doc = row["_source"].copy()
        if "highlight" in row:
            doc["sample_sentences"] = row["highlight"]
        to_return.append(doc)
    return {"data": to_return}


@app.route("/api/get-top-treatments")
def get_top_treatments():
    """Get the names and counts of the top treatments"""
    size = request.args.get("size", 10)
    query = {
        "_source": ["name", "num_paper_mentions"],
        "size": size * 2,
        "sort": [{"num_paper_mentions": {"order": "desc"}}],
    }
    res = es.search(body=query, index=TREATMENT_INDEX)
    data = []
    seen_drugs = set()
    for row in res["hits"]["hits"]:
        drug_name = row["_source"]["name"]
        if not drug_name in seen_drugs:
            data.append(row["_source"])
            seen_drugs.add(drug_name)

    return {"data": data[0:10]}


@app.route("/api/get-treatment-data")
def get_treatment_data():
    """Get relevant treatment data"""
    name = request.args.get("name")
    query = {
        "_source": [
            "clinical_trial_id",
            "date_last_updated",
            "developer",
            "funder",
            "has_emerg_use_auth",
            "name",
            "next_steps",
            "product_category",
            "product_description",
            "published_results",
            "stage",
            "aliases",
            "num_paper_mentions",
        ],
        "query": {"query_string": {"query": f"name:{name}"}},
        "size": 1,
        "sort": [{"num_paper_mentions": {"order": "desc"}}],
    }
    res = es.search(body=query, index=TREATMENT_INDEX)
    if len(res["hits"]["hits"]) > 0:
        return {"data": res["hits"]["hits"][0]["_source"]}
    else:
        return {"data": {}}


if __name__ == "__main__":
    # default port 5000
    from waitress import serve

    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

