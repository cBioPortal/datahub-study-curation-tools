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

## merge_clinical_supp.py

For metaImport, supp files cannot stay separate at all (only one
SAMPLE_ATTRIBUTES and one PATIENT_ATTRIBUTES file per study is allowed): this
merges each `data_clinical_supp*.txt` into the study's main clinical file and
removes the supp data + meta files. `--level sample|patient` forces the merge
target (default: by the supp file's id column, SAMPLE_ID preferred).

## dedup_maf.py

First-wins dedup of MAF records on the cBioPortal validator's
duplicate-mutation key — needed after concatenating multiple MAF files into
one, which otherwise fails metaImport validation.

## Usage

```bash
python3 add_timeline_meta.py [root_dir] [--dry-run]
python3 add_supp_meta.py [root_dir] [--dry-run]
python3 merge_clinical_supp.py study_dir [--dry-run] [--level auto|sample|patient]
python3 dedup_maf.py path/to/data_mutations.txt
```

`root_dir` defaults to `public/`; every immediate subdirectory is treated as a
study. `--dry-run` reports what would be written without writing.

See also `../generate-meta-files` for generating the standard meta files of a
full study.

## Examples

See `examples/` — each contains `before/`, `after/`, and `changes.diff` produced by actually running the tool.
