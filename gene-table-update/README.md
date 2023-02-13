# Introduction
This folder includes all the scripts needed for each new release to:
- generate `gene_info.txt` (input file for importer) to build gene tables in seedDB. 
- update exisitng data files accordingly
- Analyze gene loss in msigDB gene sets

## *Attention!* 
#### Before running the scripts for each update/release
- Compare selected version of [HGNC](https://www.genenames.org/download/statistics-and-files/) with [current DB](http://download.cbioportal.org/mysql-snapshots/mysql-snapshots-toc.html)
- update supplemental genes [HERE](https://github.com/cBioPortal/datahub-study-curation-tools/blob/master/gene-table-update/build-input-for-importer/supp-files/main-supp/bare-main-supp.txt) 
- update list of genes updated [HERE](https://github.com/cBioPortal/datahub-study-curation-tools/blob/master/gene-table-update/data-file-migration/outdated_entrez_ids.txt) and [HERE](https://github.com/cBioPortal/datahub-study-curation-tools/blob/master/gene-table-update/data-file-migration/outdated_hugo_symbols.txt)
