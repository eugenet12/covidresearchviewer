"""Function to dump a covid dataframe for use downstream"""
import json
import logging
import os
import pandas as pd
import pickle
import requests
from collections import defaultdict
from datetime import datetime
from multiprocessing import Pool

from polyglot.detect import Detector

import summarization
import topic_modeling
from utils.constants import *
from utils.web_utils import *

DF_COVID_PATH = "df_covid.pkl"
DF_COVID_TEXT_ONLY_PATH = "df_covid_with_text.pkl"

def save_data_for_website(save_local=True, save_aws=False):
    """Save data for use with website

    Parameters
    ----------
    save_local: bool
        whether to save the data to a local location
    save_aws: bool
        whether to save the data to aws

    """
    df = load_covid_data(text_only=True)
    to_dump = get_data_for_web(df)
    if save_local:
        save_web_data_local(to_dump, "web_data_v2.pkl")
    if save_aws:
        save_web_data_aws(to_dump, "web_data_v2.pkl")


def load_covid_data(text_only=False):
    """Load covid data

    Parameters
    ----------
    text_only: bool
        whether to load the DataFrame for which we have full text only

    Returns
    -------
    DataFrame
        a dataframe of covid research papers

    """
    if text_only:
        with open(os.path.join(DATA_DIR, DF_COVID_TEXT_ONLY_PATH), "rb") as f:
            return pickle.load(f)
    else:
        with open(os.path.join(DATA_DIR, DF_COVID_PATH), "rb") as f:
            return pickle.load(f)


def save_covid_only_data():
    """Save a set of research papers that only discuss COVID-19

    Add on embeddings and text where relevant
    """
    # load metadata
    df_meta = pd.read_csv(os.path.join(DATA_DIR, "metadata.csv"))
    df_meta["publish_date"] = pd.to_datetime(
        df_meta["publish_time"], infer_datetime_format=True
    )
    # add whether paper was peer reviewed
    df_meta["is_peer_reviewed"] = is_peer_reviewed(df_meta)
    logging.info(f"Starting with {len(df_meta)} documents")

    # load embeddings
    logging.info("Adding embeddings")
    df_embeddings = pd.read_csv(
        os.path.join(DATA_DIR, "cord_19_embeddings.csv"), header=None
    )
    df_embeddings.set_index([0], inplace=True)

    # add embeddings to df_meta
    embedding_map = df_embeddings.to_dict()
    doc_to_embedding = defaultdict(list)
    for i in embedding_map.keys():
        dim_i = embedding_map[i]
        for doc_id in dim_i.keys():
            doc_to_embedding[doc_id].append(dim_i[doc_id])
    df_meta["embedding"] = df_meta["cord_uid"].map(doc_to_embedding)
    del df_embeddings, doc_to_embedding

    # filter to covid-only data
    logging.info("Filtering to Covid-only")
    def col_contains_covid(df, col):
        """Returns a flag if the given column mentions the coronavirus"""
        return (
            df[col].str.lower().str.contains("covid")
            | df[col].str.lower().str.contains("coronavirus")
            | df[col].str.lower().str.contains("sars-cov-2")
            | df[col].str.lower().str.contains("corona")
            | df[col].str.lower().str.contains("wuhan")
        )

    # we only want documents after covid was a thing, and before the current date
    logging.info("Filtering by date")
    date_flag = (
        df_meta["publish_date"] > datetime.strptime(
            "2019-12-01", "%Y-%m-%d")
    ) & (df_meta["publish_date"] < datetime.now())
    df_recent = df_meta[date_flag]
    df_covid = apply_text_filter(df_recent, col_contains_covid)
    del df_recent, df_meta

    # get a subset of covid papers that contain the text
    logging.info("Adding text")
    df_covid_with_texts = df_covid.dropna(subset=["sha"])
    df_covid_with_texts["pdf_filename"] = (
        df_covid_with_texts["pdf_json_files"].fillna("")
        + ";"
        + df_covid_with_texts["pmc_json_files"].fillna("")
    )
    df_covid_with_texts["text"] = df_covid_with_texts["pdf_filename"].apply(
        add_texts)

    logging.info("Filtering papers")
    
    # filter out papers with no title
    df_covid = df_covid.dropna(subset=["title"])
    df_covid_with_texts = df_covid_with_texts.dropna(subset=["title"])

    # filter out papers that are not in English
    df_covid_with_texts["language"] = df_covid_with_texts["text"].apply(
        detect_language)
    df_covid_with_texts = df_covid_with_texts[
        df_covid_with_texts["language"] == "English"
    ]

    logging.info("Adding metadata")
    # add useful metadata for EDA
    df_covid["title_length"] = df_covid["title"].str.split(" ").str.len()
    df_covid["abstract_length"] = df_covid["abstract"].str.split(" ").str.len()
    df_covid_with_texts["text_length"] = (
        df_covid_with_texts["text"].str.split(" ").str.len()
    )

    # sort data by publish date
    df_covid = df_covid.sort_values(by="publish_date", ascending=False)
    df_covid_with_texts = df_covid_with_texts.sort_values(
        by="publish_date", ascending=False)

    # add useful metadata for web
    df_covid["publish_date_for_web"] = df_covid["publish_date"].dt.strftime(
        '%b %d, %Y')
    df_covid_with_texts["publish_date_for_web"] = df_covid_with_texts["publish_date"].dt.strftime(
        '%b %d, %Y')
    
    # add topics
    logging.info("Adding topics")
    df_covid_with_texts = parallelize_dataframe(df_covid_with_texts, topic_modeling.add_topics)
    
    # add is_clinical
    logging.info("Adding is_clinical")
    topic_modeling.add_is_clinical(df_covid_with_texts)

    # add keywords
    logging.info("Adding keywords")
    topic_modeling.add_keywords(df_covid_with_texts)
    
    # add summaries
    logging.info("Adding summaries")
    summarization.summarize_text(df_covid_with_texts)
    summarization.clean_summaries(df_covid_with_texts)
    df_covid_with_texts["summary_length"] = df_covid_with_texts["scibert_summary_short_cleaned"].str.len()

    # save the data to disk
    logging.info("Saving to disk")
    with open(os.path.join(DATA_DIR, DF_COVID_PATH), "wb") as f:
        pickle.dump(df_covid, f)
    with open(os.path.join(DATA_DIR, DF_COVID_TEXT_ONLY_PATH), "wb") as f:
        pickle.dump(df_covid_with_texts, f)
    
    # save the data to s3
    logging.info("Saving to s3")
    save_web_data_aws(df_covid, DF_COVID_PATH)
    save_web_data_aws(df_covid_with_texts, DF_COVID_TEXT_ONLY_PATH)


