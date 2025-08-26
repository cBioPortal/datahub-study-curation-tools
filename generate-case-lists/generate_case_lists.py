#! /usr/bin/env python3

import os
import sys
import argparse

# Constants for headers and delimiters
CASE_LIST_CONFIG_HEADER_COLUMNS = [
    "CASE_LIST_FILENAME", "STAGING_FILENAME", "META_STABLE_ID",
    "META_CASE_LIST_CATEGORY", "META_CANCER_STUDY_ID",
    "META_CASE_LIST_NAME", "META_CASE_LIST_DESCRIPTION"
]
CASE_LIST_UNION_DELIMITER = "|"
CASE_LIST_INTERSECTION_DELIMITER = "&"
MUTATION_STAGING_GENERAL_PREFIX = "data_mutations"
SEQUENCED_SAMPLES_FILENAME = "sequenced_samples.txt"
MUTATION_CASE_LIST_META_HEADER = "sequenced_samples"
MUTATION_CASE_ID_COLUMN_HEADER = "Tumor_Sample_Barcode"
SAMPLE_ID_COLUMN_HEADER = "SAMPLE_ID"
NON_CASE_IDS = frozenset([
    "MIRNA", "LOCUS", "ID", "GENE SYMBOL", "ENTREZ_GENE_ID",
    "HUGO_SYMBOL", "LOCUS ID", "CYTOBAND",
    "COMPOSITE.ELEMENT.REF", "HYBRIDIZATION REF"
])
CANCER_STUDY_TAG = "<CANCER_STUDY>"
NUM_CASES_TAG = "<NUM_CASES>"

def generate_case_lists(case_list_config_filename, case_list_dir, study_dir, study_id, overwrite=False, verbose=False):
    # Read case list config and process each row
    with open(case_list_config_filename, 'r') as case_list_config_file:
        header = case_list_config_file.readline().strip().split('\t')
        for column in CASE_LIST_CONFIG_HEADER_COLUMNS:
            if column not in header:
                print(f"ERROR: column '{column}' is not in '{case_list_config_filename}'", file=sys.stderr)
                sys.exit(2)

        for line in case_list_config_file:
            config_fields = line.strip().split('\t')
            case_list_filename = config_fields[header.index("CASE_LIST_FILENAME")]
            staging_filename_list = config_fields[header.index("STAGING_FILENAME")]
            case_list_file_full_path = os.path.join(case_list_dir, case_list_filename)

            if os.path.isfile(case_list_file_full_path) and not overwrite:
                if verbose:
                    print(f"LOG: generate_case_lists(), '{case_list_filename}' exists and overwrite is false, skipping caselist...")
                continue

            delimiter = CASE_LIST_UNION_DELIMITER if CASE_LIST_UNION_DELIMITER in staging_filename_list else CASE_LIST_INTERSECTION_DELIMITER
            staging_filenames = staging_filename_list.split(delimiter)
            intersection_case_list = delimiter == CASE_LIST_INTERSECTION_DELIMITER

            if intersection_case_list and not all(os.path.isfile(os.path.join(study_dir, fname)) for fname in staging_filenames):
                continue

            case_set = set()
            num_staging_files_processed = 0

            for staging_filename in staging_filenames:
                if verbose:
                    print(f"LOG: generate_case_lists(), processing staging file '{staging_filename}'")
                case_list = get_case_list_from_staging_file(study_dir, staging_filename, verbose)

                if not case_list:
                    if verbose:
                        print(f"LOG: generate_case_lists(), no cases in '{staging_filename}', skipping...")
                    continue

                if intersection_case_list:
                    case_set = case_set.intersection(case_list) if case_set else set(case_list)
                else:
                    case_set.update(case_list)

                num_staging_files_processed += 1

            if case_set:
                if verbose:
                    print("LOG: generate_case_lists(), calling write_case_list_file()...")
                if not (intersection_case_list and num_staging_files_processed != len(staging_filenames)):
                    write_case_list_file(header, config_fields, study_id, case_list_file_full_path, case_set, verbose)
            elif verbose:
                print("LOG: generate_case_lists(), case_set.size() == 0, skipping call to write_case_list_file()...")

