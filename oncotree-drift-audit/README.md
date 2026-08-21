# Oncotree drift audit

Tools for finding and fixing clinical sample files whose `ONCOTREE_CODE` /
`CANCER_TYPE` / `CANCER_TYPE_DETAILED` values are out of date with Oncotree
(oncotree.mskcc.org / oncotree.info).

## oncotree_audit.py (read-only)

Scans every `<study>/data_clinical_sample.txt` under a root directory and
reports, per study:

- stale codes (no longer present in the requested Oncotree version)
- `CANCER_TYPE` values that differ from the code's current mainType
- `CANCER_TYPE_DETAILED` values that differ from the code's current name

Writes a markdown report and a JSON file with raw findings.

```bash
python3 oncotree_audit.py --root path/to/datahub/public \
    [--out-md oncotree_audit.md] [--out-json oncotree_audit.json]
```

## oncotree_apply.py (writes; has --check)

Applies the pipelines JAR's transformation
(`ImporterImpl.convertCancerTypesFromOncotree`) to clinical files:

- adds missing `CANCER_TYPE` / `CANCER_TYPE_DETAILED` columns (including the
  metadata header lines) and fills them from Oncotree; unknown or blank codes
  become `NA`
- by default replicates the JAR's **datahub** path: files that already have both
  columns pass through unchanged (`forceCancerTypeFromOncotree = false`)
- `--force` replicates the non-datahub path: existing values are overwritten
  from Oncotree. Careful: stale codes then become `NA` — remap those first
  (see `../oncotree-code-converter`)

```bash
python3 oncotree_apply.py [--force] [--check] [--version oncotree_latest_stable] \
    path/to/data_clinical_sample.txt [more files ...]
```

Files that would crash the Java importer (blank lines, short data rows) are
reported as ERROR and left untouched.

## scan_cna_oncotree.py (read-only)

Combined quick scan of a datahub-style `public/` tree: flags CNA files with
duplicate gene rows (same-file key matching only — see
`../cna-duplicate-gene-merger` for full alias-aware resolution) and Oncotree
drift in clinical sample files. Skips Git LFS pointer files and reports them.

## Examples

See `examples/` — each contains `before/`, `after/`, and `changes.diff` produced by actually running the tool.
