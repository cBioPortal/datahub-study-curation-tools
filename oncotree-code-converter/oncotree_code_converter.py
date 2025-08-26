#!/usr/bin/env python3

from clinicalfile_utils import *
import argparse
import fileinput
import json
import os
import re
import sys
import urllib.request

# globals
DEFAULT_ONCOTREE_BASE_URL = 'http://oncotree.mskcc.org/'
DEFAULT_ONCOTREE_VERSION = 'oncotree_latest_stable'
DEFAULT_FORCE_CANCER_TYPE_FROM_ONCOTREE = False
CANCER_TYPE = 'CANCER_TYPE'
CANCER_TYPE_DETAILED = 'CANCER_TYPE_DETAILED'
ONCOTREE_CODE = 'ONCOTREE_CODE'
SAMPLE_ID = 'SAMPLE_ID'

samples_that_have_undefined_oncotree_codes = []

# functions
def extract_oncotree_code_mappings_from_oncotree_json(oncotree_json):
    oncotree_code_to_info = {}
    oncotree_response = json.loads(oncotree_json)
    for node in oncotree_response:
        if not node['code']:
            sys.stderr.write('Encountered oncotree node without oncotree code : ' + str(node) + '\n')
            continue
        oncotree_code = node['code']
        main_type = node['mainType']
        cancer_type = 'NA'
        if main_type:
            cancer_type = str(main_type)
        cancer_type_detailed = node.get('name', 'NA') or 'NA'
        oncotree_code_to_info[oncotree_code] = { CANCER_TYPE : cancer_type, CANCER_TYPE_DETAILED : cancer_type_detailed }
    return oncotree_code_to_info

def get_oncotree_code_mappings(oncotree_tumortype_api_endpoint_url):
    with urllib.request.urlopen(oncotree_tumortype_api_endpoint_url) as response:
        oncotree_raw_response = response.read().decode()
    return extract_oncotree_code_mappings_from_oncotree_json(oncotree_raw_response)

def get_oncotree_code_info(oncotree_code, oncotree_code_mappings):
    if oncotree_code not in oncotree_code_mappings:
        return { CANCER_TYPE : 'NA', CANCER_TYPE_DETAILED: 'NA' }
    return oncotree_code_mappings[oncotree_code]

def format_output_line(fields):
    """ each field can contain unicode that needs to be utf-8 encoded """
    return '\t'.join(str(field) for field in fields)

def existing_data_is_not_available(data):
    if not data:
        return True
    data_upper = data.strip().upper()
    return len(data_upper) == 0 or data_upper in ['NA', 'N/A', 'NOT AVAILABLE']

def process_clinical_file(oncotree_mappings, clinical_filename, force_cancer_type_from_oncotree):
    """ Insert cancer type/cancer type detailed in the clinical file """
    first = True
    metadata_headers_processed = False
    header = []
    file_has_metadata_headers = has_metadata_headers(clinical_filename)

    # same logic checking for Cancer Type/ Cancer Type Detailed but applied to metadata headers
    if file_has_metadata_headers:
        metadata_lines = get_all_metadata_lines(clinical_filename)
        if CANCER_TYPE not in get_header(clinical_filename):
            add_metadata_for_attribute(CANCER_TYPE, metadata_lines)
        if CANCER_TYPE_DETAILED not in get_header(clinical_filename):
            add_metadata_for_attribute(CANCER_TYPE_DETAILED, metadata_lines)

    # Python docs: "if the keyword argument inplace=1 is passed to fileinput.input()
    # or to the FileInput constructor, the file is moved to a backup
    # file and standard output is directed to the input file"
    f = fileinput.input(clinical_filename, inplace = 1)
    try:
        for line in f:
            line = line.rstrip('\n')
            if line.startswith('#'):
                if file_has_metadata_headers and not metadata_headers_processed:
                    metadata_headers_processed = True
                    write_metadata_headers(metadata_lines, clinical_filename)
                continue
            if first:
                first = False
                header = line.split('\t')
                if CANCER_TYPE not in header:
                    header.append(CANCER_TYPE)
                if CANCER_TYPE_DETAILED not in header:
                    header.append(CANCER_TYPE_DETAILED)
                print('\t'.join(header))
                continue
            data = line.split('\t')
            oncotree_code = data[header.index(ONCOTREE_CODE)]
            if not oncotree_code or oncotree_code not in oncotree_mappings:
                samples_that_have_undefined_oncotree_codes.append(data[header.index(SAMPLE_ID)])
            oncotree_code_info = get_oncotree_code_info(oncotree_code, oncotree_mappings)
            # Handle the case if CANCER_TYPE or CANCER_TYPE_DETAILED has to be appended to the header.
            # Separate try-except in case one of the fields exists and the other doesn't
            try:
                existing_data = data[header.index(CANCER_TYPE)]
                if force_cancer_type_from_oncotree or existing_data_is_not_available(existing_data):
                    data[header.index(CANCER_TYPE)] = oncotree_code_info[CANCER_TYPE]
            except IndexError:
                data.append(oncotree_code_info[CANCER_TYPE])
            try:
                existing_data = data[header.index(CANCER_TYPE_DETAILED)]
                if force_cancer_type_from_oncotree or existing_data_is_not_available(existing_data):
                    data[header.index(CANCER_TYPE_DETAILED)] = oncotree_code_info[CANCER_TYPE_DETAILED]
            except IndexError:
                data.append(oncotree_code_info[CANCER_TYPE_DETAILED])
            print(format_output_line(data))
    finally:
        f.close()

