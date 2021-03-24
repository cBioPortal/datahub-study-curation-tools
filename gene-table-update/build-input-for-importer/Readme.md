<span style="color:red">**ALWAYS update** the supp files first before running the scripts.</span> Instructions [HERE](https://github.com/cBioPortal/datahub-study-curation-tools/blob/master/gene-table-update/build-input-for-importer/Readme.md#supp-files)

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
- Gene data file: the output file would be deposited under the same directory and named as `gene-import-input-_date_.txt` if not specified otherwise
- Log file: a log file would be generated under the same directory and named `gene-import-input-_date_.log` 
- Rename the output file `gene-import-input-_date.txt` (or customized name) to `gene_info.txt`, and archive the output into the `archive` folder

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
See example here: [Mar 11, 2021 build](https://raw.githubusercontent.com/cBioPortal/datahub-study-curation-tools/master/gene-table-update/build-input-for-importer/archive/Mar-11-2021-output/gene-import-input-Mar-11-2021.txt)

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
Reference for previous analysis: [HGNC vs current DB data availibility comparison analysis](https://rb.gy/rbfdnl)

#### Supplemental main genes `main-supp.txt`
Genes to supplement to HGNC download as main genes.

#### Supplemental alias genes `alias-supp.txt`
Genes to supplemen to HGNC download as alias genes.

#### Supplemental Entrez ID `entrez-id-supp.txt`
This file lists all the genes (`HUGO_GENE_SYMBOL`) in HGNC download file, that does not have an entrez_ID associated originally
For each symbol, it is either:
- assigned an entrez ID
- marched as `R` - meaning this entry will be exclude from the new/updated gene tables
in the 2nd column `STATUS`
** gene entries with empty chromosome value will not be imported to the DB. 

#### Supplemental Location `location-supp.txt`
Manually curated. `cytoband` and/or `chromosome` info extracted from archived NCBI and/or portal DB, to supplement HGNC download and supplemental gene lists. 

### Steps for updating supp files
#### Step 1 - Generate a list to include ALL genes
- used by at least one profile in any public study
- include field `hugo_symbol`, `entrez_id`
- exclude `miRNA`, `phosphoprotein` genes

#### Step 2 - Compare list with HGNC
- compare lastest HGNC download with current list
- combine `hugo_symbol` & `entrez_id` as combo key
- manually curate for each results
-- hugo_symbol match, entrez_id match
-- hugo_symbol match, entrez_id unmatch
-- hugo_symbol unmatch, entrez_id match
-- hugo_symbol unmatch, entrez_id unmatch

#### Step 3 - Adjust supplemental lists
-- for existing genes removed with update, manual curation is needed to decide if this gene should be include in the supplemental lists
-- for exisitng genes updated, add gene to list under `data-file-migration`  

## Troubleshooting

#### Case #1
When running the script with the updated HGNC download, some supplemental main entries would became available in the "new" HGNC.
This would cause ERRORs and script to exit.
```
Error: Duplicate entrez ID detected ...
``` 
To resolve ERRORs, remove this entry from `main-supp.txt`, or make it as an alias.

#### Case #2
With HGNC update, some entrez IDs may become unavailable, and cause WARNINGs.
```
WARNING: ... entry is skipped - entrez ID does not exist in main table. (Redundancy)
```
To clear WARNINGs, remove this entry from `alias-supp.txt`.

#### Case #3
When running the script with the updated HGNC download, some new entries would come up and without an entrez ID assigned.  
This would cause ERRORs and script to exit.
```
Error: assign entrez ID to (OR delete)
```
To resolve ERRORs, add logged entries to `entrez-id-supp.txt` and give each a `STATUS` (assign an `entrez ID` OR `R`).

#### Case #4
With HGNC update, some entries may get new location information in HGNC, and cause WARNINGs.
```
WARNING: ... entry already have location info. (Redundancy and possible conflicts)
```
To clear WARNINGs, remove this entry from `location-supp.txt`

#### Case #5
With HGNC update, some entrez ID may become unavailable, and cause WARNINGs.
```
WARNING: ... entry is skipped - entrez ID does not exist in main table. (Redundancy)
```
To clear WARNINGs, remove this entry from `location-supp.txt`

