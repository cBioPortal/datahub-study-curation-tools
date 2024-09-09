# Extract Mutational Signatures

## Introduction

Annotate mutational signature files. The files will be annotated using the
information in [annotation.csv](./annotation.csv). This will save a cBioPortal
formatted generic assay.

Expected input is either:

- a generic assay (should only contain ENTITY_STABLE_ID, NAME, DESCRIPTION or
    URL columns, they will be replaced), the NAME column should contain the
    signature names
- a tsv file, where the first column is signature names and the rest of the
    columns are samples

If the input data contains activity scores, it is also possible to convert them
to contribution scores (required for cBioPortal), using the `--convert` option.
The following formula is used for conversion:

    contribution = activity in cell / total activity in sample

## Running the script

Run the script using python:

```shell
python3 mutational_Signatures.py \
--infile {path} \
--outfile {path} \
```

### Command line arguments

```shell
$ python3 mutational_signatures.py -h
usage: mutational_signatures.py [-h] -i FILEPATH -o FILEPATH [-a FILEPATH] [-c]

Annotate mutational signature files

options:
  -h, --help            show this help message and exit
  -i FILEPATH, --infile FILEPATH
                        Input file (csv)
  -o FILEPATH, --outfile FILEPATH
                        Output file
  -a FILEPATH, --annotate FILEPATH, --annotation-file FILEPATH
                        Annotation file
  -c, --convert
                        Convert activity scores to contribution scores before annotation
```

## Importing functions

The annotation and conversion functions are quite straightforward and can be
imported in an existing python (with pandas) workflow:

```python3
def annotate(
    data: Union[pd.DataFrame, str], annotation_file: str = "./annotation.csv"
) -> pd.DataFrame:
    """Annotate mutational signature data using an annotation file

    :param data: Either a dataframe or a filepath to a tsv file.
        The file should be in the format: rows -> signatures, columns -> samples
        (default generic assay format)
    :param annotation_file: filepath to annotation file (see ./annotation.csv)
    """
```

```python3
def convert(data: pd.DataFrame) -> pd.DataFrame:
    """Convert activity scores to contriution scores

    Activity is calculated by: activity in cell / total activity in sample

    :param data: A dataframe where each column is a sample. No other columns
        should be present. Index can be anything.
    """

```
