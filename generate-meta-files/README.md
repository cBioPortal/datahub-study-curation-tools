#Usage
Generate meta files for existing study.

### Command Line
```
generate_meta_files.py [-h] -m META_DATATYPE_FILE -d STUDY_DIR -s STUDY_ID
```
**Options**
```
-m | --META_DATATYPE_FILE : Path to datatypes.txt file.
-d | --STUDY_DIR : Path to a directory where the script writes the meta files to.
-s | --STUDY_ID : Name of the cancer_study_identifier.

```
### Example
```
python3 path/to/generate_meta_files.py -m path/to/datatypes.txt -d private/brca_tcga -s brca_tcga
```