def save_drug_data():
    """Save data on COVID-19 drugs"""
    # get treatment data from covid dashboard
    logging.info("Getting treatment data")
    link = "https://coviddashboard.eugenectang.com/api/treatments"
    f = requests.get(link)
    treatment_data = json.loads(f.text)
    raw_treatment_data = treatment_data["data"]["raw"]
    df = pd.DataFrame(raw_treatment_data)

    # get list of drug names from drugbank    
    logging.info("Compiling drug names")
    drug_names = load_web_data_aws("drug_names.pkl")
    flatten = lambda l: [item for sublist in l for item in sublist]
    treatment_names = set(flatten([row["name"].split(", ") for row in raw_treatment_data]))
    treatment_names.remove("unnamed") # remove unnamed treatments

    # create a map from name to aliases
    canonical_name_to_aliases = {}
    for alias, name in drug_names.items():
        if name in canonical_name_to_aliases:
            canonical_name_to_aliases[name].append(alias)
        else:
            canonical_name_to_aliases[name] = [alias]
    name_to_aliases = {}
    for name in treatment_names:
        if name in drug_names:
            canonical_name = drug_names[name]
            name_to_aliases[name] = canonical_name_to_aliases[canonical_name]
        else:
            name_to_aliases[name] = [name]
    df["aliases"] = df["name"].map(name_to_aliases).apply(lambda d: d if isinstance(d, list) else [])

    # count drug mentions
    logging.info("Count drug mentions")
    es = Elasticsearch(ES_URL)
    def _create_search_query(query, size):
        """Get search results based on the provided query / size"""
        query = {
            "_source": list(ES_COL_TO_TYPE.keys()),
            "query": {"query_string": {"query": query}},
            "size": size,
            "sort": [{"publish_date": {"order": "desc"}}],
        }
        return query
    def _count_drug_mentions(row):
        """Get number of times each drug is mentioned"""
        if row["name"] == "unnamed":
            return 0
        query = [row["name"]]
        if len(row["aliases"]) > 0:
            query = row["aliases"]
        lucene_query = '"' + '" OR "'.join(query) + '"'
        lucene_query = f"title:({lucene_query}) OR abstract:({lucene_query}) OR text:({lucene_query})"
        res = es.search(body=_create_search_query(lucene_query, 0), index=ES_INDEX)
        return res["hits"]["total"]["value"]
    df["num_paper_mentions"] = df.apply(_count_drug_mentions, axis=1)

    logging.info("Saving to ElasticSearch")
    save_treatments_to_elasticsearch(df)



