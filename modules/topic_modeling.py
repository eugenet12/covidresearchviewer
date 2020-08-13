import logging
import os
import pickle
import re
import string
from urllib.parse import urlparse

import gensim
import nltk
import numpy as np
import pandas as pd
from elasticsearch import Elasticsearch
from gensim.models.phrases import Phrases, Phraser
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer

from utils.constants import *

TOPICS = {
    "diagnosis": {"regex": "(diagno[a-z]*)|(test[a-z]*)", "min_count": 20},
    "epidemiology": {"regex": "epidemio[a-z]*", "min_count": 5},
    "prevention": {"regex": "prevent[a-z]*", "min_count": 5},
    "transmission": {"regex": "((transmi[a-z]*)|(spread[a-z]*))", "min_count": 20},
    "treatment": {"regex": "treat[a-z]*", "min_count": 10},
    "vaccine": {"regex": "(vacci[a-z]*)", "min_count": 10}
}

TOPICS_V4b = {
    "diagnosis": {"regex": "(diagno[a-z]*)|(test[a-z]*)|(detect[a-z]*)", "min_count": 20},
    "epidemiology": {"regex": "(epidemio[a-z]*)|(model[a-z]*)", "min_count": 10},
    "prevention": {"regex": "prevent[a-z]*", "min_count": 10},
    "transmission": {"regex": "((transmi[a-z]*)|(spread[a-z]*))", "min_count": 20},
    "treatment": {"regex": "((treat[a-z]*)|(drug[a-z]*))", "min_count": 20},
    "vaccine": {"regex": "(vacci[a-z]*)", "min_count": 10}
}


def _get_drug_names():
    """Get a list of drug names"""
    es = Elasticsearch(ES_URL)
    def flatten(l): return [item for sublist in l for item in sublist]
    drug_names = [x["_source"]["name"].split(", ") for x in es.search(
        index=TREATMENT_ES_INDEX, size=300)["hits"]["hits"] if x["_source"]["name"] != "unnamed"]
    return list(set(flatten(drug_names)))

flatten = lambda l: [item for sublist in l for item in sublist]

def _get_clinical_paper_ids():
    es = Elasticsearch(ES_URL)
    res = es.search(index=TREATMENT_ES_INDEX, size=300)
    paper_urls = [drug["_source"]["published_results"] for drug in res["hits"]["hits"]]
    paper_urls = flatten(paper_urls)
    url_re = re.compile(r"(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'.,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))")
    paper_urls_extracted = [url_re.findall(url) for url in paper_urls]
    paper_urls_extracted = set(flatten(paper_urls_extracted))
    paper_paths = [urlparse(url).path.lower() for url in paper_urls_extracted]
    paper_paths = [path for path in paper_paths if len(path.split("-")) < 5] # remove non-research links
    re_letters = re.compile(r"[a-z\.]+")
    re_doi = re.compile(r"[0-9]{2}\.[0-9]{4}")
    paper_paths_clean = ["/".join([y for y in x.split("/") if not re_letters.fullmatch(y) and not re_doi.fullmatch(y)]) for x in paper_paths]
    leading_slash = re.compile("^/")
    leading_2020 = re.compile("^2020")
    leading_pii = re.compile("^pii")
    def _clean_path(path):
        path = path.replace(".", "").replace(")", "").replace("(", "").replace("-", "")
        return leading_pii.sub("", leading_2020.sub("", leading_slash.sub("", path)))
    paper_paths_clean = [_clean_path(path) for path in paper_paths_clean]
    paper_paths_clean = [path for path in paper_paths_clean if len(path) > 8]
    return paper_paths_clean

def _is_clinical_paper(urls, paper_paths_clean):
    """Returns whether paper is a clinical paper"""
    for url in urls:
        path = urlparse(url).path.lower().replace(".","").replace(")", "").replace("(", "").replace("-", "")
        for paper_path in paper_paths_clean:
            if paper_path in path:
                return True
    return False

