### Data files migration script usage

This tool is intended to update data files in accordance to the updates made to cBioPortal's gene tables (see the [news release](https://github.com/cBioPortal/datahub/blob/0d21da85619bcc3e66c4eaf04675d3393e640306/seedDB/gene_update_dec_16_2020.md)) and [seed_DB](https://github.com/cBioPortal/datahub/tree/master/seedDB).

The tool,
- Replaces the outdated Entrez Gene IDs, Hugo Symbols to new Entrez Gene IDs, Hugo Symbols. 

The outdated to new Entrez Gene IDs, Hugo Symbol mappings ([outdated_entrez_ids.txt](https://github.com/cBioPortal/datahub-study-curation-tools/blob/19661e9998bf74836a037a6285153796b07d5318/HGNC_Genomic_Files_Migration/outdated_entrez_ids.txt) and [outdated_hugo_symbols.txt](https://github.com/cBioPortal/datahub-study-curation-tools/blob/19661e9998bf74836a037a6285153796b07d5318/HGNC_Genomic_Files_Migration/outdated_hugo_symbols.txt)) are actively maintained/updated to keep in sync with the latest gene information in HGNC and NCBI, and reducing data loss by retaining some of the symbols that were lost in updates. Please make sure to pull the latest changes before running the scripts, and follow the [news release](https://github.com/cBioPortal/datahub/blob/0d21da85619bcc3e66c4eaf04675d3393e640306/seedDB/gene_update_dec_16_2020.md) to track our latest updates.

- Updates the non-matching hugo symbols based on the entrez ids. 

For example, if the data file contains Hugo Symbol, Entrez Gene ID pair `MST4	6788`, the hugo symbol `MST4` gets updated to `STK3` since MST4 is not a valid gene symbol for entrez id 6788.

### Running the tool

#### Requirements

The Migration tool runs on python 3 and requires `pandas` library. `pandas` can be installed using
```
pip3 install pandas
 ```

#### Command line

The tool can be run with the following command:
```
python3 gene_cleanup_data_file_migration.py [-h] -path SOURCE_PATH [-l | -o | -n]
````


**Options**
```
-path | --source_path: Path to the data file or directory (of files) that needs to be migrated.
-l | --stdout_log: Dry-run the script. Preview the changes that will be made to the files.
-o | --override_file:  Override the old data files.
-n | --create_new_file: Save the migrated data to new file without overriding the old files.
```

**Note:**
The arguments `-l`, `-o` and `-n` are mutually exclusive with `-l` as default.

### Method

The updated gene and gene-alias tables are provided in the script folder. 

**Step1:**

Replaces the outdated entrez ids to new entrez ids in data files. The mapping can be found here [outdated_entrez_ids.txt](https://github.com/cBioPortal/datahub-study-curation-tools/blob/19661e9998bf74836a037a6285153796b07d5318/HGNC_Genomic_Files_Migration/outdated_entrez_ids.txt)

**Step2:**

Updates the hugo symbols in data files based on entrez ids.

1. If entrez id is valid (i.e, it is in either the gene or gene-alias tables)
- If entrez id is only in the gene table, and the hugo symbol in data file does not correspond to the symbol in the gene table for the given entrez id, update the symbol in data file to the symbol from gene table based on the entrez id.
- If entrez id only in the gene-alias table, and the hugo symbol in data file does not correspond to alias symbol for the given entrez id, update the symbol to the alias symbol. If multiple aliases exist for the entrez id, do nothing for now. Have to look into other profiles of the study for mapping these cases.
- If entrez id is in both the gene and gene-alias tables, and the hugo symbol in data file does not correspond to main/alias symbols for the given entrez id, then update the hugo symbol in data file to the symbol from gene table.

2. If entrez id in data file is invalid (i.e, it is not observed in the gene or gene-alias tables)
- If the hugo symbol in the data file is outdated, update it to new hugo symbol.
- If the hugo symbol in data file is `NA`, update the hugo symbol in file to empty cell. `NA` in our vocabulary means Unknown, but in the gene tables it maps to entrez id `7504`. So during the import, there is a chance of incorrectly mapping these records to `7504` due to importer falling back on hugo symbols when entrez id in not known.

**Step3:**

Replaces the outdated hugo symbols to new hugo symbols in data files, if the file has only hugo symbol column. The mapping can be found here [outdated_hugo_symbols.txt](https://github.com/cBioPortal/datahub-study-curation-tools/blob/19661e9998bf74836a037a6285153796b07d5318/HGNC_Genomic_Files_Migration/outdated_hugo_symbols.txt).

### Gene panel files migration script usage

This tool is intended to update outdated gene symbols in the panel files.

#### Command line

The tool can be run with the following command:
```
python3 gene_cleanup_panel_file_migration.py [-h] -path SOURCE_PATH [-o | -n]
````

**Options**
```
-path | --source_path: Path to the gene panel file to be updated.
-o | --override_file:  Override the old panel file.
-n | --create_new_file: Save the updated data to new file without overriding the old file.
```

**Note:**
The arguments `-o` and `-n` are mutually exclusive with `-n` as default.
Could omit missing microRNA genes (it's always shown as missing but we actually have them in the DB *TODO*
