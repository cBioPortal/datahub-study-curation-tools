# Missing meta file generator

Writes the meta files that metaImport requires for data files the pipelines JAR
used to pick up by filename pattern alone. Without a meta file, metaImport
silently skips these data files.

## add_timeline_meta.py

For every `data_timeline*.txt` with no matching `meta_timeline*.txt`:

```
cancer_study_identifier: <from meta_study.txt>
genetic_alteration_type: CLINICAL
datatype: TIMELINE
data_filename: <data file name>
```

## add_supp_meta.py

For every `data_clinical_supp*.txt` with no matching `meta_clinical_supp*.txt`:
same template, with `datatype: SAMPLE_ATTRIBUTES` when the data file's column
header contains `SAMPLE_ID`, else `PATIENT_ATTRIBUTES`. Files with malformed
attribute headers still get a meta file but are reported.

## Usage

```bash
python3 add_timeline_meta.py [root_dir] [--dry-run]
python3 add_supp_meta.py [root_dir] [--dry-run]
```

`root_dir` defaults to `public/`; every immediate subdirectory is treated as a
study. `--dry-run` reports what would be written without writing.

See also `../generate-meta-files` for generating the standard meta files of a
full study.
