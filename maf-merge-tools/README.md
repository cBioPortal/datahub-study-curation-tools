# MAF merge tools

Tools for reducing a study's multiple MAF files down to the single mutation
file metaImport accepts, the way the pipelines JAR effectively did by importing
all pattern-matched MAFs into one profile.

## fuse_mafs.py

Fuses extra `data_mutations*.txt` files into the study's primary MAF, in a
metaImport-compatible way: columns remapped by header name, first-wins dedup on
the validator's duplicate-mutation key, secondary data + meta files removed.
`--exclude <filename>` leaves a secondary alone (e.g. an uncalled MAF meant to
stay a separate profile).

## dedup_maf.py

First-wins dedup of MAF records on the cBioPortal validator's
duplicate-mutation key — needed after concatenating multiple MAF files into
one, which otherwise fails metaImport validation.

## Usage

```bash
python3 fuse_mafs.py study_dir [--exclude data_mutations_uncalled.txt] [--dry-run]
python3 dedup_maf.py path/to/data_mutations.txt
```

`--dry-run` reports what would be written without writing.

See also `../generate-meta-files/add_missing_clinical_meta.py` for meta files
and `../merge-clinical-supp` for folding supp clinical files.

## Examples

See `examples/` — each contains `before/`, `after/`, and `changes.diff` produced by actually running the tool.
