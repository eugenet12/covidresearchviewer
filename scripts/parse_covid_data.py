# TODO: have code to generate and update web data
import logging
import os
import sys
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

# load local libraries
sys.path.append("/home/ubuntu/capstone_corona_search/modules")
import covid_docs
from utils.constants import *
from utils.web_utils import save_data_elasticsearch

if __name__ == "__main__":
    covid_docs.save_covid_only_data()
    df = covid_docs.load_covid_data(True)
    save_data_elasticsearch(df)
    covid_docs.save_drug_data()
