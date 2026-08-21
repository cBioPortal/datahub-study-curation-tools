# JAR-faithful case list generator

Generates missing case lists for a study, mirroring the pipelines importer JAR
exactly (`FileUtilsImpl.generateCaseLists` / `getCaseListFromStagingFile` /
`writeCaseListFile` / `StableIdUtil.getSampleId`, in the JAR's import
configuration: gap-fill only — existing case list files are never touched).

Differences from the existing `generate_case_lists.py` in cmo-pipelines (which
is a near-port but diverges from the JAR in specific cases):

- Sample-id header recognition is only `Tumor_Sample_Barcode` / `SAMPLE_ID`;
  any other header (e.g. `Sample_Id` SV files, CNA matrixes) is treated as a
  matrix file whose header tokens are the case ids (minus a blocklist) — the
  JAR's behavior, surprising or not.
- TCGA barcodes are standardized via the `StableIdUtil.getSampleId` logic
  (`Tumor`→`01`, `Normal`→`11`, truncation to `TCGA-XX-XXXX-NN`, patient-only
  barcodes get `-01`).
- Output is byte-identical to the JAR's (meta line order, trailing tab after
  the last case id).
- Deterministic first-seen sample order (the JAR uses JVM hash order;
  membership is identical).

## Usage

```bash
python3 generate_case_lists_jar.py --config case_list_config.tsv \
    [--dry-run] path/to/study_dir [more study dirs ...]
```

The study id is read from `meta_study.txt` (`cancer_study_identifier`),
falling back to the directory name. `--dry-run` reports what would be
generated without writing.

`case_list_config.tsv` defines the case lists (same 7-column schema the JAR
reads from its configuration worksheet: filename, staging-file pattern with
`|` union / `&` intersection, stable-id/category/name/description templates).
The bundled copy is byte-identical to the production deployment
(`/data/portal-cron/scripts/case_list_config.tsv`) and to the copy in
cmo-pipelines (`import-scripts/test/resources/generate_case_lists/case_list_config.tsv`).

## Examples

See `examples/` — each contains `before/`, `after/`, and `changes.diff` produced by actually running the tool.
