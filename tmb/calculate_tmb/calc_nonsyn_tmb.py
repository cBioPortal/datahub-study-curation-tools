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
import numpy

LOG_STR = ""

# WGS/WES CDS
WES_WGS_CDS = 30

# egilible variants (for counting mutations)
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

# names - case list file
SEQ_CASE_LIST_FILE_NAME = "cases_sequenced.txt"
SEQ_CASE_LIST_FIELD_NAME = "case_list_ids:"

# names - MAF file
MAF_FILE_NAME = "data_mutations.txt"
MAF_VC_COL_ID = "Variant_Classification"
MAF_ID_COL_ID = "Tumor_Sample_Barcode"
MAF_SOMATIC_COL_ID = "Mutation_Status"

# names  - matrix file
MATRIX_FILE_NAME = "data_gene_panel_matrix.txt"
MATRIX_SAMPLE_ID_COL = "SAMPLE_ID"
MATRIX_MUT_COL = "mutations"

# names - clinical file
CLIN_INPUT_FILE_NAME = "data_clinical_sample.txt"
CLIN_INPUT_BCR_FILE_NAME = "data_bcr_clinical_data_sample.txt"
CLIN_OUTPUT_FILE_NAME = "tmb_output_data_clinical_sample.txt"
CLIN_ID_COL_ID = "SAMPLE_ID"
CLIN_TMB_COL_ID = "TMB_NONSYNONYMOUS"
CLIN_TMB_COL_PRIORITY = "1"
CLIN_TMB_COL_TYPE = "NUMBER"
CLIN_TMB_COL_DES = "TMB (nonsynonymous)"
CLIN_TMB_COL_NAME = "TMB (nonsynonymous)"

# names - panel file
PANEL_STABLE_ID_FIELD_NAME = "stable_id:"
PANEL_CDS_FIELD_NAME = "number_of_profiled_coding_base_pairs:"

# msgs
PANEL_THRESHOLD = 0.2
PANEL_THRESHOLD_MSG = "NA"

###### 
# extract coding sequence length from gene panels and map to each sample
######
def extractCDS(_inputStudyFolder, _panelFolderPath, _sampleMap):

	_cdsMap = {}

	# extract CDS field from all panel files
	for _panelFileName in os.listdir(_panelFolderPath):
		with open(_panelFolderPath + "/" + _panelFileName ,'r') as _panelFile:
			_panelID = ""
			for _line in _panelFile:
				if _line.startswith(PANEL_STABLE_ID_FIELD_NAME):
					_panelID = _line.split(':')[1].strip()
					_cdsMap[_panelID] = float(0)
				elif _line.startswith(PANEL_CDS_FIELD_NAME):
					_cdsMap[_panelID] = float(int(_line.split(':')[1].strip()) / 1000000)

	# Whole genome and whole exome ids are introduced as panels into the matrix file.
	# Add these to the cdsMap.
	_cdsMap.update({'WXS':30, 'WGS':30, 'WXS/WGS':30})
	
	# using gene matrix to map CDS to each sample 
	with open(_inputStudyFolder + "/" + MATRIX_FILE_NAME ,'r') as _matrixFile:
		_posSampleId = -1
		_posMutPanel = -1
		for _line in _matrixFile:
			if _line.startswith(MATRIX_SAMPLE_ID_COL):
				# parsing matrix header
				_headers = _line.rstrip("\n").rstrip('\r').split('\t')
				_posSampleId = _headers.index(MATRIX_SAMPLE_ID_COL)
				_posMutPanel = _headers.index(MATRIX_MUT_COL)
			else:
				# parsing content
				_items = _line.rstrip("\n").rstrip('\r').split('\t')
				_sampleID = _items[_posSampleId]
				_panelID = _items[_posMutPanel]
				_cds = _cdsMap[_panelID]

				if _sampleMap.has_key(_sampleID):
					_sampleMap[_sampleID]["cds"] = _cds
				else:
					# sample in matrix (sequenced) but not in MAF
					_sampleMap[_sampleID] = { 
						'vc_count': 0,
						'tmb': 0,
						'cds': _cds
					}
	
	return _sampleMap

###### 
# count eligible variants for all samples from MAF
######
def cntVariants(_inputStudyPath):

	_result = {}
	with open(_inputStudyPath + "/" + MAF_FILE_NAME,'r') as _maf:

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
							'tmb': 0,
							'cds': WES_WGS_CDS # samples not in matrix are WGS/WES
						}

	return _result

