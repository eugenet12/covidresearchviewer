# MIDS Capstone - Coronavirus Research Portal

Live web app at [covidresearchviewer.com](https://www.covidresearchviewer.com)

## Download Data
Go to https://www.semanticscholar.org/cord19/download to download the raw data. You'll want the metadata and document parses data.


Our treatment data is from the [Milken Institute](https://covid-19tracker.milkeninstitute.org/).

## Codebase Structure
* `evaluation_data`: data used for evaluating our topic models and summaries based on papers aggregated by Washington University in St. Louis medical school
* `modules`: main paper processing code
* `scripts`: contains script that runs daily to update papers
* `webapp`: website code