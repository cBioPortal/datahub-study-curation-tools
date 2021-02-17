from __future__ import division
import sys
import os
import argparse

# define path to mappings
ENTREZ_ID_MAPPING_PATH = "mappings/entrez-id-mapping.txt"
TYPE_MAPPING_PATH = "mappings/type-mapping.txt"
LOCATION_MAPPING_PATH = "mappings/location-mapping.txt"
MAIN_SUPP_PATH = "supp-files/main-supp/complete_supp_main.txt"
ALIAS_SUPP_PATH = "supp-files/alias-supp.txt"

gene_dict = {}

# 1) extract necessary columns from raw HGNC download
# 2) refill entrez ID that is empty (ref entrez-id-mapping.txt)
# 3) merge duplicate entrez ID entries into prev symbols
def cleanup_entrez_id(_input_file_name):

	# read in exising mapping
	print("Checking resource: Entrez ID mapping >>>>>>>>>>>>>>>")
	_entrez_id_mapping = {} # hugo_symbol as key
	with open(ENTREZ_ID_MAPPING_PATH, "r") as _input_entrez_id_mapping:
		_headers = _input_entrez_id_mapping.readline()
		for _line in _input_entrez_id_mapping:
			_items = _line.rstrip("\r").rstrip("\n").split('\t')
			_entrez_id_mapping[_items[0]] = _items[1]

	_exiting_flag = 0 # exiting signal for non-complete entrez ID def
	print("Cleaning up Entrez IDs >>>>>>>>>>>>>>>")
	with open(_input_file_name, "r") as _input_hgnc:
		_headers = _input_hgnc.readline().rstrip('\n').rstrip('\r').split('\t')
		for _line in _input_hgnc:
			
			_items = _line.rstrip("\r").rstrip("\n").split('\t')
			
			_entrez_id = _items[_headers.index("entrez_id")]
			_hugo_symbol = _items[_headers.index("symbol")]

			# fix entries with no entrez ID associated in HGNC
			if _entrez_id == "":
				if _entrez_id_mapping.has_key(_hugo_symbol):
					if _entrez_id_mapping[_hugo_symbol] == "R":
						print("Deleted entry: " + _hugo_symbol)
						continue
					else:
						print("Added entrez ID " + _entrez_id_mapping[_hugo_symbol] + " to: " + _hugo_symbol)
						_entrez_id = _entrez_id_mapping[_hugo_symbol]
				else:
					print("Error: assign entrez ID to (OR delete) : " + _hugo_symbol)
					_exiting_flag = 1 # found HGNC genes with no entrez ID/delete status already defined

			# extract essential columns from HGNC for building new tables
			if gene_dict.has_key(_entrez_id):
				# merge entry with same entrez ID into prev symbol of exisitng
				print("Merge " + _hugo_symbol + " into " + gene_dict[_entrez_id]["symbol"] + " as prev symbols.")
				gene_dict[_entrez_id]["prev_symbol"] = gene_dict[_entrez_id]["prev_symbol"] + "|" + _hugo_symbol
			else: 
				gene_dict[_entrez_id] = {
					"hgnc_id": _items[_headers.index("hgnc_id")],
					"symbol": _items[_headers.index("symbol")],
					"locus_group": _items[_headers.index("locus_group")],
					"locus_type": _items[_headers.index("locus_type")],
					"type": "",
					"location": _items[_headers.index("location")],
					"chromosome": "",
					"cytoband": "",
					"alias_symbol": _items[_headers.index("alias_symbol")],
					"prev_symbol": _items[_headers.index("prev_symbol")],
					"synonyms": "",
					"entrez_id": _entrez_id,
					"ensembl_gene_id": _items[_headers.index("ensembl_gene_id")]
				}

		# if any unassigned hugo symbol found, system exit
		# (we use entrez ID as may key in our DB for genes, therefore need to make sure
		# every gene has an entrez ID associated)
		if _exiting_flag == 1:
			print("Exiting.....")
			print("Please assign entrez ID to error entries above, go to " + ENTREZ_ID_MAPPING_PATH)
			sys.exit()

		print("Finished cleaning up entrez IDs ....\n")

# Remove all entires with `locus_type` value as `RNA, micro`
def remove_mirna():
	
	print("Removing miRNA entries >>>>>>>>>>>>>>>")
	for _key in gene_dict.keys():
		_gene_obj = gene_dict[_key]
		if _gene_obj["locus_type"] == "RNA, micro":
			del gene_dict[_key]
	print("Finished removing miRNA entries .... \n")

# Merge values `locus_group` and `locus_type` into one column `type`
def merge_type():
	
	print("Checking resource: Gene Types mapping >>>>>>>>>>>>>>>")
	_type_mapping_dict = {}
	with open(TYPE_MAPPING_PATH, "r") as _input_type_mapping:
		_headers = _input_type_mapping.readline()
		for _line in _input_type_mapping:
			_items = _line.rstrip("\r").rstrip("\n").split('\t')	
			_type_mapping_dict[_items[0] + "|" + _items[1]] = _items[2]
	
	print("Merging Gene Types >>>>>>>>>>>>>>>")
	for _key in gene_dict.keys():
		_gene_obj = gene_dict[_key]
		_type_key = _gene_obj["locus_group"] + "|" + _gene_obj["locus_type"]
		_gene_obj["type"] = _type_mapping_dict[_type_key]
	print("Finished merging gene types ....\n")

