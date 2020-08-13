"""General web utilities"""
import hashlib
import nltk
import numpy as np
import os
import pandas as pd
import pickle
import re
from collections import Counter
from datetime import datetime, timedelta

from elasticsearch import Elasticsearch
from s3fs.core import S3FileSystem

import topic_modeling
from utils.constants import *
from utils.topic_evaluation_utils import *


ACCESS_KEY = "AKIAT7JLV7IH5TNZAUTR"
SECRET_ACCESS_KEY = "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"
BUCKET = "covid-research-data"
s3_client = S3FileSystem(
    key = ACCESS_KEY,
    secret = SECRET_ACCESS_KEY)

def get_publish_dates(df):
    """Get time distribution of publish dates for the given dataframe

    Returns
    -------
    list[int]
        Time distribution in a format friendly towards HighCharts

    """
    return pd.to_datetime(df["publish_date"]).astype(np.int64) / int(1e6)


def get_sample_sentences(df, regex):
    """Get sample sentences that fit the regular expression

    Parameters
    ----------
    df: DataFrame
        dataframe for which to get sample sentences
    regex: str
        regex to match sentences on

    Returns
    -------
    Series
        A series of sample sentences

    """
    compiled_re = re.compile(regex)

    def extract_sentences(text):
        sents_to_return = []
        sentences = nltk.sent_tokenize(text)
        for sent in sentences:
            if compiled_re.search(sent.lower()) is not None:
                sents_to_return.append(sent)
        return sents_to_return
    return df["text"].apply(extract_sentences)


def get_data_for_web(df):
    """Get a baseline object to save for the website

    Parameters
    ----------
    df: DataFrame
        dataframe to save

    Returns
    -------
    Dict
        a dictionary object to save

    """
    # fill NAs because NAs can break flask's json protocol
    df.fillna("Missing", inplace=True)

    # for date histograms
    date_idx = pd.date_range(datetime.today().date() + timedelta(days=-60), datetime.today().date())

    to_dump = {"raw": df}

    # get per-topic data
    for topic, params in topic_modeling.TOPICS.items():
        df_topic = df[df[f"topic_{topic}"]]
        df_recent = df_topic.iloc[0:10]
        df_recent.loc[:, "sample_sentences"] = get_sample_sentences(
            df_recent, params["regex"])
        
        # get publish dates as a histogram for display on web
        # gets publish dates for last 60 days
        publish_dates = df_topic["publish_date"].value_counts()
        publish_dates = publish_dates.reindex(date_idx, fill_value=0)
        publish_date_distribution = list(zip(publish_dates.index.astype("int64")//(10**6), publish_dates))
        to_dump[topic] = {
            "distances": {
                "cluster": get_average_pairwise_distance(df_topic),
                "baseline": CORPUS_BASELINE
            },
            "recent_papers": df_recent.reset_index().to_dict("records"),
            "publish_dates": publish_date_distribution
        }

    # get overall data
    publish_dates = df["publish_date"].value_counts()
    publish_dates = publish_dates.reindex(date_idx, fill_value=0)
    publish_date_distribution = list(zip(publish_dates.index.astype("int64")//(10**6), publish_dates))
    to_dump["overall"] = {
        "recent_papers": df.iloc[0:10].reset_index().to_dict("records"),
        "publish_dates": publish_date_distribution
    }
    
    return to_dump

def save_web_data_local(to_dump, path):
    """Save data to a local path
    
    Parameters
    ----------
    to_dump: obj
        object to dump
    path: str
        path to dump object to relative to DATA_DIR

    """
    with open(os.path.join(DATA_DIR, path), "wb") as f:
        pickle.dump(to_dump, f)

def save_web_data_aws(to_dump, key):
    """Save data to aws 

    Parameters
    ----------
    to_dump: obj
        object to dump
    key: str 
        path to dump object to in bucket (bucket key)

    """
    with s3_client.open(os.path.join(BUCKET, key), "wb") as f:
        pickle.dump(to_dump, f)

def load_web_data_aws(key):
    """Load data from aws

    Parameters
    ----------
    key: str
        path to object in bucket (bucket key)

    """
    with s3_client.open(os.path.join(BUCKET, key), "rb") as f:
        return pickle.load(f)

def save_data_elasticsearch(df):
    """Save data to elasticsearch

    Parameters
    ----------
    df: DataFrame
        dataframe to dump

    """
    es = Elasticsearch(ES_URL)
    cols_to_index = ES_COL_TO_TYPE.keys()
    print("Indexing", cols_to_index)
    df_nona = df[cols_to_index].fillna("")
    df_nona["authors"] = df_nona["authors"].str.split(";")
    df_nona["journal"] = df_nona["journal"].str.split(";")
    df_nona["url"] = df_nona["url"].str.split(";").apply(lambda urls: [url.strip() for url in urls if not "api.elsevier.com" in url])

    # batch submit to ES
    batch = []
    for i,row in df_nona.iterrows():
        batch.append({"index": {"_index": ES_INDEX, "_id": row["cord_uid"]}})
        batch.append(row[cols_to_index].to_dict())
        # submit every 200
        if len(batch) % 400 == 0:
            print(f"Submitting batch {i}")
            es.bulk(batch, refresh=True)
            batch = []
    print("Submitting final batch")
    es.bulk(batch, refresh=True)
    print("Done!")
    

def save_treatments_to_elasticsearch(df):
    """Save treatment data to elasticsearch
    
    Parameters
    ----------
    df: DataFrame
        dataframe to dump

    """
    es = Elasticsearch(ES_URL)
    cols_to_index = TREATMENT_ES_COL_TO_TYPE.keys()
    print("Indexing", cols_to_index)
    df_nona = df[cols_to_index].fillna("")
    df_nona["clinical_trial_id"] = df_nona["clinical_trial_id"].str.split(", ")
    df_nona["developer"] = df_nona["developer"].str.split(", ")
    df_nona["published_results"] = df_nona["published_results"].str.split(", ")
    
    # batch submit to ES
    batch = []
    for i,row in df_nona.iterrows():
        row_id = hashlib.md5((", ".join(row["developer"]) + row["name"] + row["product_description"]).encode()).hexdigest()
        batch.append({"index": {"_index": TREATMENT_ES_INDEX, "_id": row_id}})
        batch.append(row[cols_to_index].to_dict())
        # submit every 200
        if len(batch) % 400 == 0:
            print(f"Submitting batch {i}")
            es.bulk(batch, refresh=True)
            batch = []
    print("Submitting final batch")
    es.bulk(batch, refresh=True)
    print("Done!")
    
