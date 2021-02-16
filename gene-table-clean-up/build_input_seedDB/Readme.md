## Introduction

Scripts to build an input file, to be used by importer to build/update seedDB gene tables.

## Usage

#### First, download latest HGNC table

Go to `https://www.genenames.org/download/statistics-and-files/`  
Under `Complete dataset download links` section `Complete HGNC approved dataset`  

#### Then, Run the script

```
python build-gene-table.py -i hgnc_download_nov_2_2020.txt -o final_gene_list_import.txt -m main-supp.txt -a alias-supp.txt
```

#### The final output file should include fields

```
entrez_id
symbol
chromosome
cytoband
type
synonyms
hgnc_id
ensembl_id
```

## Resources

`entrez-id-mapping.txt` generated from  
https://rb.gy/pqg455

`type-mapping.txt` generated from 
https://rb.gy/4wfl2k

`location-mapping.txt` generated from
https://rb.gy/vt2wsc
