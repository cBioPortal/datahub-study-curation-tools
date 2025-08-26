import argparse
import glob
import pandas as pd
import sys

metadata = ['type_of_cancer: gbm\n'
'name: The name of the cancer study,e.g., "Breast Cancer (Jones Lab 2013)"\n'
'description:  Description of the study.\n'
'pmid: eg.,33577785\n'
'citation: A relevant citation, e.g., "TCGA, Nature 2012".\n']


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        prog='metafile generator',
        description='Generate metafiles for datafiles'
    )

    parser.add_argument('-d', '--directory', required=True, help="The folder that has all the study data files")
    parser.add_argument('-s', '--study_id', required=True, help="Name of the cancer_study_identifier")
    parser.add_argument('-m', '--meta_datatype_file', required=True, help="datatypes.txt file path")

    # Parse arguments
    args = parser.parse_args()

    # Match all supported file types in the directory
    types = (f'{args.directory}/data_*.txt', f'{args.directory}/data_*.seg')
    files_grabbed = []
    for pattern in types:
        files_grabbed.extend(glob.glob(pattern))

    # Read the datatype metadata file
    datatype_df = pd.read_csv(args.meta_datatype_file, sep="\t")

    # Required columns for meta files
    cols = [
        "DATA_FILENAME", "META_GENERIC_ASSAY_TYPE", "META_GENERIC_ENTITY_meta_PROPERTIES",
        "META_STABLE_ID", "META_GENETIC_ALTERATION_TYPE", "META_DATATYPE",
        "META_SHOW_PROFILE_IN_ANALYSIS_TAB", "META_PROFILE_NAME",
        "META_PROFILE_DESCRIPTION", "META_REFERENCE_GENOME_ID"
    ]

    # Extract unique data file identifiers
    filenames = [
        os.path.basename(f).replace("data_", "").split(".")[0]
        for f in files_grabbed
    ]

    # Generate meta_*.txt files main logic
    for datatype in datatype_df["datatype"].unique():
        row_data = datatype_df[datatype_df["datatype"] == datatype]
        meta_content = "" # appending to empty string
        for col in cols:
            value = row_data[col].values[-1]  # Take the last row if duplicates
            if pd.notna(value): # check if NAN values are present
                key = col.replace("META_", "").lower() # then replacing Meta_ to ''
                meta_content += f"{key}: {value}\n" # appending to empty string

        # Determine output file name
        filename = row_data["DATA_FILENAME"].values[-1]
        clean_name = filename.replace("data_", "").split(".")[0]

        # Write meta file only if data file is present in directory
        if clean_name in filenames:
            meta_path = os.path.join(args.directory, f"meta_{clean_name}.txt")
            with open(meta_path, "w") as meta_file:
                meta_file.write(f"cancer_study_identifier: {args.study_id}\n")
                meta_file.write(meta_content)

            meta_study_path = f"{args.directory}/meta_study.txt"
            with open(meta_study_path, "w") as meta_study:
                meta_study.writelines(f"cancer_study_identifier: {args.study_id}\n")
                for val in metadata:
                    meta_study.write(val)

