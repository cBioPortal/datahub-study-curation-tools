# Introduction
Data curation scripts for [cBioPortal](cbioportal.org). 
Curated data sets can be found in [Datahub](https://github.com/cBioPortal/datahub).

# Directory layout
```
.
├── archive                         # legacy tools 
├── GN-annotation-wrapper           # MAF genome-nexus annotation 
├── add-clinical-header             # attach header lines to clinical files  
├── gene-table-update               # tools for updating seedDB gene tables  
├── generate-case-lists             # generate case lists  
├── hugo-symbol-corrector           # correct hugo symbols convereted to dates by Microsoft Excel 
├── TMB                             # tumor mutation burden calculation
├── validation                      # validator wrapper and tools for validator 
├── oncotree-code-converter         # add `cancer_type` and `cancer_type_detailed` based on oncotree code
├── map-ids                         # rewrite IDs used in a study sample/patient ID maps
├── subset-data                     # subset study based on sample/patient ID list
├── zscores                         # calculate z-scores
├── LICENSE  
└── README.md  
```
