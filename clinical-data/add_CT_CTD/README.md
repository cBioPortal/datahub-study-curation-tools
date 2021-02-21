### Usage
Add additional columns `CANCER_TYPE` and `CANCER_TYPE_DETAILS` according to values `ONCOTREE_CODE` column into data clinical files.

### Command Line
```
oncotree_code_converter.py [-h] -c CLINICAL_FILE [-o ONCOTREE_BASE_URL] [-v ONCOTREE_VERSION] [-f]
```

### Example
```
python oncotree_code_converter.py --oncotree-url "http://oncotree.mskcc.org/" --oncotree-version oncotree_candidate_release --clinical-file data_clinical_sample.txt```

### Notes
`clinicalfile_utils.py` is needed under the sample path. 
