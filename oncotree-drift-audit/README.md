# Oncotree drift audit

Read-only tool for finding clinical sample files whose `ONCOTREE_CODE`,
`CANCER_TYPE`, or `CANCER_TYPE_DETAILED` values differ from Oncotree's latest
stable reference. Findings require review; this tool does not rewrite study data.

## Usage

Scans every `<study>/data_clinical_sample.txt` under a root directory and reports:

- codes absent from the latest stable Oncotree
- populated `CANCER_TYPE` values differing from the code's mainType
- populated `CANCER_TYPE_DETAILED` values differing from the code's name

Files without an `ONCOTREE_CODE` column and Git LFS pointers are listed separately.
Missing or blank label columns are not treated as drift by this audit.

```bash
python3 oncotree_audit.py --root path/to/datahub/public \
    --out-md oncotree_audit.md --out-json oncotree_audit.json
```

Writes a Markdown report and JSON findings. The example input at
`examples/data_clinical_sample.txt` contains labels and codes to review; exact
findings depend on the live reference version.
