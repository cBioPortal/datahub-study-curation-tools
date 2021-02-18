### Usage

Given the expression data for a set of samples, this script generates normalized expression values with the reference population of a defined input set.

#### Command Line
```
  -h, --help            show this help message and exit
  -i INPUT_EXP_FILE_NAME, --input-expression-file-name INPUT_EXP_FILE_NAME
                        Name of the expression file to normalized
  -r INPUT_REF_FILE_NAME, --input-reference-file-name INPUT_REF_FILE_NAME
                        Name of the expression file to be used as reference
                        distribution
  -o OUTPUT_FILE_NAME, --output-file-name OUTPUT_FILE_NAME
```

#### Example
```
python NormalizeExpressionLevels_allsampleref.py -i <expression_file> -r <reference_file> -o <output_file>
```
#### Format
	For both input files: expression file and reference file:
	- 1st column must be "Hugo_Symbol"
	- 2nd column must be "Entrez_Gene_Id"
