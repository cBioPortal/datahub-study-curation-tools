### Usage
Generate case lists for existing study.

### Command Line
```
generate_case_lists.py [-h] -c CASE_LIST_CONFIG_FILE -d CASE_LIST_DIR -s STUDY_DIR -i STUDY_ID [-o] [-v]
```

### Example
```
cd path/to/brca_tcga
rm -rf case_lists #remove current case lists folder (if existed)
mkdir case_lists
python path/to/generate_case_lists.py -c path/to/case_list_conf.txt -d case_lists -s . -i brca_tcga
```

### Notes
`case_list_conf.txt` and `clinicalfile_utils.py` are needed under the sample path. 
`case_list_conf.txt` should be synced with the corresponding google config sheet.
TCGA barcodes are normalized to the sample barcode (`TCGA-XX-XXXX-NN`) before case lists are built, as the pipelines importer does (`StableIdUtil.getSampleId`): aliquot barcodes are truncated, `Tumor`/`Normal` suffixes become `01`/`11`, and patient-only barcodes get `-01`. Non-TCGA ids are left untouched.