###### 
# calculate TMB for every sample 
######
def calcTMB(_sampleMap):

	_tmbs = []

	for _sampleID in _sampleMap:
		_tmb = _sampleMap[_sampleID]["vc_count"] / _sampleMap[_sampleID]["cds"]
		if _sampleMap[_sampleID]["cds"] < PANEL_THRESHOLD:
			_sampleMap[_sampleID]["tmb"] = PANEL_THRESHOLD_MSG
		else:
			_sampleMap[_sampleID]["tmb"] = _sampleMap[_sampleID]["vc_count"] / _sampleMap[_sampleID]["cds"]
			_tmbs.append(_tmb)
	if len(_tmbs) != 0:	
		sys.stdout.write(str(max(_tmbs)) + "\t" + str(min(_tmbs)) + "\t" + str(numpy.median(_tmbs)) + "\n")
	else: 
		sys.stdout.write("No TMBs calculated.\n")

	return _sampleMap

###### 
# add TMB column to clinical file
######
def addTMB(_inputStudyFolder, _sampleTmbMap):

	# extract list of sequenced sample IDs
	_seqSampleIds = [] 
	if os.path.isfile(_inputStudyFolder + "/case_lists/" + SEQ_CASE_LIST_FILE_NAME):
		_caseListPath = _inputStudyFolder + "/case_lists/" + SEQ_CASE_LIST_FILE_NAME
		with open(_caseListPath,'r') as _caseList:
			for _line in _caseList:
				if _line.startswith(SEQ_CASE_LIST_FIELD_NAME):
					_seqSampleIds = _panelID = _line.split(':')[1].strip().split("\t")
	else:
		print("Can't find sequenced case list file!")
		sys.exit(2)


	# header for the new column in clinical sample file
	_headerItems = [	
		CLIN_TMB_COL_ID,	
		CLIN_TMB_COL_PRIORITY,
		CLIN_TMB_COL_TYPE,
		CLIN_TMB_COL_DES,
		CLIN_TMB_COL_NAME
	]

	_posSampleID = -1
	_outputClinFile = open(_inputStudyFolder + "/" + CLIN_OUTPUT_FILE_NAME,'w')

	_inputFilePath = ""
	if os.path.isfile(_inputStudyFolder + "/" + CLIN_INPUT_FILE_NAME):
		_inputFilePath = _inputStudyFolder + "/" + CLIN_INPUT_FILE_NAME
	elif os.path.isfile(_inputStudyFolder + "/" + CLIN_INPUT_BCR_FILE_NAME):
		_inputFilePath = _inputStudyFolder + "/" + CLIN_INPUT_BCR_FILE_NAME
	
	with open(_inputFilePath,'r') as _inputClinFile:

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
				if _sampleID in _sampleTmbMap:
					_newline = _line.rstrip("\n") + "\t" + str(_sampleTmbMap[_sampleID]["tmb"])
				else:
					if _sampleID in _seqSampleIds:
						_newline = _line.rstrip("\n") + "\t" + "0"
					else:
						_newline = _line.rstrip("\n") + "\t" + "NA"

			_outputClinFile.write(_newline + "\n")


def main():

	parser = argparse.ArgumentParser()
	parser.add_argument('-i','--input-study-folder', action = 'store', dest = 'input_study_folder', required = True, help = 'Input Study folder')	
	parser.add_argument('-p','--input-gene-panel-folder', action = 'store', dest = 'input_gene_panel_folder', required = True, help = 'Gene Panel folder (optional)')	
	args = parser.parse_args()

	_genePanelFolder = args.input_gene_panel_folder
	_inputStudyFolder = args.input_study_folder
	_sampleTmbMap = {}

	sys.stdout.write(os.path.basename(_inputStudyFolder) + "\t")

	if os.path.isdir(_inputStudyFolder) and os.path.isdir(_genePanelFolder):
		# Find matrix file -> identify CDS for targeted panels 
		if os.path.isfile(_inputStudyFolder + "/" + MATRIX_FILE_NAME):
			sys.stdout.write("Targeted\t")
			_sampleTmbMap = calcTMB(extractCDS(_inputStudyFolder, _genePanelFolder, cntVariants(_inputStudyFolder)))
		else: # No matrix file -> WGS/WES studies
			sys.stdout.write("WGS/WES\t")
			_sampleTmbMap = calcTMB(cntVariants(_inputStudyFolder))
		
		# check if any TMB are generated, otherwise skip modifying clinical file
		_update_flag = "false"
		for _sampleTmbInst in _sampleTmbMap.values():
			if _sampleTmbInst["tmb"] != PANEL_THRESHOLD_MSG:
				_update_flag = "true"
		if _update_flag == "true":
			addTMB(_inputStudyFolder, _sampleTmbMap)
	
	else:
		print("Error input folder path(s)!")
		sys.exit(2)

if __name__ == '__main__':
	main()