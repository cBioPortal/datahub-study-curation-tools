#!/usr/bin/env python3

# Copyright (c) 2023 Memorial Sloan Kettering Cancer Center
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import os.path
import sys
import click
import logging

# set logger
logfilename = 'subset.log'
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler = logging.FileHandler(logfilename)
file_handler.setFormatter(formatter)
logger = logging.getLogger('subset')
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

CASE_LIST_CONFIG_HEADER_COLUMNS = ["CASE_LIST_FILENAME", "STAGING_FILENAME", "META_STABLE_ID", "META_CASE_LIST_CATEGORY", "META_CANCER_STUDY_ID", "META_CASE_LIST_NAME", "META_CASE_LIST_DESCRIPTION"]
CASE_LIST_UNION_DELIMITER = "|"
CASE_LIST_INTERSECTION_DELIMITER = "&"
MUTATION_STAGING_GENERAL_PREFIX = "data_mutations"
SEQUENCED_SAMPLES_FILENAME = "sequenced_samples.txt"
MUTATION_CASE_LIST_META_HEADER = "sequenced_samples"
MUTATION_CASE_ID_COLUMN_HEADER = "Tumor_Sample_Barcode"
SAMPLE_ID_COLUMN_HEADER = "SAMPLE_ID"
NON_CASE_IDS = frozenset(["MIRNA", "LOCUS", "ID", "GENE SYMBOL", "ENTREZ_GENE_ID", "HUGO_SYMBOL", "LOCUS ID", "CYTOBAND", "COMPOSITE.ELEMENT.REF", "HYBRIDIZATION REF"])
CANCER_STUDY_TAG = "<CANCER_STUDY>"
NUM_CASES_TAG = "<NUM_CASES>"

def generate_case_lists(case_list_config_file, case_list_dir, study_dir, study_id, overwrite=False, verbose=False):
    header = []
    with open(case_list_config_file, 'r') as case_list_config_file:
        # get header and validate
        header = case_list_config_file.readline().rstrip('\n').rstrip('\r').split('\t')
        # check full header matches what we expect
        for column in CASE_LIST_CONFIG_HEADER_COLUMNS:
            if column not in header:
                logger.error("column '%s' is not in '%s'" % (column, case_list_config_file))
                sys.exit(2)

        for line in case_list_config_file:
            line = line.rstrip('\n').rstrip('\r')
            config_fields = line.split('\t')
            case_list_filename = config_fields[header.index("CASE_LIST_FILENAME")]
            staging_filename_list = config_fields[header.index("STAGING_FILENAME")]
            case_list_file_full_path = os.path.join(case_list_dir, case_list_filename)
            if os.path.isfile(case_list_file_full_path) and not overwrite:
                if verbose:
                    logger.info("generate_case_lists(), '%s' exists and overwrite is false, skipping caselist..." % (case_list_filename))
                continue

            # might be single staging file
            staging_filenames = []
            # union (like all cases)
            union_case_list = CASE_LIST_UNION_DELIMITER in staging_filename_list
            # intersection (like complete or cna-seq)
            intersection_case_list = CASE_LIST_INTERSECTION_DELIMITER in staging_filename_list
            delimiter = CASE_LIST_UNION_DELIMITER if union_case_list else CASE_LIST_INTERSECTION_DELIMITER
            staging_filenames = staging_filename_list.split(delimiter)
            if verbose:
                logger.info("generate_case_lists(), staging filenames: %s" % (",".join(staging_filenames)))

            # if this is intersection all staging files must exist
            if intersection_case_list and \
                    not all([os.path.isfile(os.path.join(study_dir, intersection_filename)) for intersection_filename in staging_filenames]):
                continue

            # this is the set we will pass to write_case_list_file
            case_set = set([])
            # this indicates the number of staging files processed -
            # used to verify that an intersection should be written
            num_staging_files_processed = 0
            for staging_filename in staging_filenames:
                if verbose:
                    logger.info("generate_case_lists(), processing staging file '%s'" % (staging_filename))
                # compute the case set
                case_list = []
                case_list = get_case_list_from_staging_file(study_dir, staging_filename, verbose)

                if len(case_list) == 0:
                    if verbose:
                        logger.info("LOG: generate_case_lists(), no cases in '%s', skipping..." % (staging_filename))
                    continue

                if intersection_case_list:
                    if len(case_set) == 0:
                        # it is empty so initialize it
                        case_set = set(case_list)
                    else:
                        case_set = case_set.intersection(case_list)
                else:
                    # union of files or single file
                    case_set = case_set.union(case_list)

                num_staging_files_processed += 1

            # write case list file (don't make empty case lists)
            if len(case_set) > 0:
                if verbose:
                    logger.info("generate_case_lists(), calling write_case_list_file()...")

                # do not write out complete cases file unless we've processed all the files required
                if intersection_case_list and num_staging_files_processed != len(staging_filenames):
                    if verbose:
                        logger.info("LOG: generate_case_lists(), number of staging files processed (%d) != number of staging files required (%d) for '%s', skipping call to write_case_list_file()..." % (num_staging_files_processed, len(staging_filenames), case_list_filename))
                else:
                    write_case_list_file(header, config_fields, study_id, case_list_file_full_path, case_set, verbose)
            elif verbose:
                logger.info("generate_case_lists(), case_set.size() == 0, skipping call to write_case_list_file()...")

