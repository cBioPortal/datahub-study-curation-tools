# CNA duplicate gene merger

Fuses duplicate-gene rows in discrete CNA staging files (`data_cna*.txt`,
`data_log2_cna*.txt`), replicating the behavior of the pipelines JAR importer
(see "Known deviations" below for the exceptions):

- Rows are grouped by resolved Entrez gene id (explicit `Entrez_Gene_Id` column
  first, then `Hugo_Symbol`/alias lookup against the portal gene table, with the
  JAR's hardcoded disambiguations MLL2→8085, MLL4→9757, CDC2→983).
- When a group merges cleanly, values are fused per sample with the JAR's
  preference ladder: blank < NA-style strings < `0` (no event) < real event code.
  The merged row keeps the gene-table-preferred Hugo symbol and the resolved
  Entrez id (`CopyNumberAlterationUtilImpl.unifyDuplicatedGeneIdsByName`).
- When any group has two differing real event codes for the same sample — or the
  file has an unparseable Entrez cell, a ragged row, or a blank line — the JAR
  abandons the merge for the whole file and imports the original, which the
  downstream importer (`ImportTabDelimData`) dedupes first-row-wins, dropping
  lines with invalid (non-digit) Entrez values entirely. This script reproduces
  that fallback in-file.

Files that produce identical results under both importers are reported CLEAN
and left untouched. The transformation is idempotent.

## Usage

```bash
python3 cna_merge.py [--check] [--portal-url URL] path/to/data_cna.txt [more files ...]
```

`--check` is a dry run: reports MERGED / FALLBACK / CLEAN per file, writes nothing.

### Public validator-aligned resolution

For the containerized public rollout, use `--gene-resolution validator` with
the same frozen gene/alias tables used by validation. This mode normalizes
symbol/alias case, trims identifiers and strips `|` suffixes, prefers canonical
symbols, and leaves ambiguous aliases unresolved instead of choosing an arbitrary
lowest Entrez ID. Explicit known Entrez IDs take precedence. Unknown IDs/symbols
are kept in the file for warning-only validation; they are not silently removed
by preprocessing. Malformed Entrez values still enter the reported invalid-row
path; the public preprocessing wrapper refuses outputs that would drop them.

For example, a row named `PIH1` with no Entrez ID now resolves through reference
alias `Pih1` to 55011 and is grouped with an existing `PIH1D1 / 55011` row. The
same resolver is used for both successful merging and conflict fallback, so the
collision cannot reappear just because a different group triggered fallback.

This changes identification, not the merge-value/fallback policy. Conflicting
events still cause whole-file first-row-wins fallback, and the report records
that decision. The original input must be preserved by the caller. The default
`--gene-resolution jar` retains the historical behavior described elsewhere in
this document; validator mode is not a claim of complete Java-importer parity.

Run regression tests with `python3 -m unittest -v test_cna_merge` in this directory.
Set `CBIOPORTAL_SCRIPTS_DIR` to the candidate core `scripts/` directory to also
run differential resolution checks against the actual Python validator.

## Gene table inputs

By default the script fetches gene data live: canonical genes from the public
cBioPortal API (`/api/genes`, the same table the portal database serves) and
symbol synonyms from NCBI `Homo_sapiens.gene_info`. The NCBI synonym set is a
close approximation of the portal's `gene_alias` table (which is seeded from
NCBI) but not the identical snapshot.

For exact parity with a specific portal database, pass dumps of its tables:

```bash
python3 cna_merge.py --gene-table gene_table.tsv --gene-alias gene_alias_table.tsv ...
```

```sql
-- gene_table.tsv: entrez_gene_id<TAB>hugo_gene_symbol
SELECT entrez_gene_id, hugo_gene_symbol FROM gene;
-- gene_alias_table.tsv: entrez_gene_id<TAB>gene_alias
SELECT entrez_gene_id, gene_alias FROM gene_alias;
```

## Known deviations from the Java implementation

- **Output row order.** Merged and resolved groups keep first-occurrence input
  order; Java iterates a `HashMap` keySet, i.e. arbitrary order. Unresolvable
  rows are appended at the end, as in Java.
- **Alias tie-breaking.** `gene_alias` rows are sorted by `entrez_gene_id`
  ascending before first-wins insertion, implementing the DAO comment "select
  the first entrez id returned (lowest integer)". The Java SQL has no
  `ORDER BY`.
- **Fallback dedup details.** Replicates `ImportTabDelimData` line handling:
  gene columns untrimmed, non-digit Entrez cells drop the whole line (no Hugo
  fallback), Hugo truncated at the first `|`, blank lines skipped.
- **Ambiguous symbols and miRNA aliases (known gap).** The real importer uses
  `DaoGeneOptimized`, which skips lines whose symbol is ambiguous (maps to
  multiple genes) or is `///` / `---`, and duplicates rows for miRNA aliases.
  This script resolves through a flat symbol->entrez map instead, so such rows
  may claim a gene or survive where Java drops them.
- **Unresolvable rows are kept** in both modes. The downstream importer
  reports-then-drops them at import time; this script leaves the data in the
  file.

## Examples

See `examples/` — each contains `before/`, `after/`, and `changes.diff` produced by actually running the tool.
