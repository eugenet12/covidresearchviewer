"""Get documents on treatments"""
import nltk
import os
import pickle
import re
from collections import Counter, defaultdict


from covid_docs import load_covid_data
from utils.topic_extraction_utils import *
from utils.web_utils import *

RE_TOPIC = "treat[a-z]*"
FNAME = "web_data_treatment_papers.pkl"

def save_data_for_website(save_local=True, save_aws=False):
    """Save data for use with website
    
    Parameters
    ----------
    save_local: bool
        whether to save the data to a local location
    save_aws: bool
        whether to save the data to aws

    """
    df_treatment = get_papers()

    to_dump = get_data_for_web(df_treatment, RE_TOPIC)

    drug_counts, paper_counts = count_drugs_mentions(df_treatment)
    most_common_drugs = [drug for drug, count in drug_counts.most_common(n=10)]
    to_dump["most_common_drugs"] = drug_counts.most_common(n=10)

    drug_to_df = {}
    for drug in most_common_drugs:
        relevant_papers = [
            paper_id for paper_id, count in paper_counts[drug].items() if count > 5
        ]
        drug_to_df[drug] = df_treatment.loc[relevant_papers]
    to_dump["drugs_to_papers"] = {
        drug: df.iloc[0:10].reset_index().to_dict("records")
        for drug, df in drug_to_df.items()
    }
    if save_local:
        save_web_data_local(to_dump, FNAME)
    if save_aws:
        save_web_data_aws(to_dump, FNAME)


def count_drugs_mentions(df):
    """Counts how often a drug was mentioned in the text

    Parameters
    ----------
    df: DataFrame
        dataframe of drugs to

    Returns
    -------
    dict, dict
        The first dictionary contains how often each drug was mentioned.
        The second dictionary tracks, for each drug, how often it was mentioned in each paper.

    """
    drug_alias_to_name = get_drug_names()

    drug_counts = Counter()
    paper_counts = defaultdict(Counter)
    for cord_uid, row in df.iterrows():
        sentences = nltk.sent_tokenize(row["text"])
        for sent in sentences:
            for token in nltk.word_tokenize(sent):
                token = token.lower()
                if token in drug_alias_to_name:
                    # NOTE: this only works with single-word aliases
                    drug_name = drug_alias_to_name[token]
                    drug_counts[drug_name] += 1
                    paper_counts[drug_name][cord_uid] += 1
    return drug_counts, paper_counts


def get_papers():
    """Get papers discussing COVID-19 treatments

    Returns
    -------
    DataFrame
        dataframe of treatment documents

    """
    def count_treatments(df):
        # TODO: normalize by text length?
        return df["text"].str.count(RE_TOPIC)
    return filter_docs_by_count(count_treatments, 10)


def get_drug_names():
    """Load drug names

    Returns
    -------
    dict
        a map of drug alias to canonical name
    """
    with open(os.path.join(DATA_DIR, "drug_names.pkl"), "rb") as f:
        drug_alias_to_name = pickle.load(f)
    return drug_alias_to_name
