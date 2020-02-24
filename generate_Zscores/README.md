### Usage

Given the expression data for a set of samples, this script generates normalized expression values with the reference population of all samples independent of sample diploid status.

Use the `-l` option if the data needs to be log transformed before calculating z-scores.

### Command Line
```
  -h, --help            show this help message and exit
  -i INPUT_EXPRESSION_FILE, --input-expression-file INPUT_EXPRESSION_FILE
                        The expression filename to normalize
  -o OUTPUT_FILENAME, --output-filename OUTPUT_FILENAME
                        The filename to which normalized data has to be saved
  -l, --log-transform   Pass this argument to log transform the data before
                        calculating zscores
```

### Example
```
python NormalizeExpressionLevels.py -i <expression_file> -o <output_file> [-l]
```