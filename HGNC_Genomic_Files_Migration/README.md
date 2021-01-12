## HGNC Genomic Data Migration Tool

This tool is intended to migrate the changes in entrez ids and hugo symbols based on HGNC in data files. The tool,
1. Replaces the outdated entrez ids to new entrez ids. The outdated to new entrez id mapping file is pre-defined based on our analysis and is  included in the script folder.
2. Updates the non-matching hugo symbols based on the entrez ids. 
For example, if the data file contains hugo symbol entrez id pair `MST4	6788`, the hugo symbol `MST4` gets updated to `STK3` since MST4 is not a valid symbol for entrez id 6788.

### Prerequisites
The Migration tool runs on python 3 and requires `pandas` library. `pandas` be installed using
```
pip3 install pandas
 ```

### Running the tool

The tool can be run with the following command:
```
python hgnc_data_file_migration.py [-h] -path SOURCE_PATH [-l | -o | -n]
````


**Options**
```
-h | --help: show this help message and exit
-path | --source_path: Path to the data file or directory (of files) that needs to be migrated.
-l | --stdout_log: Dry-run the script. Preview the changes that will be made to the files.
-o | --override_file:  Override the old data files.
-n | --create_new_file: Save the migrated data to new file without overriding the old files.
```

**Note**
The arguments -l, -o and -n are mutually exclusive.