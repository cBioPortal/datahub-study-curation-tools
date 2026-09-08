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
## add_missing_clinical_meta.py

Gap-fill companion to the generator above, for the two data file families it
cannot produce correct metaImport meta files for: `data_timeline*.txt` and
`data_clinical_supp*.txt`. `datatypes.txt` maps every such file to a single
`meta_timeline.txt` / `meta_clinical.txt` with `datatype: CLINICAL`; metaImport
needs one meta file per data file with `datatype: TIMELINE`, or
`SAMPLE_ATTRIBUTES` / `PATIENT_ATTRIBUTES` decided by whether the supp file's
header carries `SAMPLE_ID`.

Only writes meta files that are missing — a data file is covered if any
existing `meta_*.txt` names it in `data_filename`, whatever that meta file is
called. Never touches existing meta files or
`meta_study.txt` (unlike `generate_meta_files.py`, which rewrites
`meta_study.txt` on every run).

```bash
python3 add_missing_clinical_meta.py [root_dir] [--dry-run]
```

`root_dir` defaults to `public/`; every immediate subdirectory is treated as a
study. See `examples/add_missing_clinical_meta/` for `before/`, `after/`, and
`changes.diff` produced by running it.

See also `../merge-clinical-supp` for folding supp files into the main clinical
file when metaImport rejects them as extra attribute files.