def detect_language(text):
    """Detect the language of the text. 

    Parameters
    ----------
    text: str
        text for which to detect language

    Returns
    -------
    str
        language of the text. Returns English if not confident.

    """
    detector = Detector(text, quiet=True)
    # return English by default
    if not detector.reliable:
        return "English"
    for language in detector.languages:
        # return if there is > 90% confidence
        if language.confidence > 90:
            return language.name
    return "English"

def is_peer_reviewed(df):
    """Adds column for whether the paper is peer reviewed.
    
    Parameters
    ----------
    df: DataFrame
        input dataframe
    
    Returns
    -------
    Series
        series of whether each paper is peer reviewed

    """
    from_pr_source = df["source_x"].str.contains("PMC") | df["source_x"].str.contains("Medline") | df["source_x"].str.contains("Elsevier")
    from_nonpr_source = df["source_x"].str.contains("ArXiv") | df["source_x"].str.contains("BioRxiv") | df["source_x"].str.contains("MedRxiv")
    return from_pr_source & ~from_nonpr_source


def apply_title_filter(df, f):
    """Applies f on the title to get filtered results

    Parameters
    ----------
    df: DataFrame
        source data
    f: function
        a function that accepts a dataframe and a field name. and returns a boolean flag.

    Returns
    -------
    DataFrame
        a dataframe filtered based on f

    """
    title_flag = f(df, "title")
    return df[title_flag.fillna(False)]


def apply_text_filter(df, f):
    """Applies f on the title and abstract to get filtered results

    Parameters
    ----------
    df: DataFrame
        source data
    f: function
        a function that accepts a dataframe and a field name. and returns a boolean flag.

    Returns
    -------
    DataFrame
        a dataframe filtered based on f

    """
    title_flag = f(df, "title")
    abstract_flag = f(df, "abstract")
    return df[title_flag | abstract_flag]


def load_text(path):
    """Load text from path.

    Parameters
    ----------
    path: str
        pathfrom which to load text

    Returns
    -------
    str
        the loaded text

    """
    with open(os.path.join(DATA_DIR, path)) as f:
        sample_text = json.load(f)
        return "\n".join([body["text"] for body in sample_text["body_text"]])


def add_texts(paths):
    """Add texts to document. Finds the longest text and keeps it.

    Some parses from certain sources are better than others.

    Before doing this "longest" method, average text length as 2140
    After, it is 2244. 

    Parameters
    ----------
    paths: str
        paths to load separated by semicolon

    Returns
    -------
    str
        the loaded text

    """
    text = ""
    for path in paths.split(";"):
        path = path.strip()
        if len(path) == 0:
            continue
        path_text = load_text(path)
        if len(path_text) > len(text):
            text = path_text
    return text

def parallelize_dataframe(df, func, n_cores=16):
    """Parallelize a function over the dataframe
    
    Parameters
    ----------
    df: DataFrame
        dataframe of interest
    func: function
        function of interest
    n_cores: int
        number of cores to use

    """
    df_split = np.array_split(df, n_cores)
    pool = Pool(n_cores)
    df = pd.concat(pool.map(func, df_split))
    pool.close()
    pool.join()
    return df