from __future__ import division
import sys
import os
import argparse
import math
import statistics 
import numpy

ENTREZ_ID_MAPPING_PATH = "mapping-rules/entrez-id-mapping.txt"
TYPE_MAPPING_PATH = "mapping-rules/type-mapping.txt"
LOCATION_MAPPING_PATH = "mapping-rules/location-mapping.txt"


# 1) extract necessary columns from raw HGNC download
# 2) refill entrez ID that is empty (ref entrez-id-mapping.txt)
# 3) merge duplicate entrez ID entries
def cleanup_hgnc_download(_input_file_name):

	print("Processing HGNC file.....")

	# make sure every gene entry is associated with entrez ID
	symbol_entrez_id_dict = fill_entrez_id(_input_file_name)
	print(symbol_entrez_id_dict)

	_hgnc_items = {}
 	with open(_input_file_name, "r") as _input_hgnc:
		_headers = _input_hgnc.readline().rstrip('\n').rstrip('\r').split('\t');
		for _line in _input_hgnc:
			_items = _line.rstrip("\r").rstrip("\n").split('\t')
			_entrez_id = _items[_headers.index("entrez_id")]
			_hugo_symbol = _items[_headers.index("symbol")]
			if _hgnc_items.has_key(_entrez_id):
				# merge entry with same entrez ID into prev symbol of exisitng
				print("to merge")
				print(_entrez_id)
			else: 
				_hgnc_items[_entrez_id] = {
					"hgnc_id": _items[_headers.index("hgnc_id")],
					"symbol": _items[_headers.index("symbol")],
					"locus_group": _items[_headers.index("locus_group")],
					"locus_type": _items[_headers.index("locus_type")],
					"location": _items[_headers.index("location")],
					"alias_symbol": _items[_headers.index("alias_symbol")],
					"prev_symbol": _items[_headers.index("prev_symbol")],
					"entrez_id": _entrez_id,
					"ensembl_gene_id": _items[_headers.index("ensembl_gene_id")]
				}
		#print(_hgnc_items)


	_input_hgnc.close()

def fill_entrez_id(_input_file_name):
	
	print(">>>>>>>>>>>>>>> Processing entries with no entrez ID")
	print(">>>>>>>>>>>>>>> checking resource: " + ENTREZ_ID_MAPPING_PATH)

	symbol_entrez_id_dict = {} # hugo_symbol as key

	# read in exising mapping
	_entrez_id_mapping = {} # hugo_symbol as key
	with open(ENTREZ_ID_MAPPING_PATH, "r") as _input_entrez_id_mapping:
		_headers = _input_entrez_id_mapping.readline()
		for _line in _input_entrez_id_mapping:
			_items = _line.rstrip("\r").rstrip("\n").split('\t')
			_entrez_id_mapping[_items[0]] = _items[1]

	# clean up no entrez ID entries
	with open(_input_file_name, "r") as _input_hgnc:
		_headers = _input_hgnc.readline().rstrip('\n').rstrip('\r').split('\t');
		for _line in _input_hgnc:
			_items = _line.rstrip("\r").rstrip("\n").split('\t')
			_entrez_id = _items[_headers.index("entrez_id")]
			_hugo_symbol = _items[_headers.index("symbol")]
			if _entrez_id == "":
				if _entrez_id_mapping.has_key(_hugo_symbol):
					if _entrez_id_mapping[_hugo_symbol] == "":
						print("Deleted entry: " + _hugo_symbol)
					else:
						print("Added entrez ID " + _entrez_id_mapping[_hugo_symbol] + " to: " + _hugo_symbol)
						symbol_entrez_id_dict[_hugo_symbol] = _entrez_id_mapping[_hugo_symbol]
				else:
					print("Error: assign entrez ID to (OR delete): " + _hugo_symbol)
					_exiting_flag = 1
			else:
				symbol_entrez_id_dict[_hugo_symbol] = _entrez_id

		# if any unassigned hugo symbol found, system exit
		# (we use entrez ID as may key in our DB for genes, therefore need to make sure
		# every gene has an entrez ID associated)
		if _exiting_flag == 1:
			print("Exiting.....")
			print("Please assign entrez ID to all entries (see above errors).")
			sys.exit()

	return symbol_entrez_id_dict

# Entries with same entrez IDs merged (as prev_symbol)
#def merge_sample_entrez_id():

# Remove all entires with `locus_type` value as `RNA, micro`
#def remove_mirna():