# Merging values in `alias_symbol` and `prev_symbol` into one column `synonyms`
# Remove duplicates by prioritizing: main > previous > alias 
# Meaning, if a symbol already exists as a main symbol, even if it is also a HGNC alias/prev symbol, do not add it into the alias table; if a symbol already exists as a prev symbol, even if it is also a HGNC alias symbol, do not add it to alias table
def merge_alias():

	_unavailable_symbols_for_alias = {}

	for _gene_obj in gene_dict.values():
		_unavailable_symbols_for_alias[_gene_obj["symbol"]] = ""

	print("Merging Alias (from Previous Symbols) >>>>>>>>>>>>>>>")
	for _gene_obj in gene_dict.values():
		_prev_symbols = _gene_obj["prev_symbol"].split("|")
		for _prev_symbol in _prev_symbols:
			if _unavailable_symbols_for_alias.has_key(_prev_symbol):
				continue
			elif _prev_symbol != "":
				_unavailable_symbols_for_alias[_prev_symbol] = ""
			 	if _gene_obj["synonyms"].strip() == "":
			 		_gene_obj["synonyms"] = _prev_symbol
			 	else:
			 		_gene_obj["synonyms"] = _gene_obj["synonyms"] + "|" + _prev_symbol

	print("Merging Alias (from Alias Symbols) >>>>>>>>>>>>>>>")
	for _gene_obj in gene_dict.values():
		_alias_symbols = _gene_obj["alias_symbol"].split("|")
		for _alias_symbol in _alias_symbols:
			if _unavailable_symbols_for_alias.has_key(_alias_symbol):
				continue
			elif _alias_symbol != "":
				_unavailable_symbols_for_alias[_alias_symbol] = ""
			 	if _gene_obj["synonyms"].strip() == "":
			 		_gene_obj["synonyms"] = _alias_symbol
			 	else:
			 		_gene_obj["synonyms"] = _gene_obj["synonyms"] + "|" + _alias_symbol

	print("Finished Merging Alias ..... \n")

# Translate the `location` column into two `chromosome` and `cytoband`
def translate_location():
	
	print("Checking resource: Locations mapping >>>>>>>>>>>>>>>")
	_location_mapping_dict = {}
	with open(LOCATION_MAPPING_PATH, "r") as _input_location_mapping:
		_headers = _input_location_mapping.readline()
		for _line in _input_location_mapping:
			_items = _line.rstrip("\r").rstrip("\n").split('\t')	
			_location_mapping_dict[_items[0]] = _items[1]

	print ("Translating HGNC location >>>>>>>>>>>>>")
	for _gene_obj in gene_dict.values():
		if _location_mapping_dict.has_key(_gene_obj["location"]):
			# special format (ref mapping)
			_gene_obj["chromosome"] = _location_mapping_dict[_gene_obj["location"]]
		else: 
			# parsing standard format (e.g. 19q13.12, 4q31.21-q31.22)
			for _index in range(len(_gene_obj["location"])):
				if _gene_obj["location"][_index] in ["q", "p"]:
					_gene_obj["chromosome"] = _gene_obj["location"].split(_gene_obj["location"][_index])[0]
					break
		
		_gene_obj["cytoband"] = _gene_obj["location"]

	print ("Finished translating HGNC location >>>>>>>>>>>>>\n")


# Concatenate `supp_main.txt`
def add_supp_main():
	print ("Adding main supplement genes >>>>>>>>>>>>>")
	with open(MAIN_SUPP_PATH, "r") as _input_main_supp:
		_headers = _input_main_supp.readline()
		_exiting_flag = 0
		for _line in _input_main_supp:
			_items = _line.rstrip("\r").rstrip("\n").split('\t')	
			if gene_dict.has_key(_items[0]):
				_exiting_flag = 1
				print("Error: Duplicate entrez ID detected:" + _items[1] + "\t" + _items[0])
			else:
				gene_dict[_items[0]] = {
					"hgnc_id": "",
					"symbol": _items[1],
					"locus_group": "",
					"locus_type": "",
					"type": _items[4],
					"location": "",
					"chromosome": _items[2],
					"cytoband": _items[3],
					"alias_symbol": "",
					"prev_symbol": "",
					"synonyms": "",
					"entrez_id": _items[0],
					"ensembl_gene_id": _items[5]
				}

	# if an supplment gene's entrez ID already exist in HGNC, system would exit
	# Remove this gene from supp-main, or make it as an alias. 
	if _exiting_flag == 1:
		print("Exiting.....")
		print("Please fix the entries with duplicate entrez IDs listed as errors above, under " + MAIN_SUPP_PATH)
		sys.exit()

# merge the supplemental alias list `supp_alias.txt`
def add_supp_alias():
	with open(ALIAS_SUPP_PATH, "r") as _input_alias_supp:
		_header = _input_alias_supp.readlines()
		for _line in _input_alias_supp:
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
	parser.add_argument('-i','--input-hgnc-file', action = 'store', dest = 'input_hgnc_file', required = True, help = 'downloaded HGNC file')
	parser.add_argument('-m','--input-supp-main-file', action = 'store', dest = 'input_supp_main_file', required = False, help = 'File of genes to supplement to main table')
	parser.add_argument('-a','--input-supp-alias-file', action = 'store', dest = 'input_supp_alias_file', required = False, help = 'File of genes to supplement to alias table')
	parser.add_argument('-o','--output-file-name', action = 'store', dest = 'output_file_name', required = False, help = 'Name of the output file')
	args = parser.parse_args()

	input_hgnc_file = args.input_hgnc_file
	input_supp_main_file = args.input_supp_main_file
	input_supp_alias_file = args.input_supp_alias_file
	output_file_name = args.output_file_name

	cleanup_entrez_id(input_hgnc_file)
	remove_mirna()
	merge_type()
	merge_alias()
	translate_location()


if __name__ == '__main__':
	main()