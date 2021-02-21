from __future__ import division
import sys
import os
import argparse
import math
import statistics 
import numpy

REF_KEY = "Entrez_Gene_Id"
HUGO_SYMBOL_KEY = "Hugo_Symbol"

# calculate reference for each gene
# input: reference file (in standard expression format, entrez_gene_id required)
# output: dictionary (key is entrez_gene_id, value is mean & standard diviation)
def calc_ref(_inputFileName):
	
	print("Calculating reference distribution...")

	_result = {} 
	_pos = 0 # column position of entrez_id 

	with open(_inputFileName,'r') as _inputFile:
		
		# parsing header
		_headers = _inputFile.readline().rstrip('\n').rstrip('\r').split('\t');
		_pos = _headers.index(REF_KEY)
		
		# parsing content
		for _line in _inputFile:

			_items = _line.rstrip('\n').rstrip('\r').split('\t')
			
			_entrezID = _items[_pos] # entrez ID
			_vals = [] # reference expression value set for this gene
			
			# log transform
			for _item in _items[_pos+1:len(_items)]:
				if _item != "NA" and float(_item) > 0:
					_vals.append(math.log(float(_item) + 1, 2))
			# calculate mean and std for each gene/row	

			if len(_vals) <= 1:
				_result[_entrezID] = {
					'mean': 0,
					'std': 0
				}
			else:
				_result[_entrezID] = {
					'mean': numpy.mean(_vals),
					'std': numpy.std(_vals)
				}
	return(_result)

# calculate zscore for each gene
# input: expression file to be normalized (in standard expression format, entrez_gene_id required)
# output: array of strings of each row, including header
def calc_zscores(_inputFileName, _refDict):

	print("Calculating Z-scores...")

	_resultLinesArr = [] # overall result
	_pos = 0 # column position of entrez_id 

	with open(_inputFileName,'r') as _inputFile:

		# parsing header
		_headers = _inputFile.readline().rstrip('\n').rstrip('\r').split('\t');
		_posEntrezID = _headers.index(REF_KEY)	
		_posHugoSymbol = _headers.index(HUGO_SYMBOL_KEY)
		_resultLinesArr.append('\t'.join(_headers))

		# parsing content line by line
		for _line in _inputFile:
			
			_resultLineArr = [] # results of current row/gene
			_items = _line.rstrip('\n').rstrip('\r').split('\t')
			
			_entrezID = _items[_posEntrezID] # entrez ID
			_hugoSymbol = _items[_posHugoSymbol] # hugo symbol
			_resultLineArr.append(_hugoSymbol)
			_resultLineArr.append(_entrezID)

			for _rawVal in _items[_posEntrezID+1:len(_items)]:
				
				_val = 0
				_zscore = ""

				# log transform positive raw exp value
				if _rawVal != "NA" and float(_rawVal) > 0:
					_val = math.log(float(_rawVal) + 1, 2)
				
				# calculate zscore
				if _rawVal == "NA" or _refDict[_entrezID]["std"] == 0: 
					_zscore = "NA" # if STD is 0, zscore is NA
				else: 
					_zscore = str(round((_val - _refDict[_entrezID]["mean"]) / _refDict[_entrezID]["std"],4))
				_resultLineArr.append(_zscore)

			_resultLinesArr.append('\t'.join(_resultLineArr))
		
		return _resultLinesArr

def main():

	parser = argparse.ArgumentParser()
	parser.add_argument('-i','--input-expression-file-name', action = 'store', dest = 'input_exp_file_name', required = True, help = 'Name of the expression file to normalized')
	parser.add_argument('-r','--input-reference-file-name', action = 'store', dest = 'input_ref_file_name', required = True, help = 'Name of the expression file to be used as reference distribution')
	parser.add_argument('-o','--output-file-name', action = 'store', dest = 'output_file_name', required = True, help = 'Name of the output file')
	args = parser.parse_args()

	input_exp_file_name = args.input_exp_file_name
	input_ref_file_name = args.input_ref_file_name
	output_file_name = args.output_file_name
	
	_outputFile = open(output_file_name,'w')
	_outputFile.write("\n".join(calc_zscores(input_exp_file_name, calc_ref(input_ref_file_name))))
	_outputFile.close()
	print("DONE!")

if __name__ == '__main__':
	main()
