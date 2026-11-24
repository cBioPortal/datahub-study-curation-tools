# Single-study Datahub preprocessing

`preprocess_datahub_study.py` runs all applicable preprocessing on a separate
copy. Python 3.9+ and the Python standard library are sufficient. It does **not**
run the portal validator, import anything, upload to S3, or change live traffic.
Successful preprocessing does not imply validator acceptance.

## Tool versions

Fetch the exact tools, with SHA-256 verification, into a new directory:

```bash
python3 preprocess-study/fetch_preprocessing_tools.py /work/preprocessing-tools
```

`preprocessing-tools.lock.json` pins cmo-pipelines PR #1394 (with case-list
parity fixes through `cd98aef3` for virtual `_all`, stable-ID/category gap filling, filename conflicts, and empty
intersections), validator case-list rules at cbioportal-core `a964d5b`, and
the PR #1394 tools for first-wins MAF deduplication and OncoTree audit, plus the remaining Datahub curation
PRs #75 (CNA, with validator-aligned resolution at `82a6c6f`), #78 (missing clinical/timeline metadata), and #79 (MAF fusion). These are
specific PR revisions, not a claim that they have merged. To use different
versions, supply another tools directory; every executed script is hashed in
the study manifest. The wrapper calls the existing tools instead of reimplementing
their transformations.

## Reference inputs

Supply a reference directory containing:

- `gene_table.tsv`: headerless `entrez_gene_id<TAB>hugo_gene_symbol` from the
  intended portal's live gene table, deterministically ordered.
- `gene_alias_table.tsv`: headerless `entrez_gene_id<TAB>gene_alias` from the
  same database snapshot, deterministically ordered.
- `case_list_config.tsv`: the exact pinned validator configuration downloaded
  into the tools directory. Copy it into the reference bundle; an older deployed
  EC2 file is not interchangeable. The wrapper rejects mismatched rules before
  copying or processing study data.
- `oncotree.json`: the tumorTypes API JSON for a concrete pinned OncoTree version,
  not an unrecorded moving `latest` endpoint.

Retain the reference capture timestamp, database color, queries, OncoTree version,
and configuration source alongside these files. References are hashed by the
wrapper. It makes no network requests. OncoTree uses PR #1394's read-only audit
functions against the supplied JSON snapshot, avoiding repeated API requests.

## Run

Materialize the study's Git LFS files first. Use a pinned, clean Datahub checkout:

```bash
python3 preprocess-study/preprocess_datahub_study.py /work/datahub/public/STUDY \
  --output-dir /work/prepared-runs/STUDY \
  --tools-dir /work/preprocessing-tools \
  --references-dir /work/preprocessing-references \
  --source-revision DATAHUB_COMMIT
```

The output directory must not already exist or overlap the source directory.
`--source-revision` is a provenance label, not checkout or Git verification;
the batch caller is responsible for pinning Git and verifying downloaded LFS
object hashes. Output contains `study/<study_id>/`, `logs/`, and `manifest.json`.
Keep logs/manifests outside any import study archive. Package the study directory
as one top-level study folder for `staging/<study_id>.tar.gz`.

Execution order:

1. CNA duplicate-gene merging, with a preview report and `--gene-resolution validator`.
   Gene/alias lookup uses the validator's case-insensitive, canonical-first policy;
   ambiguous aliases are not assigned an arbitrary gene. Unknown identifiers are
   retained for warning-only validation. First-wins duplicate-gene
   fallback follows the upstream JAR-parity tool and is recorded. Invalid-Entrez
   row deletion is held for explicit review, not silently accepted.
2. Supplemental clinical files are not merged. `data_clinical_supp*.txt` files are
   left untouched and listed in the manifest (`clinical_supplements_left_for_curation`);
   the validator rejects a clinical data file that no clinical meta file references,
   so curators merge or declare them by hand.
3. Same-profile MAF fusion. Explicitly distinct profiles are preserved.
   Ambiguous undeclared secondary MAFs are held unless individually named with
   `--same-profile-maf data_mutations_EXTRA.txt`. This cannot override an explicit
   distinct profile. Extra secondary columns and nonstandard removable metadata
   filenames are held for review.
4. First-wins MAF deduplication using all eight validator key columns.
5. Missing timeline metadata, gap-fill only. The upstream gap-filler also writes
   meta files for supplemental clinical files; the wrapper removes those it just
   generated (`supplement_meta_not_generated`) so step 2's policy holds. Meta files
   already in the study are kept.
6. Missing case lists, with TCGA normalization. Existing lists are preserved.
7. Read-only OncoTree audit. Drift is reported, not rewritten or treated as a
   preprocessing failure.

Exit 0 and `status: prepared` indicate all applicable preprocessing finished.
Exit 1 and `status: failed` retain the partial output for diagnosis; **do not
publish a failed result**. Missing inputs, unsafe merges, unresolved LFS pointers,
and symlinks are refused. Source and final file sizes/SHA-256 hashes, added/deleted/
modified file names, tool/reference hashes, commands and audit findings are saved.
Retry into a fresh output directory after resolving the cause; no automatic
resampling, unsafe override, or partial-success upload is performed.

## Tests

```bash
python3 -m unittest discover -s preprocess-study -p 'test_preprocess*.py' -v
PREPROCESS_TOOLS_DIR=/work/preprocessing-tools \
PREPROCESS_CASE_CONFIG=/work/preprocessing-references/case_list_config.tsv \
  python3 -m unittest discover -s preprocess-study -p 'test_preprocess*.py' -v
```

The second invocation includes a fixture exercising the pinned tools,
source preservation, audit-only OncoTree behavior, and refusal to overwrite.