def _get_topic_list(row):
    row_topics = []
    for topic in TOPICS.keys():
        if row[f"topic_{topic}"]:
            row_topics.append(topic)
    return row_topics


def add_topics(df):
    """Add topics to the given dataframe

    Performs the addition in-place

    Parameters
    ----------
    df: DataFrame
        source dataframe to add topics to

    """
    # get drug names for treatments
    drug_names = _get_drug_names()
    drug_names = [x.replace("(", "\(").replace(")", "\)").replace(
        "-", "\-") for x in drug_names]
    drug_re = "(" + ")|(".join(drug_names) + ")"
    for topic, params in TOPICS_V4b.items():
        title_counts = df["title"].str.lower().str.count(
            params["regex"]).fillna(0)
        abstract_counts = df["abstract"].str.lower(
        ).str.count(params["regex"]).fillna(0)
        text_counts = df["text"].str.lower().str.count(
            params["regex"]).fillna(0)
        topic_counts = 5 * title_counts + 3 * abstract_counts + text_counts
        # special case to look for drugs. This might take a very long time
        if topic == "treatment":
            title_counts = df["title"].str.lower().str.count(drug_re).fillna(0)
            abstract_counts = df["abstract"].str.lower(
            ).str.count(drug_re).fillna(0)
            text_counts = df["text"].str.lower().str.count(drug_re).fillna(0)
            topic_counts += 5 * title_counts + 3 * abstract_counts + text_counts
        df[f"topic_{topic}"] = topic_counts >= params["min_count"]
    df["topics"] = df.apply(_get_topic_list, axis=1)
    return df


def add_topics_v1(df):
    """Add topics to the given dataframe

    Performs the addition in-place

    Parameters
    ----------
    df: DataFrame
        source dataframe to add topics to

    """
    for topic, params in TOPICS.items():
        topic_counts = df["text"].str.count(params["regex"])
        df[f"topic_{topic}"] = topic_counts >= params["min_count"]
    df["topics"] = df.apply(_get_topic_list, axis=1)


def add_is_clinical(df):
    """Add column to indicate whether a paper is a clinical result"""
    df["is_clinical_paper"] = df.url.str.split("; ").apply(_is_clinical_paper, paper_paths_clean=_get_clinical_paper_ids())
    
    
def add_keywords(df):
    """Add topics to the given dataframe

    Performs the addition in-place

    Parameters
    ----------
    df: DataFrame
        source dataframe to add topics to

    """
    retrain_phraser(df)
    extract_keywords(df)

    ID_TO_KEYWORD_PATH = "cord_uid_to_keywords.pkl"
    with open(os.path.join(DATA_DIR, ID_TO_KEYWORD_PATH), "rb") as f:
        cord_uid_to_top_keywords = pickle.load(f)
    print("Keyword counts", len(cord_uid_to_top_keywords), len(df))
    # assert(len(cord_uid_to_top_keywords) >= len(df))
    df["top_keywords"] = df["cord_uid"].map(
        cord_uid_to_top_keywords).fillna("")
    df["top_keywords"] = df["top_keywords"].apply(
        lambda l: l if isinstance(l, list) else [])
    df["top_keywords"] = df["top_keywords"].apply(
        lambda l: [x.replace("_", " ") for x in l])


def retrain_phraser(df):
    """Retrain phrase generator

    Parameters
    ----------
    df: DataFrame
        source dataframe to add topics to

    """
    all_sentences = []
    for cord_id, row in df.iterrows():
        title = row["title"]
        abstract = row["abstract"]
        full_text = row["text"]

        # tokenize doc to sentences
        for text in [title, abstract, full_text]:
            if type(text) is str:
                all_sentences += nltk.sent_tokenize(text)
    logging.info("Obtained all sentences")

    tokenized_sentences = []
    for sentence in all_sentences:
        tokenized_sentences.append([word.lower() for word in nltk.word_tokenize(
            sentence) if word not in set(string.punctuation)])
    logging.info("Tokenized sentences")

    phrases = Phrases(tokenized_sentences, min_count=5,
                      threshold=10, common_terms=set(stopwords.words("english")))
    logging.info("Trained phraser")
    with open(os.path.join(DATA_DIR, "phraser.pkl"), "wb") as f:
        pickle.dump(phrases, f)