def get_case_list_from_staging_file(study_dir, staging_filename, verbose):
    if verbose:
        logger.info("get_case_list_from_staging_file(), '%s'" % (staging_filename))

    case_set = set([])

    # if we are processing mutations data and a SEQUENCED_SAMPLES_FILENAME exists, use it
    if MUTATION_STAGING_GENERAL_PREFIX in staging_filename:
        sequenced_samples_full_path = os.path.join(study_dir, SEQUENCED_SAMPLES_FILENAME)
        if os.path.isfile(sequenced_samples_full_path):
            if verbose:
                logger.info("get_case_list_from_staging_file(), '%s' exists, calling get_case_list_from_sequenced_samples_file()" % (SEQUENCED_SAMPLES_FILENAME))
            return get_case_list_from_sequenced_samples_file(sequenced_samples_full_path, verbose)

    staging_file_full_path = os.path.join(study_dir, staging_filename)
    if not os.path.isfile(staging_file_full_path):
        return []

    # staging file
    with open(staging_file_full_path, 'r') as staging_file:
        id_column_index = 0
        process_header = True
        for line in staging_file:
            line = line.rstrip('\n')
            if line.startswith('#'):
                if line.startswith('#' + MUTATION_CASE_LIST_META_HEADER + ':'):
                    # split will split on any whitespace, tabs or any number of consecutive spaces
                    return line[len(MUTATION_CASE_LIST_META_HEADER)+2:].strip().split()
                continue # this is a comment line, skip it
            elif len(line.strip()) == 0:
                continue
            values = line.split('\t')

            # is this the header line?
            if process_header:
                # look for MAF file case id column header
                # if this is not a MAF file and header contains the case ids, return here
                # we are assuming the header contains the case ids because SAMPLE_ID_COLUMN_HEADER is missing
                if MUTATION_CASE_ID_COLUMN_HEADER not in values and SAMPLE_ID_COLUMN_HEADER not in [x.upper() for x in values]:
                    if verbose:
                        logger.info("get_case_list_from_staging_file(), this is not a MAF header but has no '%s' column, we assume it contains sample ids..." % (SAMPLE_ID_COLUMN_HEADER))
                    for potential_case_id in values:
                        # check to filter out column headers other than sample ids
                        if potential_case_id.upper() in NON_CASE_IDS:
                            continue
                        case_set.add(potential_case_id)
                    break # got case ids from header, don't read the rest of the file
                else:
                    # we know at this point one of these columns exists, so no fear of ValueError from index method
                    id_column_index = values.index(MUTATION_CASE_ID_COLUMN_HEADER) if MUTATION_CASE_ID_COLUMN_HEADER in values else [x.upper() for x in values].index(SAMPLE_ID_COLUMN_HEADER)
                    if verbose:
                        logger.info("get_case_list_from_staging_file(), this is a MAF or clinical file, samples ids in column with index: %d" % (id_column_index))
                process_header = False
                continue # done with header, move on to next line
            case_set.add(values[id_column_index])

    return list(case_set)

