## Introduction
Scripts to compare all gene sets in msigDB used by current version of seedDB (described [HERE](https://github.com/cBioPortal/datahub/blob/gene_update_doc/seedDB/Release-Notes.md#seed-database-schema-273)), to latest HGNC-based gene tables (described [HERE](https://github.com/cBioPortal/datahub-study-curation-tools/blob/master/gene-table-update/build-input-for-importer/Mar-11-2021-output/gene-import-input-Mar-11-2021.txt))

## Usage
```
geneSetComp.py [-h] -i INPUT_MSIGDB_FILE -r INPUT_HGNC_FILE
```
##### Example
```
python geneSetComp.py -i msigdb_download/msigdb_v6.1.xml -r ../build-input-for-importer/Mar-11-2021-output/gene-import-input-Mar-11-2021.txt
```
##### Commandline
```
  -h, --help            show this help message and exit
  -i INPUT_MSIGDB_FILE, --input-msigdb-file INPUT_MSIGDB_FILE
                        (Required) msigDB file
  -r INPUT_HGNC_FILE, --input-hgnc-file INPUT_HGNC_FILE
                        (Required) Gene Table file
```

Output file includes all genes with status either:
- all genes are included in the lastest gene tables 
- list of missing genes (entrez_ID + symbol, sometimes either is missing by resource)