def extract_keywords(df):
    """Extract keywords from the dataframe"""
    num_keywords = 20
    with open(os.path.join(DATA_DIR, "phraser.pkl"), "rb") as f:
        phrases = pickle.load(f)

    preprocessed_docs = []
    for cord_id, row in df.iterrows():
        title = "" if pd.isnull(row["title"]) else row["title"]
        abstract = "" if pd.isnull(row["abstract"]) else row["abstract"]
        full_text = "" if pd.isnull(row["text"]) else row["text"]

        text = title + " " + abstract + " " + full_text

        # tokenize doc to sentences
        preprocessed_doc = []
        text = text.replace("-", "_")
        for sentence in nltk.sent_tokenize(text):
            tokens = phrases[[word.lower()
                              for word in nltk.word_tokenize(sentence)]]
            preprocessed_doc += tokens
        preprocessed_docs.append(" ".join(preprocessed_doc))
    logging.info("Got preprocessed docs")

    vectorizer = TfidfVectorizer(ngram_range=(1, 1))
    X = vectorizer.fit_transform(preprocessed_docs)

    with open(os.path.join(DATA_DIR, "keywords_intermediate.pkl"), "wb") as f:
        pickle.dump({"sparse_results": X, "tfidf_vectorizer": vectorizer}, f)

    bad_words = ["covid", "cov", "sars", "mers", "coronavirus", "et_al", "table", "authors", "author",
                 "appendix", "data", "june", "posted", "license", "version", "preprint", "medrxiv", "review",
                 "science", "health", "study", "studies", "right", "reserved", "permission", "cc", "certified", "reuse",
                 "copyright", "tool", "model", "agent", "trial", "quarter", "factor", "sample", "level",
                 "january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
                 "november", "december", "case", "patient", "document", "usepackage", "state", "room", "people", "virus",
                 "viruses"]

    STOPLIST = re.compile(fr"(\b|_)({'|'.join(bad_words)})(\b|s|_)")

    def keep_word(word):
        num_digits = sum(char.isdigit() for char in word)
        return (
            STOPLIST.search(word) is None and
            not word.isdecimal() and
            not word.endswith("_") and
            not word.startswith("_") and
            not num_digits / len(word) >= 0.5 and
            word not in gensim.parsing.preprocessing.STOPWORDS and
            len(word) > 3
        )

    top_keywords = pd.Series([], dtype=str)
    for start_index in range(0, X.shape[0], 1000):
        logging.info(f"Extracting keywords {start_index} of {X.shape[0]}")
        end_index = start_index + 1000
        if end_index > X.shape[0]:
            X_subset = X.tocsr()[start_index:, ].todense()
        else:
            X_subset = X.tocsr()[start_index:end_index, ].todense()
        df_scores = pd.DataFrame(
            X_subset, columns=vectorizer.get_feature_names())
        df_scores = df_scores[filter(keep_word, df_scores.columns)]
        top_keywords = top_keywords.append(df_scores.apply(lambda x: list(
            x.sort_values(ascending=False).index[:num_keywords]), axis=1))

    df3 = df[["cord_uid"]].reset_index(drop=True)
    df3["top_keywords"] = top_keywords.reset_index(drop=True)
    cord_uid_to_top_keywords = df3[["cord_uid", "top_keywords"]].set_index(
        "cord_uid").to_dict()["top_keywords"]
    with open(os.path.join(DATA_DIR, "cord_uid_to_keywords.pkl"), "wb") as f:
        pickle.dump(cord_uid_to_top_keywords, f)
