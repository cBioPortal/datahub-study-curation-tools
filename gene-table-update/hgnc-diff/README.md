# HGNC Diff Script

This directory contains a Python script to compare two versions of HGNC gene tables. The script identifies changes in Hugo symbols, Entrez IDs, and locus types between two versions of the `hgnc_complete_set` file.

## Overview

The script compares the following data between two HGNC releases:
1. **Hugo Symbols**: The gene symbols assigned by HGNC.
2. **Entrez IDs**: The unique identifiers assigned to genes in the Entrez Gene database.
3. **Locus Types**: The classification of a gene's genomic region (e.g., protein-coding, non-coding RNA, pseudogene).

## Input Files

The script fetches data from the HGNC FTP server:
- The old version of the HGNC gene table (e.g., `2023-10-01`).
- The new version of the HGNC gene table (e.g., `2024-08-23`).

Example URLs:
- Old file: `http://ftp.ebi.ac.uk/pub/databases/genenames/hgnc/archive/monthly/tsv/hgnc_complete_set_2023-10-01.txt`
- New file: `http://ftp.ebi.ac.uk/pub/databases/genenames/hgnc/archive/monthly/tsv/hgnc_complete_set_2024-08-23.txt`

#### Running the tool

The tool can be run with the following command:

```
python hgnc_combo.py --old_file <old_file_url> --new_file <new_file_url> --output_file <output_file_path>

```

#### Command Line
```
python hgnc_combo.py --old_file http://ftp.ebi.ac.uk/pub/databases/genenames/hgnc/archive/monthly/tsv/hgnc_complete_set_2023-10-01.txt --new_file http://ftp.ebi.ac.uk/pub/databases/genenames/hgnc/archive/monthly/tsv/hgnc_complete_set_2024-08-23.txt --output_file gene_changes_diff.txt

```

## Output

The script generates a `gene_changes.txt` file with the following sections:
1. **Genes where both Hugo symbol & Entrez ID have been updated**.
2. **Genes where only Entrez ID got updated**.
3. **Genes where only Hugo symbols got updated**.
4. **Genes that are not present in the new file but exist in the old file**.
5. **Genes that got added in the new file but do not exist in the old file**.