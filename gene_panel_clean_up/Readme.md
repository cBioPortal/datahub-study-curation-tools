### Usage
Replace gene symbols in gene panels according to the mapping file. 

### Command Line

usage: cleanup_gene_panel.py [-h] -p INPUT_GENE_PANEL_FOLDER -m
                             INPUT_GENE_MAPPING_FILE -o
                             OUTPUT_GENE_PANEL_FOLDER

optional arguments:
  -h, --help            show this help message and exit
  -p INPUT_GENE_PANEL_FOLDER, --input-gene-panel-folder INPUT_GENE_PANEL_FOLDER
                        Gene Panel folder
  -m INPUT_GENE_MAPPING_FILE, --input-gene-mapping-file INPUT_GENE_MAPPING_FILE
                        Gene Mapping
  -o OUTPUT_GENE_PANEL_FOLDER, --output-gene-panel-folder OUTPUT_GENE_PANEL_FOLDER
                        Output Folder for Updated Panels

### Example

```
python cleanup_gene_panel.py -p path/to/gene_panels -m gene_mapping.txt -o path/to/output_folder
```

### Notes
Gene mapping file currenctly includes panel genes that are:
- alias <> main
- outdated <> current
- typo <> correct