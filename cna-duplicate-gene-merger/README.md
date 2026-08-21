# CNA duplicate gene merger

Fuses duplicate-gene rows in discrete CNA staging files (`data_cna*.txt`,
`data_log2_cna*.txt`), replicating the behavior of the pipelines JAR importer
end-to-end:

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

Known deviations from the Java implementation are documented in the script
docstring (output row ordering, alias tie-breaking, and the downstream
importer's ambiguous-symbol/miRNA special cases).

## Examples

See `examples/` — each contains `before/`, `after/`, and `changes.diff` produced by actually running the tool.
