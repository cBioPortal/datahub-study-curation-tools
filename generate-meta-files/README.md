#Usage
Generate meta files for existing study.

#### Running the tool

The script takes in either a list of sample IDs to subset on or a list of sample IDs to exclude from the source directories. The script can be run as,

### Command Line
```
generate_meta_files.py [-h] -c CREATE_META_CNA_SEG [yes/no] -d STUDY_DIR -s STUDY_ID
```
**Options**
```
-d | --STUDY_DIR : Path to a directory where the script writes the meta files to.
-s | --STUDY_ID : Name of the cancer_study_identifier.
-c | --CREATE_META_CNA_SEG : Pass "yes" to create meta SEG file. Pass "no" if you don't want to create meta SEG file. Only one of the option can be passed.

### Example
```
python3 path/to/generate_meta_files.py -c yes -d private/brca_tcga -s brca_tcga
```