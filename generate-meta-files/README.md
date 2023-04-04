#Usage
This tool is designed to create metadata files using the metadata types file.
The metadata types file contains values such as DATATYPE, STABLE_ID, DATA_FILENAME, META_GENETIC_ALTERATION_TYPE, META_PROFILE_NAME etc and the script looks for the datatype values present in the datatypes sheet and generates meta files accordingly.

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
python3 path/to/generate_meta_files.py -m path/to/datatypes.txt -d public/brca_tcga -s brca_tcga
```