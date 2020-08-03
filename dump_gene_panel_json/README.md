### Usage
Script to dump the gene panel json with gene information from the cBioPortal api. The output json file is to be added to datahub(https://github.com/cBioPortal/datahub/tree/master/.circleci/portalinfo) for validation of gene panels.

### Command Line
```
  -h, --help            show this help message and exit
  -o OUTPUT_FILENAME, --output_filename OUTPUT_FILENAME
                        Gene panel json output file path.
```

### Example
```
python dump_gene_panel_json.py -o path/to/output_file
```
