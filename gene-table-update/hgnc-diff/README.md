# Introduction
This script is used for comparing two different version of HGNC release/download.

## Before running
1. Download the released you want to compare from http://ftp.ebi.ac.uk/pub/databases/genenames/hgnc/archive/monthly/tsv/
2. Extract three columns `hgnc_id`, `symbol`, and `locus_type`

## How to use
````
python compare_hgnc_version.py -n [newer-version-hgnc-download-file-name] -o [older-version-hgnc-download-file-name]
````