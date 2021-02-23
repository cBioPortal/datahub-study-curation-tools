### Usage

Given the expression data for a set of samples, this script generates normalized expression values with the reference population of all samples with expression values.

#### Method
Each gene is normalized separately. The expression distribution of the gene is estimated by calculating the mean and variance of the expression values for all samples in the reference poplulation.

For RNA-seq data (read counts, rpkm, fpkm etc.,), the reference population is defined by any non-zero, non-negative numeric values. As raw expression counts or normalized units (rpkm, fpkm..) provide a measure of the abundance of transcripts, we exclude any negative counts and the rationale to exclude 0's is that the values could be due to technical biases.

For microarray or RPPA data, the reference population is defined by any numeric values. 

If the gene has samples whose expression values are all zero's or non-numeric (NA, Null or NaN), then its normalized expression is reported as `NA`. Otherwise, for every sample, the gene's normalized expression is reported as
```
(r - mu)/sigma
```
where `r` is the raw expression value, and `mu` and `sigma` are the mean and standard deviation of the samples in the reference poplulation, respectively.

#### Algorithm
```
Input expression file
for each gene:
  log-transform the raw data, if -l is passed
  identify the base population (if -e is passed, n = # of samples where expression value is non-zero, non-negative numeric values. else, n = # of samples where expression value is numeric)
  compute mean and standard deviation for samples in the base poplulation 
  for each sample in the input set:
    Z-Score <- (value - mean)/sd when standard deviation != 0
    Z-Score <- NA when standard deviation = 0
```

### Running the tool
The tool can be run with the following command:
```
python NormalizeExpressionLevels_allsampleref.py -i <expression_file> -o <output_file> [-l] [-e]
```
Use the `-l` option if the data needs to be log transformed before calculating z-scores.

Use the `-e` option to exclude zero's or negative counts from the reference population when calculating the zscores.

#### Options

```
  -i | --input-expression-file: This is the path to the source file to normalize.
  -o | --output-filename: This is the path to the target file to which normalized data will be saved.
  -l | --log-transform:  Pass this argument to log transform the data before calculating zscores.
  -e | --exclude-zero-negative-values: Pass this argument to exclude zero's or negative counts when normalizing the data.
```

#### Log-transforming the data
Using the `-l` option above calculates log base 2 of the expression values.

Here's how we handle the Negative values when log transforming:
```
Replace the negative values to 0 and add a pseudo-count (+1) to all observed counts prior to applying log transform.
example, if raw value is -1, the log transform would be log(0+1)
         if the value is 0, the log transform would be log(0+1)
         if the value is 1, the log transform would be log(1+1)
```

**NOTE:**

For each gene (row) in the data file, the following must be satisfied:
 - the first column provides gene identifiers