def get_case_list_from_sequenced_samples_file(sequenced_samples_full_path, verbose):
    if verbose:
        logger.info("get_case_list_from_sequenced_samples_file, '%s'", sequenced_samples_full_path)

    case_set = set([])
    with open(sequenced_samples_full_path, 'r') as sequenced_samples_file:
        for line in sequenced_samples_file:
            case_set.add(line.rstrip('\n'))

    if verbose:
        logger.info("get_case_list_from_sequenced_samples_file, case set size: %d" % (len(case_set)))

    return list(case_set)

def write_case_list_file(case_list_config_header, case_list_config_fields, study_id, case_list_full_path, case_set, verbose):
    if verbose:
        logger.info("write_case_list_file(), '%s'" % (case_list_full_path))
    with open(case_list_full_path, 'w') as case_list_file:
        case_list_file.write("cancer_study_identifier: " + study_id + "\n")
        stable_id = case_list_config_fields[case_list_config_header.index("META_STABLE_ID")].replace(CANCER_STUDY_TAG, study_id)
        case_list_file.write("stable_id: " + stable_id + "\n")
        case_list_file.write("case_list_name: " + case_list_config_fields[case_list_config_header.index("META_CASE_LIST_NAME")] + "\n")
        case_list_description = case_list_config_fields[case_list_config_header.index("META_CASE_LIST_DESCRIPTION")].replace(NUM_CASES_TAG, str(len(case_set)))
        case_list_file.write("case_list_description: " + case_list_description + "\n")
        case_list_file.write("case_list_category: " + case_list_config_fields[case_list_config_header.index("META_CASE_LIST_CATEGORY")] + "\n")
        case_list_file.write("case_list_ids: " + '\t'.join(case_set) + "\n")

@click.command()
@click.option('-c', '--case-list-config-file', required = True, help = 'Path to the case list configuration file')
@click.option('-d', '--case-list-dir', required = True, help = 'Path to the directory in which the case list files should be written')
@click.option('-s', '--study-dir', required = True, help = 'The directory that contains the cancer study genomic files')
@click.option('-i', '--study-id', required = True, help = 'The cancer study stable id')
@click.option('-o', '--overwrite', is_flag=True, required = False, help = 'When given, overwrite the case list files')
@click.option('-v', '--verbose', is_flag=True, required = False, help = 'When given, be verbose')

def main(case_list_config_file, case_list_dir, study_dir, study_id, overwrite, verbose):
    if verbose:
        logger.info("case_list_config_file='%s'" % (case_list_config_file))
        logger.info("case_list_dir='%s'" % (case_list_dir))
        logger.info("study_dir='%s'" % (study_dir))
        logger.info("study_id='%s'" % (study_id))
        logger.info("overwrite='%s'" % (overwrite))
        logger.info("verbose='%s'" % (verbose))

    if not os.path.isfile(case_list_config_file):
        logger.error("case list configuration file '%s' does not exist or is not a file" % (case_list_config_file))
        sys.exit(2)

    if not os.path.isdir(case_list_dir):
        logger.info("case list file directory '%s' does not exist or is not a directory" % (case_list_dir))
        logger.info("creating a new case list file directory..")
        os.mkdir(case_list_dir)
        logger.info("'%s' directory created!" % (case_list_dir))

    if not os.path.isdir(study_dir):
        logger.error("study directory '%s' does not exist or is not a directory" % (study_dir))
        sys.exit(2)

    generate_case_lists(case_list_config_file, case_list_dir, study_dir, study_id, overwrite, verbose)

if __name__ == '__main__':
    main()
