#Usage
Generate meta files for existing study.

#### Running the tool

The script takes in either a list of sample IDs to subset on or a list of sample IDs to exclude from the source directories. The script can be run as,

### Command Line
```
generate_meta_files.py [-h] -d STUDY_DIR -s STUDY_ID -m META_DATATYPE_FILE
```
**Options**
```
-d | --STUDY_DIR : Path to a directory where the script writes the meta files to.
-s | --STUDY_ID : Name of the cancer_study_identifier.
-m | --META_DATATYPE_FILE : Path to datatypes.txt file.

### Example
```
python3 path/to/generate_meta_files.py -m path/to/datatypes.txt -d private/brca_tcga -s brca_tcga
```