def get_case_list_from_staging_file(study_dir, staging_filename, verbose):
    if verbose:
        print(f"LOG: get_case_list_from_staging_file(), '{staging_filename}'")

    case_set = set()
    if MUTATION_STAGING_GENERAL_PREFIX in staging_filename:
        path = os.path.join(study_dir, SEQUENCED_SAMPLES_FILENAME)
        if os.path.isfile(path):
            if verbose:
                print(f"LOG: get_case_list_from_staging_file(), '{SEQUENCED_SAMPLES_FILENAME}' exists, using sequenced_samples file")
            return get_case_list_from_sequenced_samples_file(path, verbose)

    full_path = os.path.join(study_dir, staging_filename)
    if not os.path.isfile(full_path):
        return []

    with open(full_path, 'r') as f:
        process_header = True
        for line in f:
            line = line.strip()
            if line.startswith('#'):
                if line.startswith(f'#{MUTATION_CASE_LIST_META_HEADER}:'):
                    return line.split(':', 1)[1].strip().split()
                continue
            values = line.split('\t')
            if process_header:
                upper_values = [v.upper() for v in values]
                if MUTATION_CASE_ID_COLUMN_HEADER not in values and SAMPLE_ID_COLUMN_HEADER not in upper_values:
                    if verbose:
                        print("LOG: no known ID column, assuming this is sample IDs in header")
                    case_set.update(v for v in values if v.upper() not in NON_CASE_IDS)
                    break
                id_index = values.index(MUTATION_CASE_ID_COLUMN_HEADER) if MUTATION_CASE_ID_COLUMN_HEADER in values else upper_values.index(SAMPLE_ID_COLUMN_HEADER)
                if verbose:
                    print(f"LOG: found sample ID column at index {id_index}")
                process_header = False
                continue
            case_set.add(values[id_index])
    return list(case_set)

def get_case_list_from_sequenced_samples_file(path, verbose):
    if verbose:
        print(f"LOG: reading sequenced samples from '{path}'")
    with open(path, 'r') as f:
        return [line.strip() for line in f]

def write_case_list_file(header, fields, study_id, path, case_set, verbose):
    if verbose:
        print(f"LOG: writing case list to '{path}'")
    with open(path, 'w') as f:
        f.write(f"cancer_study_identifier: {study_id}\n")
        stable_id = fields[header.index("META_STABLE_ID")].replace(CANCER_STUDY_TAG, study_id)
        f.write(f"stable_id: {stable_id}\n")
        f.write(f"case_list_name: {fields[header.index('META_CASE_LIST_NAME')]}\n")
        description = fields[header.index("META_CASE_LIST_DESCRIPTION")].replace(NUM_CASES_TAG, str(len(case_set)))
        f.write(f"case_list_description: {description}\n")
        f.write(f"case_list_category: {fields[header.index('META_CASE_LIST_CATEGORY')]}\n")
        joined_ids = '\t'.join(case_set)
        f.write(f"case_list_ids: {joined_ids}\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--case-list-config-file', required=True)
    parser.add_argument('-d', '--case-list-dir', required=True)
    parser.add_argument('-s', '--study-dir', required=True)
    parser.add_argument('-i', '--study-id', required=True)
    parser.add_argument('-o', '--overwrite', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    if args.verbose:
        print(f"LOG: case_list_config_file='{args.case_list_config_file}'")
        print(f"LOG: case_list_dir='{args.case_list_dir}'")
        print(f"LOG: study_dir='{args.study_dir}'")
        print(f"LOG: study_id='{args.study_id}'")
        print(f"LOG: overwrite='{args.overwrite}'")
        print(f"LOG: verbose='{args.verbose}'")

    if not os.path.isfile(args.case_list_config_file):
        print(f"ERROR: case list configuration file '{args.case_list_config_file}' does not exist", file=sys.stderr)
        sys.exit(2)

    if not os.path.isdir(args.case_list_dir):
        print(f"ERROR: case list file directory '{args.case_list_dir}' does not exist", file=sys.stderr)
        sys.exit(2)

    if not os.path.isdir(args.study_dir):
        print(f"ERROR: study directory '{args.study_dir}' does not exist", file=sys.stderr)
        sys.exit(2)

    generate_case_lists(
        args.case_list_config_file,
        args.case_list_dir,
        args.study_dir,
        args.study_id,
        args.overwrite,
        args.verbose
    )

if __name__ == '__main__':
    main()