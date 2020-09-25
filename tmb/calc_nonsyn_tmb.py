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

CLIN_ID_COL_ID = "SAMPLE_ID"

CLIN_TMB_COL_ID = "TMB_nonsynonymous"
CLIN_TMB_COL_PRIORITY = "1"
CLIN_TMB_COL_TYPE = "STRING"
CLIN_TMB_COL_DES = "TMB (nonsynonymous)"
CLIN_TMB_COL_NAME = "TMB (nonsynonymous)"

PANEL_FIELD_NAME = "number_of_profiled_coding_base_pairs:"

MAF_VC_COL_ID = "Variant_Classification"
MAF_ID_COL_ID = "Tumor_Sample_Barcode"
MAF_SOMATIC_COL_ID = "Mutation_Status"

VC_NONSYNONYMOUS_LIST = [
	"Frame_Shift_Del", 
	"Frame_Shift_Ins", 
	"In_Frame_Del", 
	"In_Frame_Ins", 
	"Missense_Mutation", 
	"Nonsense_Mutation", 
	"Splice_Site", 
	"Nonstop_Mutation", 
	"Splice_Region"
]

def extractCDS(_panel):

	_cdsLength = 0
	with open(_panel,'r') as _panel:
		for _line in _panel:
			if _line.startswith('number_of_profiled_coding_base_pairs:'):
				_cdsLength = _line.split(':')[1].strip()

	return float(int(_cdsLength) / 1000000)

def cntVariants(_maf):

	_result = {}

	with open(_maf,'r') as _maf:

		_headers = []
		_posSampleID = -1
		_posVariantClass = -1

		for _line in _maf:
			if _line.startswith('#'):
				continue
			elif _line.startswith('Hugo_Symbol'):
				# parsing MAF header
				_headers = _line.rstrip("\n").rstrip('\r').split('\t')
				_posSampleID = _headers.index(MAF_ID_COL_ID)
				_posVariantClass = _headers.index(MAF_VC_COL_ID)
			else:	
				# parsing content
				_items = _line.rstrip("\n").rstrip('\r').split('\t')

				_sampleID = _items[_posSampleID]
				_variantClass = _items[_posVariantClass]

				if _variantClass in VC_NONSYNONYMOUS_LIST :
					if _sampleID in _result:
						_result[_sampleID]["vc_count"] = _result[_sampleID]["vc_count"] + 1
					else:
						_result[_sampleID] = {
							'vc_count': 1,
							'tmb': 0
						}

	return _result

def calcTMB(_sampleDict, _cdsLength):

	for _sampleID in _sampleDict:
		_sampleDict[_sampleID]["tmb"] = _sampleDict[_sampleID]["vc_count"] / _cdsLength

	return _sampleDict

def addTMB(_inputClinFile, _outputClinFile, _sampleTmbMap):

	_headerItems = [	
		CLIN_TMB_COL_ID,	
		CLIN_TMB_COL_PRIORITY,
		CLIN_TMB_COL_TYPE,
		CLIN_TMB_COL_DES,
		CLIN_TMB_COL_NAME
	]

	_posSampleID = -1
	_outputClinFile = open(_outputClinFile,'w')

	with open(_inputClinFile,'r') as _inputClinFile:

		for _line in _inputClinFile:
			
			# meta headers
			if _line.startswith("#"): 
				_newline = _line.rstrip("\n") + "\t" + _headerItems.pop()
				
			# attr ID header line
			elif CLIN_ID_COL_ID in _line.rstrip("\n").split("\t"): 
				_posSampleID = _line.rstrip("\n").split("\t").index(CLIN_ID_COL_ID)
				_newline = _line.rstrip("\n") + "\t" + _headerItems.pop()

			# values
			else: 
				_sampleID = _line.split("\t")[_posSampleID]
				_newline = _line.rstrip("\n") + "\t" + str(_sampleTmbMap[_sampleID]["tmb"])

			_outputClinFile.write(_newline + "\n")


def main():

	parser = argparse.ArgumentParser()
	parser.add_argument('-p','--input-gene-panel-filename', action = 'store', dest = 'input_gene_panel_filename', required = False, help = 'Gene panel filename')	
	parser.add_argument('-m','--input-maf-filename', action = 'store', dest = 'input_maf_filename', required = True, help = 'MAF filename')
	parser.add_argument('-c','--input-clinical-filename', action = 'store', dest = 'input_clinical_filename', required = True, help = 'Clinical (sample) filename')
	parser.add_argument('-o','--output-clinical-file-name', action = 'store', dest = 'output_clinical_filename', required = True, help = 'Name of the output clinical file')
	args = parser.parse_args()

	maf_filename = args.input_maf_filename
	gene_panel_filename = args.input_gene_panel_filename
	input_clinical_filename = args.input_clinical_filename
	output_clinical_filename = args.output_clinical_filename


	# check if the input file exists
	if not os.path.isfile(maf_filename):
		print("ERROR: MAF file %s doesn't exist or is not a file" % (maf_filename))
		parser.print_help()
		sys.exit(2)

	if not os.path.isfile(gene_panel_filename):
		print("ERROR: Gene Panel file %s doesn't exist or is not a file" % (gene_panel_filename))
		parser.print_help()
		sys.exit(2)

	if not os.path.isfile(input_clinical_filename):
		print("ERROR: Clinical file %s doesn't exist or is not a file" % (clinical_filename))
		parser.print_helpinput_clinical_filename		
		sys.exit(2)

	# calculation
	# output --- Dictionary {ID1: {mut #:, tmb:}, ID2: {mut #:, tmb:}, ...}
	_sampleTmbMap = calcTMB(cntVariants(maf_filename), extractCDS(gene_panel_filename))
	addTMB(input_clinical_filename, output_clinical_filename, _sampleTmbMap)

if __name__ == '__main__':
	main()