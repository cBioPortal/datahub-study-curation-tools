#! /usr/bin/env python

#
# Copyright (c) 2018 Memorial Sloan Kettering Cancer Center.
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY, WITHOUT EVEN THE IMPLIED WARRANTY OF
# MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.  The software and
# documentation provided hereunder is on an "as is" basis, and
# Memorial Sloan Kettering Cancer Center
# has no obligations to provide maintenance, support,
# updates, enhancements or modifications.  In no event shall
# Memorial Sloan Kettering Cancer Center
# be liable to any party for direct, indirect, special,
# incidental or consequential damages, including lost profits, arising
# out of the use of this software and its documentation, even if
# Memorial Sloan Kettering Cancer Center
# has been advised of the possibility of such damage.
#
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import division
import sys
import os
import argparse
import math


# names - clinical file
CLIN_SAMPLE_ID_COL_ID = "SAMPLE_ID"
CLIN_PATIENT_ID_COL_ID = "PATIENT_ID"
CLIN_SS_COL_ID = "SOMATIC_STATUS"
CLIN_SS_COL_PRIORITY = "1"
CLIN_SS_COL_TYPE = "STRING"
CLIN_SS_COL_DES = "Somatic Status"
CLIN_SS_COL_NAME = "Somatic Status"

# array of column names (by order)
_headerItems = [	
	CLIN_SS_COL_ID,	
	CLIN_SS_COL_PRIORITY,
	CLIN_SS_COL_TYPE,
	CLIN_SS_COL_DES,
	CLIN_SS_COL_NAME
]

def addUnified(_allSamplesStatus, _inputFile, _outputFile):

	_outputFile = open(_outputFile, 'w')

	with open(_inputFile, 'r') as _inputFile:
		for _line in _inputFile:
			if _line.startswith("#") or _line.startswith(CLIN_SAMPLE_ID_COL_ID) or _line.startswith(CLIN_PATIENT_ID_COL_ID):
				_newline = _line.rstrip("\n") + "\t" + _headerItems.pop()
			else:
				if _allSamplesStatus == "1": # matched
					_newline = _line.rstrip("\n") + "\t" + "Matched"
				elif _allSamplesStatus == "0": # unmatched
					_newline = _line.rstrip("\n") + "\t" + "Unmatched"
		
			_outputFile.write(_newline + "\n")		

	_outputFile.close()


def addByList(_sampleStatusList, _inputFile, _outputFile):

	_sampleMap = {}

	with open(_sampleStatusList, 'r') as _sampleStatusList:
		for _line in _sampleStatusList:
			if not _line.startswith(CLIN_SAMPLE_ID_COL_ID):
				_items = _line.rstrip("\n").split("\t")
				_sampleMap[_items[0]] = _items[1]

	_outputFile = open(_outputFile, 'w')
	
	with open(_inputFile, 'r') as _inputFile:
		_posSampleId = -1
		for _line in _inputFile:	
			if _line.startswith("#"):
				_newline = _line.rstrip("\n") + "\t" + _headerItems.pop()
			elif _line.startswith(CLIN_SAMPLE_ID_COL_ID) or _line.startswith(CLIN_PATIENT_ID_COL_ID):
				_attrIdHeaderItems = _line.rstrip("\n").split("\t")
				_posSampleId = _attrIdHeaderItems.index(CLIN_SAMPLE_ID_COL_ID)
				_newline = _line.rstrip("\n") + "\t" + _headerItems.pop()
			else:
				_valueItems = _line.rstrip("\n").split("\t")
				_newline = _line.rstrip("\n") + "\t" + _sampleMap[_valueItems[_posSampleId]]

			_outputFile.write(_newline + "\n")

	_outputFile.close()


def main():

	parser = argparse.ArgumentParser()
	parser.add_argument('-i','--input-clinical-file-name', action = 'store', dest = 'input_clinical_file_name', required = True, help = 'Original Clinical File')	
	parser.add_argument('-l','--input-sample-status-list', action = 'store', dest = 'input_sample_status_list', required = False, help = 'List of Sample vs. Matched Normal Status (Optional)')	
	parser.add_argument('-s','--overall-status', action = 'store', dest = 'status_for_all_samples', required = False, help = 'Unified Status for all samples (Optional)')	
	parser.add_argument('-o','--onput-file-name', action = 'store', dest = 'output_file_name', required = True, help = 'Output File')	
	args = parser.parse_args()

	_inputClinicalFile = args.input_clinical_file_name
	_outputFileName = args.output_file_name

	if args.status_for_all_samples is not None:
		if args.status_for_all_samples is "1" or "0":
			addUnified(args.status_for_all_samples, args.input_clinical_file_name, args.output_file_name)
		else:
			print("Error: Defined 'Sample Status' Value Not Valid (1/0)")

	elif args.input_sample_status_list is not None:
		addByList(args.input_sample_status_list, args.input_clinical_file_name, args.output_file_name)

	else:
		print("\nError: Must define a unified value OR a detailed sample <> status list.\n")
		sys.exit(2)

if __name__ == '__main__':
	main()