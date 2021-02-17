
## Introduction
Scripts to build an input file, to be used by importer to build/update seedDB gene tables.  

## Background
- [Project Presentation](https://rb.gy/4rvgf9) 
- [News Release](https://rb.gy/njmzom)

## Usage

#### Step 1 - Download latest HGNC gene table

```
wget ftp://ftp.ebi.ac.uk/pub/databases/genenames/hgnc/tsv/hgnc_complete_set.txt
```

OR

Go to `https://www.genenames.org/download/statistics-and-files/`  
Under `Complete dataset download links` section, click `Complete HGNC approved dataset`  

```Note: please remove the double quotes from the file```

#### Step 2 - Run the script

##### Example
```
python build-gene-table-input.py -i hgnc_complete_set.txt
```
##### Commandline
```
  -h, --help            show this help message and exit
  -i INPUT_HGNC_FILE, --input-hgnc-file INPUT_HGNC_FILE
                        (Required)Downloaded HGNC file
  -o OUTPUT_FILE_NAME, --output-file-name OUTPUT_FILE_NAME
                        (Optional)Name of the output file
```

## Output
By dafault, the output file would be deposited under the same directory and named as `final_gene_list_import.txt`.

#### Content
The final output file should include fields below
| FIELD_NAME | VALUE|CAN BE NULL?| DISTINCT? |
|----------|----------|---------|-----|
| entrez_id | NUM | NO |YES |
|symbol| STR | NO | YES |
|chromosome |`1-22`,`M`, `X`, `Y`, `-`|NO|NO|
|cytoband |STR, `-`|NO|NO|
|type |`protein-coding`, `ncRNA`, `rRNA`, `tRNA`, `snRNA`, `snoRNA`, `pseudogene`, `unknown`, `other`|NO|NO|
|synonyms |STR(separate with `\|`)|YES|NO|
|hgnc_id |STR (start with `HGNC:`)|YES|NO|
|ensembl_gene_id |STR|YES|YES|

#### Example
See example here: Feb 17, 2021 build

## Mappings
The files under `mappings` folders define some rules and/or mappings between HGNC vs. Portal, used by the script. 

#### Type mapping `type-mapping.txt`
Mapping between HGNC `locus_group` and `locus_type` vs. portal DB `type`

#### Location mapping `location-mapping.txt`
Define mapping between HGNC `location` vs. portal DB `chromosome` and `cytoband`  
This list contains all the "unconvention" values in the HGNC `location` columns, and their corresponding values in portal DB. 
For `location` values that follows the standard format 
- Parse by arms `q` or `p` (e.g. `19q13.12`, `4q31.21-q31.22`) to obtain `chromosome`
- For empty values, use `-`

## Supp Files
To reduce data loss caused by gene table udpates, we supplemental some important genes.  
Details at [HGNC vs current DB data availibility comparison analysis](https://rb.gy/rbfdnl)

#### Supplemental main genes `main-supp.txt`
Genes to supplement to HGNC download as main genes.
When running the script with the updated HGNC download, some supplemental main entries would became part of updated HGNC, 
and cause ERRORS as below 
```
Error: Duplicate entrez ID detected ...
```
which would cause the script to exit. 
Remove this entry from `main-supp.txt`, or make it as an alias, to enable to script to run successfully. 

#### Supplemental alias genes `alias-supp.txt`
With HGNC update, some entrez ID may become unavailable, and cause WARNINGS as below
```
WARNING: ... entry is skipped - entrez ID does not exist in main table
```
Remove this entry from `alias-supp.txt`, to clear warnings.

#### Supplemental Entrez ID `entrez-id-supp.txt`

This file lists all the genes (`HUGO_GENE_SYMBOL`) in HGNC download file, that does not have an entrez_ID associated originally

For each symbol, it is either:
- assigned an entrez ID
- marched as `R` - meaning this entry will be exclude from the new/updated gene tables
in the 2nd column `STATUS`

When running the script with the updated HGNC download, some new entries in data files would come up as 
```
Error: assign entrez ID to (OR delete)
```
which would cause the script to exit. 
These new entries must be added to `entrez-id-supp.txt` and given a `STATUS` (assign an `entrez ID` OR `R`),
to enable to script to run successfully. 

#### Supplemental Location `location-supp.txt`
`cytoband` and/or `chromosome` info from NCBI and/or portal DB, to supplement HGNC download and supplemental gene lists. 

With HGNC update, some entries may get new location information in HGNC, and cause warnings as below 
```
WARNING: ... entry already have location info. 
```
Remove this entry from `location-supp.txt`, to clear warnings.

