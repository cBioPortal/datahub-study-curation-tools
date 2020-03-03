### Usage

Given the expression data for a set of samples, this script generates normalized expression values with the reference population of all samples independent of sample diploid status.

#### Method
Each gene is normalized separately. The reference population for the given gene is all samples with expression values (excludes zeros, non-numeric values like NA, NaN or Null). 
First, the expression distribution of the gene is estimated by calculating the mean and variance of the expression values for all samples whose values are not Zero, Null, NA or NaN.

If the gene has samples whose expression values are all Zeros, Null, NaN or NA, then its normalized expression is reported as `NA`. Otherwise, for every sample, the gene's normalized expression is reported as
```
(r - mu)/sigma
```
where `r` is the raw expression value, and `mu` and `sigma` are the mean and standard deviation of the samples with expression values, respectively.

#### Command Line
```
  -h, --help            show this help message and exit
  -i INPUT_EXPRESSION_FILE, --input-expression-file INPUT_EXPRESSION_FILE
                        The expression filename to normalize
  -o OUTPUT_FILENAME, --output-filename OUTPUT_FILENAME
                        The filename to which normalized data has to be saved
  -l, --log-transform   Pass this argument to log transform the data before
                        calculating zscores
```

#### The syntax is simple
```
python NormalizeExpressionLevels_allsampleref.py -i <expression_file> -o <output_file> [-l]
```
Use the `-l` option if the data needs to be log transformed before calculating z-scores. The output is written onto a file named "output_file"

Any number of columns may precede the data. However, the following must be satisfied:
 - the first column provides gene identifiers

#### Algorithm
```
Input expression file
for each gene:
  log-transform the raw data, if -l is passed
  compute mean and standard deviation for samples ( n = # of samples where expression value is not Zero, Null, NA, NaN)
  for each sample:
    compute Zscore when standard deviation != 0
    output NA for genes with standard deviation = 0
```
#### Log-transforming the data
Using the `-l` option above calculates log base 2 of the expression values.

Here's how we handle the Negative values when log transforming:
```
Replace the negative values to 0 and add a constant value(+1) to data pior to applying log transform.
example, if raw value is -1, the log transform would be log(0+1)
         if the value is 0, the log transform would be log(0+1)
         if the value is 1, the log transform would be log(1+1)
```
