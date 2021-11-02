# Introduction
Contains tools used by cBioPortal data curators when preparing data for upload into the datahub repos.

# directory layout
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
├── subset-data                     # subset study based on sample/patient ID list
├── zscores                         # calculate z-scores
├── LICENSE  
└── README.md  
```
