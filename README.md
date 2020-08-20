# MIDS Capstone - Coronavirus Research Portal

Live web app at [covidresearchviewer.com](https:///www.covidresearchviewer.com)

## Download Data
Go to https://www.semanticscholar.org/cord19/download to download the raw data. You'll want the metadata and document parses data.

## Codebase Structure
* `evaluation_data`: data used to evaluate our summary model
* `modules`: core modules implementing the data pipeline
* `scripts`: script run daily to download new covid-19 papers
* `webapp`: web application code
