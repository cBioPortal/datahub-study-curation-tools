### Usage

Given expression data for a set of samples, this tool generates normalized expression values (Independant of unaltered status from CNA file)

### Command Line
```
-h, --help            show this help message and exit
-i INPUT_FILE, --input_file INPUT_FILE
                        Expression file for which z-score has to be computed
-o OUTPUT_FILE, --output_file OUTPUT_FILE
                        Output file name
```

### Example
```
python NormalizeExpressionLevels.py -i <expression_file> -o <output_file>
```   
                    