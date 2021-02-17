## Introduction

Scripts to build an input file, to be used by importer to build/update seedDB gene tables.

## Usage

#### Step 1 - download latest HGNC table

```
wget ftp://ftp.ebi.ac.uk/pub/databases/genenames/hgnc/tsv/hgnc_complete_set.txt
```

OR

Go to `https://www.genenames.org/download/statistics-and-files/`  
Under `Complete dataset download links` section, click `Complete HGNC approved dataset`  

#### Step 2 - Run the script

```
python build-gene-table.py -i hgnc_download_nov_2_2020.txt -o final_gene_list_import.txt -m main-supp.txt -a alias-supp.txt
```

## Output

The final output file should include fields below

```
entrez_id (not null, unique)
symbol (not null, unique)
chromosome
cytoband
type
synonyms
hgnc_id (unique)
ensembl_id (unique)
```

## Mappings

#### Entrez ID mapping `entrez-id-mapping.txt`

This file lists all the genes (`HUGO_GENE_SYMBOL`) in HGNC download file, that does not have an entrez_ID associated

For each symbol, it is either:
- assigned an entrez ID
- marched as `R` - meaning this entry will be exclude from the new/updated gene tables
in the 2nd column `STATUS`

When running the script with the updated HGNC download, some new entries would come up as 
```
Error: assign entrez ID to (OR delete) :
```
which would cause the script to exit. 
These new entries needs to be added to this mapping, and given a `STATUS` (entrez ID OR `R`),
to enable to script to run successfully. 
