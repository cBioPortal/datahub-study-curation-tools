## Introduction

Scripts to build an input file, to be used by importer to build/update seedDB gene tables.  
- [Project Background Presentation](https://rb.gy/4rvgf9) 
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
python build-gene-table-input.py -i hgnc_complete_set.txt -m supp-files/main-supp/complete_supp_main.txt -a supp-files/alias-supp.txt -o final_gene_import_file.txt
```
##### Commandline
```
  -h, --help            show this help message and exit
  -i INPUT_HGNC_FILE, --input-hgnc-file INPUT_HGNC_FILE
                        (Required)Downloaded HGNC file
  -m INPUT_SUPP_MAIN_FILE, --input-supp-main-file INPUT_SUPP_MAIN_FILE
                        (Required)File of genes to supplement to main table
  -a INPUT_SUPP_ALIAS_FILE, --input-supp-alias-file INPUT_SUPP_ALIAS_FILE
                        (Required)File of genes to supplement to alias table
  -o OUTPUT_FILE_NAME, --output-file-name OUTPUT_FILE_NAME
                        (Required)Name of the output file
```

## Output

The final output file should include fields below
| FIELD_NAME | VALUE| DISTINCT? |
|----------|----------|---------|
| entrez_id | NOT NULL| YES |
|symbol| NOT NULL | YES |
|chromosome |1-22, M, X, Y, NULL|NO|
|cytoband |could be NULL|NO|
|type |protein-coding, ncRNA, rRNA, tRNA, snRNA, snoRNA, pseudogene, unknown, other|NO|
|synonyms |separate with `\|`|NO|
|hgnc_id |could be NULL|YES|
|ensembl_gene_id |could be NULL|YES|

## Mappings
The files under `mappings` folders define some rules and/or mappings between HGNC vs. Portal, used by the script. 

#### Entrez ID mapping `entrez-id-mapping.txt`

This file lists all the genes (`HUGO_GENE_SYMBOL`) in HGNC download file, that does not have an entrez_ID associated originally

For each symbol, it is either:
- assigned an entrez ID
- marched as `R` - meaning this entry will be exclude from the new/updated gene tables
in the 2nd column `STATUS`

When running the script with the updated HGNC download, some new entries would come up as 
```
Error: assign entrez ID to (OR delete)
```
which would cause the script to exit. 
These new entries need to be added to this mapping files, and given a `STATUS` (entrez ID OR `R`),
to enable to script to run successfully. 

#### Type mapping `type-mapping.txt`
Mapping between HGNC `locus_group` and `locus_type` vs. portal DB `type`

#### Location mapping `location-mapping.txt`
Mapping between HGNC `location` vs. portal DB `chromosome` and `cytoband`
This list contains all the "unconvention" values in the HGNC `location` columns, and their corresponding values in portal DB. 
For `location` values that follows the standard format (e.g. `19q13.12`, `4q31.21-q31.22`), just parsing by arms (`q` or `p`) to obtain `chromosome`.

## Supp Files
To reduce data loss caused by gene table udpates, we supplemental some important genes.  
Details at [HGNC vs current DB data availibility comparison analysis](https://rb.gy/rbfdnl)

#### Supplemental main genes `supp-main.txt`
Genes to supplement to HGNC download as main genes.
When running the script with the updated HGNC download, some supplemental main entries would became part of updated HGNC, 
and cause ERRORS as below 
```
Error: Duplicate entrez ID detected
```
which would cause the script to exit. 
Remove this entry from supp-main, or make it as an alias, to enable to script to run successfully. 

#### Supplemental alias genes `supp-alias.txt`
With HGNC update, some entrez ID may become unavailable, and cause WARNINGS as below
```
entry is skipped - entrez ID does not exist in main table
```
Remove this entry from supp-alias, to clear warnings.
