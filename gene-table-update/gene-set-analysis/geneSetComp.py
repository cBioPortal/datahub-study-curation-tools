import os
import sys
import argparse
import xml.etree.ElementTree as ET
from datetime import date

def main():

	parser = argparse.ArgumentParser()
	parser.add_argument('-i','--input-msigdb-file', action = 'store', dest = 'input_msigdb_file', required = True, help = '(Required) msigDB file')	
	parser.add_argument('-r','--input-hgnc-file', action = 'store', dest = 'input_hgnc_file', required = True, help = '(Required) Gene Table file')
	args = parser.parse_args()

	hgnc_input_file = args.input_hgnc_file
	msigdb_input_file = args.input_msigdb_file
	_output_file_name = "gene-set-analysis-result-" + date.today().strftime("%b-%d-%Y") + ".txt"
	_output_file = open(_output_file_name, "w")

	# create dictionary for all HGNC genes (from current input folder); value is empty
	hgnc_gene_entrez_id_dict = {} # entrez ID as key
	with open(hgnc_input_file, "r") as _input_hgnc:
		_headers = _input_hgnc.readline()
		for _line in _input_hgnc:
			_items = _line.rstrip("\r").rstrip("\n").split('\t')
			hgnc_gene_entrez_id_dict[_items[0]] = ""

	# extract msigDB gene sets 
	gene_set_dict = {} # standard name as key, entrez ID (array) as values
	tree = ET.parse(msigdb_input_file)
	root = tree.getroot()
	for _geneset in root:		
		_mapping_arr = _geneset.attrib['MEMBERS_MAPPING'].split(",")
		gene_set_dict[_geneset.attrib['STANDARD_NAME']] = _geneset.attrib['MEMBERS_MAPPING'].split("|")

	# compare and list missing genes
	for key, value in gene_set_dict.items():
		for _mapping in value:
			_set_flag = 0
			_items = _mapping.split(",")
			for _entrezID_or_symbol in _items:
				_flag = 0
				if _entrezID_or_symbol in hgnc_gene_entrez_id_dict:
					_flag = 1
			if _flag == 0:
				_output_file.write(key + " is missing: " + _mapping + "\n")
				_set_flag = 1
		if _set_flag == 0:
			_output_file.write(">>>>> Genes in set " + key + " are all included.\n")


if __name__ == '__main__':
	main()