def report_failures_to_match_oncotree_code():
    if samples_that_have_undefined_oncotree_codes:
        sys.stderr.write('WARNING: Could not find an oncotree code match for the following samples:\n')
        sys.stderr.write('         (default value of NA was inserted for CANCER_TYPE and CANCER_TYPE_DETAILED for oncotree code match failures)\n')
        for sample_id in samples_that_have_undefined_oncotree_codes:
            sys.stderr.write('        ' + sample_id + '\n')

def construct_oncotree_url(oncotree_base_url, oncotree_version):
    """ test that oncotree_version exists, then construct url for web API query """
    oncotree_api_base_url = oncotree_base_url.rstrip('/') + '/api/'
    oncotree_versions_api_url = oncotree_api_base_url + 'versions'
    print(oncotree_versions_api_url)
    try:
        with urllib.request.urlopen(oncotree_versions_api_url) as response:
            oncotree_version_response = json.load(response)
    except urllib.error.HTTPError as err:
        sys.stderr.write('ERROR: failure during attempt to access oncotree through base url ' + oncotree_base_url + '\n')
        sys.stderr.write('        failure during access of versions web service (' + oncotree_versions_api_url + ')\n')
        sys.stderr.write('        http status code returned: ' + str(err.code) + '\n')
        sys.exit(3)
    found_versions = []
    for version in oncotree_version_response:
        if version['api_identifier'] == oncotree_version:
            return oncotree_api_base_url + 'tumorTypes?version=' + oncotree_version
        else:
            found_versions.append(version['api_identifier'] + ' (' + version['description'] + ')')
    sys.stderr.write('ERROR: oncotree version ' + oncotree_version + ' was not found in the list of available versions:\n')
    for version in found_versions:
        sys.stderr.write('\t' + version + '\n')
    sys.exit(1)

def exit_with_error_if_file_is_not_accessible(filename):
    if not os.path.exists(filename):
        sys.stderr.write('ERROR: file cannot be found: ' + filename + '\n')
        sys.exit(2)
    read_write_error = False
    if not os.access(filename, os.R_OK):
        sys.stderr.write('ERROR: file permissions do not allow reading: ' + filename + '\n')
        read_write_error = True
    if not os.access(filename, os.W_OK):
        sys.stderr.write('ERROR: file permissions do not allow writing: ' + filename + '\n')
        read_write_error = True
    if read_write_error:
        sys.exit(2)

def main():
    """
    Parses a clinical file with a ONCOTREE_CODE column and add/update the CANCER_TYPE and CANCER_TYPE_DETAILED columns inplace
    with values from an oncotree instance.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--clinical-file', required=True, help='Path to the clinical file')
    parser.add_argument('-o', '--oncotree-url', required=False, help='The URL of the oncotree web application')
    parser.add_argument('-v', '--oncotree-version', required=False, help='The oncotree version to use')
    parser.add_argument('-f', '--force', action='store_true', help='Force overwrite all cancer type values')
    parser.set_defaults(
        oncotree_base_url=DEFAULT_ONCOTREE_BASE_URL,
        oncotree_version=DEFAULT_ONCOTREE_VERSION,
        force_cancer_type_from_oncotree=DEFAULT_FORCE_CANCER_TYPE_FROM_ONCOTREE
    )
    args = parser.parse_args()

    clinical_filename = args.clinical_file
    exit_with_error_if_file_is_not_accessible(clinical_filename)

    oncotree_url = construct_oncotree_url(args.oncotree_base_url, args.oncotree_version)
    oncotree_mappings = get_oncotree_code_mappings(oncotree_url)

    process_clinical_file(oncotree_mappings, clinical_filename, args.force)
    report_failures_to_match_oncotree_code()
    sys.exit(0)

if __name__ == '__main__':
    main()
