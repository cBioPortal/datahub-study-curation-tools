import argparse
import os.path as osp
import pandas as pd
from typing import Union


def existing_file(f: str) -> str:
    if not osp.exists(f):
        raise argparse.ArgumentError(None, f"file {f} does not exist")
    return f


def parse_args():
    parser = argparse.ArgumentParser(description="Annotate mutational signature files")

    parser.add_argument(
        "-i", "--infile", metavar="FILEPATH", type=existing_file,
        help="Input file (csv)", required=True,
    )
    parser.add_argument(
        "-o", "--outfile", metavar="FILEPATH", help="Output file", required=True,
    )
    parser.add_argument(
        "-a", "--annotate", "--annotation-file", default="annotation.csv",
        metavar="FILEPATH", type=existing_file, help="Annotation file",
        dest="annotation_file"
    )
    parser.add_argument(
        "-c", "--convert", action="store_true", default=False,
        help="Convert activity scores to contribution scores before annotation",
    )

    return parser.parse_args()


def read_data(f: str) -> pd.DataFrame:
    # TODO:
    """"""
    data = pd.read_csv(f, sep="\t", comment="#", index_col=False, header="infer")
    # If this is already in generic assay format, the NAME column should have the signature name
    if "NAME" in data.columns.to_list():
        data = data.set_index("NAME")
    else:
        data = data.set_index(data.columns[0])
    data.index = data.index.str.upper()
    # Drop non-sample columns (standard generic assay columns)
    data = data[
        data.columns.difference(["ENTITY_STABLE_ID", "NAME", "DESCRIPTION", "URL"])
    ]
    return data


def convert(data: pd.DataFrame) -> pd.DataFrame:
    """Convert activity scores to contriution scores

    Activity is calculated by: activity in cell / total activity in sample

    :param data: A dataframe where each column is a sample. No other columns
        should be present. Index can be anything.
    """
    # transpose to make sum calculations easier
    data = data.transpose()
    data = data.astype("float")
    data["sum"] = data.sum(axis="columns")
    for col in data.columns:
        if col == "sum":
            continue
        data[col] = data[col] / data["sum"]
    data = data.drop(columns=["sum"])
    # transpose back
    data = data.transpose()
    return data


def annotate(
    data: Union[pd.DataFrame, str], annotation_file: str = "./annotation.csv"
) -> pd.DataFrame:
    """Annotate mutational signature data using an annotation file

    :param data: Either a dataframe or a filepath to a tsv file.
        The file should be in the format: rows -> signatures, columns -> samples
        (default generic assay format)
    :param annotation_file: filepath to annotation file (see ./annotation.csv)
    """
    if isinstance(data, str):
        data = read_data(data)
    if not isinstance(data, pd.DataFrame):
        raise ValueError("param data should be a pandas DataFrame")
    if not osp.exists(annotation_file):
        raise FileNotFoundError(f"file {annotation_file} does not exist")

    annotation = pd.read_csv(annotation_file, dtype=str)
    annotation = annotation.set_index("SIGNATURE")
    # join, but keep rows in original data
    data = annotation.join(data, how="right")
    data = data.reset_index(names="index")

    data["ENTITY_STABLE_ID"] = data["index"].apply(
        lambda index: f"mutational_signature_{index}"
    )

    # Output signatures that were not in the annotation file
    sigs = list(data.loc[data["NAME"].isnull(), "index"])
    if sigs:
        print(f"The following signatures do not have additional annotation: {sigs}")
        # Copy name from index if no annotation
        data.loc[data.index.isin(sigs), "NAME"] = data.loc[
            data.index.isin(sigs), "index"
        ]
    data = data.drop("index", axis=1)

    # Reorder the columns, to make sure generic assay columns come first
    data = data.set_index("ENTITY_STABLE_ID")
    generic_assay_cols = ["NAME", "DESCRIPTION", "URL"]
    data = data[
        generic_assay_cols + data.columns.difference(generic_assay_cols).tolist()
    ]
    return data


def write_file(data: pd.DataFrame, outfile: str):
    """Write dataframe to file.

    NaN values are represented as 0.0 due to the possibility of division by 0.
    """
    data.to_csv(outfile, sep="\t", na_rep="0.0", index=True, header=True)


def main():
    args = parse_args()
    data = read_data(args.infile)
    if args.convert:
        data = convert(data)
    data = annotate(data, args.annotation_file)
    write_file(data, args.outfile)


if __name__ == "__main__":
    main()
