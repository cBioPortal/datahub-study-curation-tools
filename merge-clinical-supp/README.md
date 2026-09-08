# Merge clinical supp files

For metaImport, `data_clinical_supp*.txt` files cannot stay separate: only one
`SAMPLE_ATTRIBUTES` and one `PATIENT_ATTRIBUTES` file is allowed per study.
The pipelines JAR imported supp files as extra clinical files; this merges
each one into the study's main clinical file and removes the supp data + meta
files.

- Supp attribute columns are appended to the main file's columns.
- Header comment rows (`#display` / `#description` / `#datatype` / `#priority`)
  are extended from the supp file's rows; a 5-comment-line supp file (mixed
  format with an attribute-types row) is handled by skipping that row.
- Data is joined on `SAMPLE_ID` (or `PATIENT_ID`). Main-file rows without supp
  data get blank values; supp rows whose id is absent from the main file are
  reported and dropped.

## Usage

```bash
python3 merge_clinical_supp.py study_dir [--dry-run] [--level auto|sample|patient]
```

`--level` picks the merge target: `sample` joins on `SAMPLE_ID` into
`data_clinical_sample.txt`, `patient` on `PATIENT_ID` into
`data_clinical_patient.txt`, `auto` (default) by whichever id column the supp
file carries (`SAMPLE_ID` preferred). Forcing a level requires the supp file to
carry that id column.

The inverse operation (splitting a mixed `data_clinical.txt` into sample and
patient files by attribute type) is
`../internal_data_curation_automation/split_data_clinical_attributes.py`.
`../generate-meta-files/add_missing_clinical_meta.py` writes meta files for supp
files that are being kept rather than merged.

## Examples

See `examples/` — `before/`, `after/`, and `changes.diff` produced by running the tool.
