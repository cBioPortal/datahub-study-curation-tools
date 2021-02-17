## Introduction

Scripts to build an input file, to be used by importer to build/update seedDB gene tables.

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
python build-gene-table.py -i hgnc_complete_set.txt -o final_gene_list_import.txt -m main-supp.txt -a alias-supp.txt
```
##### Commandline
```
  -h, --help            show this help message and exit
  -i INPUT_HGNC_FILE_NAME, --input-hgnc-file-name INPUT_HGNC_FILE_NAME
                        downloaded HGNC file
  -m INPUT_SUPP_MAIN_FILE_NAME, --input-supp-main-name INPUT_SUPP_MAIN_FILE_NAME
                        File of genes to supplement to main table
  -a INPUT_SUPP_ALIAS_FILE_NAME, --input-supp-alias-name INPUT_SUPP_ALIAS_FILE_NAME
                        File of genes to supplement to alias table
  -o OUTPUT_FILE_NAME, --output-file-name OUTPUT_FILE_NAME
                        Name of the output file
```

## Output

The final output file should include fields below

```
entrez_id (not null, unique)
symbol (not null, unique)
chromosome (1-22, M, X, Y, "-")
cytoband
type
synonyms
hgnc_id (unique)
ensembl_id (unique)
```

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
Error: assign entrez ID to (OR delete) :
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
