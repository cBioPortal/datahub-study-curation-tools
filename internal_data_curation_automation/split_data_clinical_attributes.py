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
import sys
import csv

# some file descriptors
ERROR_FILE = sys.stderr
OUTPUT_FILE = sys.stdout

CLINICAL_ATTRIBUTE_METADATA_FILENAME = 'config_files/clinical_attributes_metadata.txt'
CLINICAL_ATTRIBUTE_METADATA = {}
PATIENT_CLINICAL_ATTRIBUTES = {}

CLINICAL_PATIENT_FILENAME = 'data_clinical_patient.txt'
CLINICAL_SAMPLE_FILENAME = 'data_clinical_sample.txt'

def get_header(filename):
	""" Returns the file header. """
	filedata = [x for x in open(filename).read().split('\n') if not x.startswith('#')]
	header = list(map(str.strip, filedata[0].split('\t')))
	return header


def load_clinical_attribute_metadata():
	# read file and load clinical attribute metadata
	metadata_file = open(CLINICAL_ATTRIBUTE_METADATA_FILENAME, 'r')
	metadata_reader = csv.DictReader(metadata_file, dialect='excel-tab')
	for line in metadata_reader:
		column = line['NORMALIZED_COLUMN_HEADER']
		attribute_type = line['ATTRIBUTE_TYPE']
		display_name = line['DISPLAY_NAME']
		description = line['DESCRIPTIONS']
		priority = line['PRIORITY']
		datatype = line['DATATYPE']

		if attribute_type == 'PATIENT':
			PATIENT_CLINICAL_ATTRIBUTES[column] = True
		else:
			PATIENT_CLINICAL_ATTRIBUTES[column] = False

		CLINICAL_ATTRIBUTE_METADATA[column] = {'DISPLAY_NAME':display_name, 'DESCRIPTION':description, 'PRIORITY':priority, 'DATATYPE':datatype}

def get_clinical_header(clinical_filename, is_patient_file):
	""" Returns the new file header by clinical file type. """
	new_header = ['PATIENT_ID']
	# sample clinical header needs SAMPLE_ID
	if not is_patient_file:
		new_header.append('SAMPLE_ID')

	# get the file header and filter by attribute type
	clinical_file_header = get_header(clinical_filename)
	attribute_type_header = [hdr for hdr in clinical_file_header if PATIENT_CLINICAL_ATTRIBUTES[hdr] == is_patient_file]
	filtered_header = [hdr for hdr in attribute_type_header if not hdr in new_header]
	new_header.extend(filtered_header)

	return new_header


def get_clinical_header_metadata(header):
	""" 
		Returns the clinical header metadata. 
		The order of the clinical header metadata goes:
			1. display name 
			2. descriptions
			3. datatype (STRING, NUMBER, BOOLEAN)
			4. priority
	"""

	display_names = []
	descriptions = []
	datatypes = []
	priorities = []

	for column in header:
		if not column in CLINICAL_ATTRIBUTE_METADATA.keys():
			disp_name = column.replace('_', ' ').title()
			CLINICAL_ATTRIBUTE_METADATA[column] = {'DISPLAY_NAME': disp_name, 'DESCRIPTION': disp_name, 'DATATYPE': 'STRING', 'PRIORITY': '1'}

		display_names.append(CLINICAL_ATTRIBUTE_METADATA[column]['DISPLAY_NAME'])
		descriptions.append(CLINICAL_ATTRIBUTE_METADATA[column]['DESCRIPTION'])
		datatypes.append(CLINICAL_ATTRIBUTE_METADATA[column]['DATATYPE'])
		priorities.append(CLINICAL_ATTRIBUTE_METADATA[column]['PRIORITY'])

	display_names = '#' + '\t'.join(display_names)
	descriptions = '#' + '\t'.join(descriptions)
	datatypes = '#' + '\t'.join(datatypes)
	priorities = '#' + '\t'.join(priorities)

	metadata = [display_names, descriptions, datatypes, priorities]
	return metadata	


def write_clinical_datafile(clinical_header, is_patient_file, clinical_filename, logger):
	""" Writes the clinical datafile with the metadata filtered by attribute type. """

	# get the clinical metadata
	clinical_metadata = get_clinical_header_metadata(clinical_header)

	# read the clinical data file and filter data by given header
	clinical_file = open(clinical_filename, 'r')
	clinical_reader = csv.DictReader(clinical_file, dialect='excel-tab')
	filtered_clinical_data = ['\t'.join(clinical_header)]
	for line in clinical_reader:
		line_data = map(lambda x: line.get(x, 'NA'), clinical_header)
		filtered_clinical_data.append('\t'.join(line_data))

	# resolve the output filename 
	output_directory = os.path.dirname(os.path.abspath(clinical_filename))
	if is_patient_file:
		output_filename = os.path.join(output_directory, CLINICAL_PATIENT_FILENAME)
	else: 
		output_filename = os.path.join(output_directory, CLINICAL_SAMPLE_FILENAME)
	clinical_file.close()

	# combine metadata and filtered clinical data for output
	output_data = clinical_metadata[:]
	output_data.extend(filtered_clinical_data)

	# create output file and write output data
	output_file = open(output_filename, 'w')
	output_file.write('\n'.join(output_data))
	output_file.close()

	if is_patient_file:
		logger.info('Patient clinical data written to:' + output_filename)
	else :
		logger.info('Sample clinical data written to:' + output_filename)

def split_data_clinical_attributes_main(clinical_filename, logger):
	""" Writes clinical data to separate clinical patient and clinical sample files. """

	# Assign missing clinical attributes from the metadata to sample level
	clinical_header = get_header(clinical_filename)
	for val in clinical_header:
		if val not in PATIENT_CLINICAL_ATTRIBUTES: PATIENT_CLINICAL_ATTRIBUTES[val] = False

	# get the patient and sample clinical file headers
	patient_clinical_header = get_clinical_header(clinical_filename, True)
	sample_clinical_header = get_clinical_header(clinical_filename, False)

	write_clinical_datafile(patient_clinical_header, True, clinical_filename, logger)
	write_clinical_datafile(sample_clinical_header, False, clinical_filename, logger)

def main(clinical_filename, logger):
	# load clinical attribute metadata
	logger.info("Subsetting data_clinical.txt to patient and sample level files")
	load_clinical_attribute_metadata()
	split_data_clinical_attributes_main(clinical_filename, logger)

if __name__ == '__main__':
	main()
