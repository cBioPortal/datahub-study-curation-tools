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

```Note: please remove the double quotes from the file and make sure it's Unicode(UTF-8) and Unix(LF) encoded```

#### Step 2 - Compare latest version of HGNC with current version used
***This step required manual curation.***

First, reduce the newly downloaded HGNC file to only `hgnc_id`, `symbol` and `locus_type` columns.
Then run the `diff` script [here](https://github.com/cBioPortal/datahub-study-curation-tools/tree/master/gene-table-update/hgnc-diff).   
The output would include 3 parts of changes genes between inquired versions: removed, added and updated (Output example [here](https://github.com/cBioPortal/datahub-study-curation-tools/blob/master/gene-table-update/hgnc-diff/examples/output/diff_mar_2021_vs_jan_2022.txt))
##### for genes removed
###### For protein-coding genes
  - First check if this is actually an update from an existing gene (search the entrez ID of this gene in NCBI); if no entrez ID could be found associated with this gene, then this gene would not be included in this new update. 
  - If yes, add entries for this update in data migration input list ([entrez ID](https://github.com/cBioPortal/datahub-study-curation-tools/blob/master/gene-table-update/data-file-migration/outdated_entrez_ids.txt) and [Hugo Symbol](https://github.com/cBioPortal/datahub-study-curation-tools/blob/master/gene-table-update/data-file-migration/outdated_entrez_ids.txt)); 
  - If not, add this entry to supp lists in the building script ([Main](https://github.com/cBioPortal/datahub-study-curation-tools/blob/master/gene-table-update/build-input-for-importer/supp-files/main-supp/complete-supp-main.txt) and [Alias](https://github.com/cBioPortal/datahub-study-curation-tools/blob/master/gene-table-update/build-input-for-importer/supp-files/alias-supp.txt))
*TODO: update this step for hg38 diverge*
###### For other type genes
  - no action needed
##### for genes updated
add the updates to the input lists for the data-file-migration script's input lists
[entrez ID](https://github.com/cBioPortal/datahub-study-curation-tools/blob/master/gene-table-update/data-file-migration/outdated_entrez_ids.txt) and/or [Hugo Symbol](https://github.com/cBioPortal/datahub-study-curation-tools/blob/master/gene-table-update/data-file-migration/outdated_hugo_symbols.txt)
##### for genes added
  - no action needed - just nice addition!
 
#### Step 3 - Build input `gene_info.txt` for importer

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

#### What's in the output file 
##### Header
Below header must be included in the output file as the first line.
```
entrez_id	symbol	chromosome	cytoband	type	synonyms	hgnc_id	ensembl_id
```
##### Content
The final output file should include fields below (NO SPACE should be included in any of the values listed below)
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
This file lists the genes that does not have an entrez_ID associated originally in HGNC.
For each symbol, it is either:
- assigned an entrez ID manually
- marked as `R` - meaning this entry will be exclude from our next gene table release

#### Supplemental Location `location-supp.txt`
Manually curated. `cytoband` and/or `chromosome` info extracted from archived NCBI and/or portal DB, to supplement HGNC download and supplemental gene lists. 
** gene entries with empty chromosome value will not be imported to the DB. 

## Troubleshooting

#### Case #1
When running the script with the updated HGNC download, some supplemental main entries would became available in the "new" HGNC.
This would cause ERRORs and script to exit.
```
Error: Duplicate entrez ID detected ...
``` 
To resolve ERRORs, remove this entry from `main-supp.txt`, or make the symbol as an alias to this entrez_ID.
If the hugo symbol got updated in the newly released HGNC, add the older symbol <> newer symbol combo to the data-file-migration input list [here](https://github.com/cBioPortal/datahub-study-curation-tools/blob/master/gene-table-update/data-file-migration/outdated_hugo_symbols.txt)

#### Case #2
With HGNC update, some entrez IDs in `alias-supp.txt` may become unavailable, and cause WARNINGs.
```
WARNING: ... entry is skipped - entrez ID does not exist in main table. (Redundancy)
```
To clear WARNINGs, remove this entry from the corresponding supplemental file `alias-supp.txt` as the log indicates.

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
