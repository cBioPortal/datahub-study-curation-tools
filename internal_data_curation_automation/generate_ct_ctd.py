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

from clinicalfile_utils import *
import json
import os
import sys
import logging
import click
import urllib.request

# globals
CANCER_TYPE = 'CANCER_TYPE'
CANCER_TYPE_DETAILED = 'CANCER_TYPE_DETAILED'
ONCOTREE_CODE = 'ONCOTREE_CODE'
SAMPLE_ID = 'SAMPLE_ID'

samples_that_have_undefined_oncotree_codes = []

# set logger
logfilename = 'subset.log'
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler = logging.FileHandler(logfilename)
file_handler.setFormatter(formatter)
logger = logging.getLogger('subset')
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

# functions

def extract_oncotree_code_mappings_from_oncotree_json(oncotree_json):
    oncotree_code_to_info = {}
    oncotree_response = json.loads(oncotree_json)
    for node in oncotree_response:
        if not node['code']:
            logger.info('Encountered oncotree node without oncotree code : ' + node + '\n')
            continue
        oncotree_code = node['code']
        main_type = node['mainType']
        cancer_type = 'NA'
        if main_type:
            cancer_type = main_type
        cancer_type_detailed = node['name']
        if not cancer_type_detailed:
            cancer_type_detailed = 'NA'
        oncotree_code_to_info[oncotree_code] = { CANCER_TYPE : cancer_type, CANCER_TYPE_DETAILED : cancer_type_detailed }
    return oncotree_code_to_info

def get_oncotree_code_mappings(oncotree_tumortype_api_endpoint_url):
    oncotree_raw_response = urllib.request.urlopen(oncotree_tumortype_api_endpoint_url).read()
    return extract_oncotree_code_mappings_from_oncotree_json(oncotree_raw_response)

def get_oncotree_code_info(oncotree_code, oncotree_code_mappings):
    if not oncotree_code in oncotree_code_mappings:
        return { CANCER_TYPE : 'NA', CANCER_TYPE_DETAILED: 'NA' }
    return oncotree_code_mappings[oncotree_code]

def format_output_line(fields):
    """ each field can contain unicode that needs to be utf-8 encoded """
    if not fields or len(fields) == 0:
        return ''
    output_line = ''
    for field in fields:
        output_line = output_line + '\t'
    return output_line[:-1]

def existing_data_is_not_available(data):
    if not data:
        return True
    data_upper = data.strip().upper()
    if len(data_upper) == 0:
        return True
    if data_upper in ['NA','N/A','NOT AVAILABLE']:
        return True
    return False

def process_clinical_file(oncotree_mappings, clinical_filename, force_cancer_type_from_oncotree):
    """ Insert cancer type/cancer type detailed in the clinical file """

    # check if ONCOTREE_CODE column is provided
    if 'ONCOTREE_CODE' not in get_header(clinical_filename):
        logger.error('Skipping addition of CANCER_TYPE and CANCER_TYPE_DETAILED to data clinical. No ONCOTREE_CODE column found..')
        return()

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

    clinical_data = ""
    with open(clinical_filename, 'r') as f:
        for line in f:
            line = line.rstrip('\n')
            if line.startswith('#'):
                if file_has_metadata_headers and not metadata_headers_processed:
                    metadata_headers_processed = True
                continue
            if first:
                first = False
                header = line.split('\t')
                if CANCER_TYPE not in header:
                    header.append(CANCER_TYPE)
                if CANCER_TYPE_DETAILED not in header:
                    header.append(CANCER_TYPE_DETAILED)
                continue
            data = line.split('\t')
            oncotree_code = data[header.index(ONCOTREE_CODE)]
            if not oncotree_code or not oncotree_code in oncotree_mappings:
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
            if format_output_line(data) != '':
                clinical_data += format_output_line(data)+'\n'
                continue

    if clinical_data.strip() != "":
        os.remove(clinical_filename)
        with open(clinical_filename, 'w') as file:
            write_metadata_headers(metadata_lines, file)
            file.write('\t'.join(header)+'\n')
            file.write(clinical_data)
    else:
        logger.error("No Cancer_Type and Cancer_Type_Detailed generated for the file.. ")

def report_failures_to_match_oncotree_code():
    if len(samples_that_have_undefined_oncotree_codes) > 0:
        logger.warning('Could not find an oncotree code match for the following samples:\n')
        logger.warning('         (default value of NA was inserted for CANCER_TYPE and CANCER_TYPE_DETAILED for oncotree code match failures)\n')
        for sample_id in samples_that_have_undefined_oncotree_codes:
            logger.warning('        ' + sample_id + '\n')

def construct_oncotree_url(oncotree_base_url, oncotree_version):
    """ test that oncotree_version exists, then construct url for web API query """
    oncotree_api_base_url = oncotree_base_url.rstrip('/') + '/api/'
    oncotree_versions_api_url = oncotree_api_base_url + 'versions'
    oncotree_versions_raw_response = ''
    try:
        oncotree_versions_raw_response = urllib.request.urlopen(oncotree_versions_api_url)
    except:
        pass
    oncotree_version_response = json.load(oncotree_versions_raw_response)
    found_versions = []
    for version in oncotree_version_response:
        if version['api_identifier'] == oncotree_version:
            #version exists
            return oncotree_api_base_url + 'tumorTypes?version=' + oncotree_version
        else:
            found_versions.append(version['api_identifier'] + ' (' + version['description'] + ')')
    logger.error('oncotree version ' + oncotree_version + ' was not found in the list of available versions:')
    for version in found_versions:
        logger.info('\t' + version + '\n')
    sys.exit(1)

def exit_with_error_if_file_is_not_accessible(filename):
    if not os.path.exists(filename):
        logger.error('file cannot be found: ' + filename + '\n')
        sys.exit(2)
    read_write_error = False
    if not os.access(filename, os.R_OK):
        logger.error('ERROR: file permissions do not allow reading: ' + filename + '\n')
        read_write_error = True
    if not os.access(filename, os.W_OK):
        logger.error('ERROR: file permissions do not allow writing: ' + filename + '\n')
        read_write_error = True
    if read_write_error:
        sys.exit(2)

@click.command()
@click.option('-c', '--clinical-file', required = True, help = 'Path to the clinical file')
@click.option('-o', '--oncotree-url', required = False, help = 'The url of the oncotree web application (default is https://oncotree.info/)')
@click.option('-v', '--oncotree-version', required = False, help = 'The oncotree version to use (default is oncotree_latest_stable)')
@click.option('-f', '--force', required = False, help = 'When given, all CANCER_TYPE/CANCER_TYPE_DETAILED values in the input file are overwritten based on oncotree code. When not given, only empty or NA values are overwritten.')

def main(clinical_file, oncotree_url, oncotree_version, force):
    if not oncotree_url:
        oncotree_url = 'https://oncotree.info/'
    if not oncotree_version:
        oncotree_version = 'oncotree_latest_stable'
    exit_with_error_if_file_is_not_accessible(clinical_file)
    oncotree_url = construct_oncotree_url(oncotree_url, oncotree_version)
    oncotree_mappings = get_oncotree_code_mappings(oncotree_url)
    process_clinical_file(oncotree_mappings, clinical_file, force)
    #report_failures_to_match_oncotree_code()

if __name__ == '__main__':
    main()
