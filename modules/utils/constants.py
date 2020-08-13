import os

DATA_DIR = os.environ.get(
    "COVID_WEBAPP_DATA_DIR", "/home/ubuntu/efs-mnt/latest_new/"
)

# elasticsearch index
ES_COL_TO_TYPE = {
    "cord_uid": {
        "type": "keyword"
    },
    "title":{  
        "type": "text",
    },
    "abstract": {
        "type": "text",
    },
    "text": {
        "type": "text"
    },
    "authors": {
        "type": "keyword"
    },
    "journal": {
        "type": "keyword"
    },
    "url": {
        "type": "text"
    },
    "publish_date": {
        "type": "date"
    }, 
    "publish_date_for_web": {
        "type": "keyword"
    },
    "embedding": {
        "type": "float"
    },
    "language": {
        "type": "keyword"
    },
    "topic_diagnosis": {
        "type": "boolean"
    },
    "topic_epidemiology": {
        "type": "boolean"
    },
    "topic_prevention": {
        "type": "boolean"
    },
    "topic_transmission": {
        "type": "boolean"
    },
    "topic_treatment": {
        "type": "boolean"
    },
    "topic_vaccine": {
        "type": "boolean"
    },
    "topics": {
        "type": "keyword"
    },
    "scibert_summary_short": {
        "type": "text"
    },
    "scibert_summary_short_cleaned": {
        "type": "text"
    },
    "top_keywords": {
        "type": "keyword"
    },
    "is_peer_reviewed": {
        "type": "boolean"
    },
    "summary_length": {
        "type": "long"
    },
    "is_clinical_paper": {
        "type": "boolean"
    },
}
ES_INDEX = "cord19-docs"
ES_URL = "https://search-es-covid-research-n6etnstkyvx6k2oxrlavq66sia.us-east-2.es.amazonaws.com/"

TREATMENT_ES_COL_TO_TYPE = {
    "clinical_trial_id": {
        "type": "keyword"
    },
    "date_last_updated": {
        "type": "date"
    },
    "developer": {
        "type": "keyword"
    },
    "fda_approval": {
        "type": "text"
    },
    "funder": {
        "type": "keyword"
    },
    "has_emerg_use_auth": {
        "type": "keyword"
    },
    "name": {
        "type": "keyword"
    },
    "next_steps": {
        "type": "text"
    },
    "phase": {
        "type": "keyword",
    },
    "product_category": {
        "type": "keyword",
    },
    "product_description": {
        "type": "text"
    },
    "published_results": {
        "type": "text"
    }, 
    "stage": {
        "type": "keyword"
    },
    "aliases": {
        "type": "keyword"
    },
    "num_paper_mentions": {
        "type": "long"
    },
}
TREATMENT_ES_INDEX = "cord19-treatments"