# Merge values `locus_group` and `locus_type` into one column `type`
def merge_type():
	_type = ""
	_locus_group = _items[2]
	_locus_type = _items[3]
	if _locus_group == "protein-coding gene":
		_type = "protein-coding"
	elif _locus_group == "non-coding RNA":
		if _locus_type == "RNA, ribosomal":
			_type = "rRNA"
		elif _locus_type == "RNA, transfer":
			_type = "tRNA"
		elif _locus_type == "RNA, small nuclear":
			_type = "snRNA"
		elif _locus_type == "RNA, small nucleolar":
			_type = "snoRNA"
		else:
			_type = "ncRNA"
	elif _locus_group == "pseudogene":
		_type = "pseudogene"
	elif _locus_group == "other":
		if _locus_type == "unknown":
			_type = "unknown"
		else:
			_type = "other"

# Merging values in `alias_symbol` and `prev_symbol` into one column `synonyms`
# Remove duplicates by prioritizing: main > previous > alias 
# Meaning, if a symbol already exists as a main symbol, even if it is also a HGNC alias/prev symbol, do not add it into the alias table; if a symbol already exists as a prev symbol, even if it is also a HGNC alias symbol, do not add it to alias table
#def merge_alias():

# Translate the `location` column into two `chromosome` and `cytoband`
def translate_location():
	"""
	_chromosome = ""
	_cytoband = ""
	if _items[6] == "":
		_chromosome = "-"
		_cytoband = "-"
	elif _items[6] in ["unplaced", "reserved", "not on reference assembly"]: 
		_chromosome = "-"
		_cytoband = _items[6]
	elif "pter" in _items[6]: #"22pter-q11"
		_chromosome = _items[6].split("pter")[0]
		_cytoband = _items[6]
	elif "q" in _items[6]:
		continue
	elif "p" in _items[6]:
		continue
	elif _items[6] != "" and "q" not in _items[6] and "p" not in _items[6]:
		continue
	"""

# Simply concatenate `supp_main.txt`
#def add_supp_main():

# merge the supplemental alias list `supp_alias.txt`
def add_supp_alias():
	with open("/Users/suny1/gene_table_clean_up/final_alias_table.txt", "r") as _input_alias_list:
		_header = _input_alias_list.readlines()
		for _line in _input_alias_list:
			_items = _line.rstrip("\r").rstrip("\n").split('\t')
			if _alias_items.has_key(_items[1]):
				_existing_symbol_str = _alias_items[_items[1]]["alias_symbol"]
				_alias_items[_items[1]]["alias_symbol"] = _existing_symbol_str + "|" + _items[0]
			else:
				_alias_items[_items[1]] = {
					"entrez_id": _items[1],
					"alias_symbol": _items[0]
				}
	_input_alias_list.close()

def generate_output():
	_outputF = open("/Users/suny1/gene_table_clean_up/complete_final_table.txt", "w")
	_outputF.write("entrez_id\tsymbol\tchromosome\tcytoband\ttype\tsynonyms\thgnc_id\tensembl_id\n")
	for _final_gene_item in _final_gene_items:
		_outputF.write(
			_final_gene_item["entrez_id"] + "\t" + 
			_final_gene_item["symbol"] + "\t" + 
			_final_gene_item["chromosome"] + "\t" + 
			_final_gene_item["cytoband"] + "\t" + 
			_final_gene_item["type"] + "\t" + 
			_final_gene_item["synonyms"] + "\t" + 
			_final_gene_item["hgnc_id"] + "\t" + 
			_final_gene_item["ensembl_id"] + "\n"				
			)

def main():
	
	parser = argparse.ArgumentParser()
	parser.add_argument('-i','--input-hgnc-file-name', action = 'store', dest = 'input_hgnc_file_name', required = True, help = 'Name of the expression file to normalized')
	parser.add_argument('-m','--input-supp-main-name', action = 'store', dest = 'input_supp_main_file_name', required = False, help = 'Name of the supp main file to be used as reference distribution')
	parser.add_argument('-a','--input-supp-alias-name', action = 'store', dest = 'input_supp_alias_file_name', required = False, help = 'Name of the supp alias file to be used as reference distribution')
	parser.add_argument('-o','--output-file-name', action = 'store', dest = 'output_file_name', required = False, help = 'Name of the output file')
	args = parser.parse_args()

	input_hgnc_file_name = args.input_hgnc_file_name
	input_supp_main_file_name = args.input_supp_main_file_name
	input_supp_alias_file_name = args.input_supp_alias_file_name
	output_file_name = args.output_file_name

	cleanup_hgnc_download(input_hgnc_file_name)



if __name__ == '__main__':
	main()