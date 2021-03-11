import os
import sys
import argparse
import logging
import shutil
from datetime import date

# define path to mappings
TYPE_MAPPING_PATH = "mappings/type-mapping.txt"
LOCATION_MAPPING_PATH = "mappings/location-mapping.txt"

# define path to supps
MAIN_SUPP_PATH = "supp-files/main-supp/complete-supp-main.txt"
ALIAS_SUPP_PATH = "supp-files/alias-supp.txt"
ENTREZ_ID_SUPP_PATH = "supp-files/entrez-id-supp.txt"
LOCATION_SUPP_PATH = "supp-files/location-supp.txt"

# global gene data dictionary
# entrez id is key
# Fields:
#	"hgnc_id": from HGNC, only HGNC genes have it
#	"symbol": unique, not null
#	"locus_group": from HGNC 
#	"locus_type": from HGNC
#	"type": merged from "locus_group & locus type"
#	"location": from HGNC
#	"chromosome": translated from "location" OR current DB OR NCBI
#	"cytoband": translated from "location" OR current DB OR NCBI
#	"alias_symbol": from HGNC
#	"prev_symbol": from HGNC
#	"synonyms": merged from "alias_symbol" & "prev_symbol" OR supp_alias
#	"entrez_id": from HGNC OR NCBI
#	"ensembl_gene_id": from HGNC OR NCBI
gene_dict = {} 


# 1) extract necessary columns from raw HGNC download
# 2) refill entrez ID that is empty (ref entrez-id-mapping.txt)
# 3) merge duplicate entrez ID entries into prev symbols
def cleanup_entrez_id(_input_file_name):

	# read in exising mapping
	logging.info("Checking resource: Entrez ID mapping >>>>>>>>>>>>>>>")
	_entrez_id_dict = {} # hugo_symbol as key
	with open(ENTREZ_ID_SUPP_PATH, "r") as _input_entrez_id_supp:
		_headers = _input_entrez_id_supp.readline()
		for _line in _input_entrez_id_supp:
			_items = _line.rstrip("\r").rstrip("\n").split('\t')
			_entrez_id_dict[_items[0]] = _items[1]

	_exiting_flag = 0 # exiting signal for non-complete entrez ID def
	logging.info("Cleaning up Entrez IDs >>>>>>>>>>>>>>>")
	with open(_input_file_name, "r") as _input_hgnc:
		_headers = _input_hgnc.readline().rstrip('\n').rstrip('\r').split('\t')
		for _line in _input_hgnc:
			
			_items = _line.rstrip("\r").rstrip("\n").split('\t')
			
			_entrez_id = _items[_headers.index("entrez_id")]
			_hugo_symbol = _items[_headers.index("symbol")]

			# fix entries with no entrez ID associated in HGNC
			if _entrez_id == "":
				if _entrez_id_dict.has_key(_hugo_symbol):
					if _entrez_id_dict[_hugo_symbol] == "R":
						logging.info("Deleted entry: " + _hugo_symbol)
						continue
					else:
						logging.info("Added entrez ID " + _entrez_id_dict[_hugo_symbol] + " to: " + _hugo_symbol)
						_entrez_id = _entrez_id_dict[_hugo_symbol]
				else:
					logging.error("Assign entrez ID to (OR delete) : " + _hugo_symbol)
					_exiting_flag = 1 # found HGNC genes with no entrez ID/delete status already defined

			# extract essential columns from HGNC for building new tables
			if gene_dict.has_key(_entrez_id):
				# merge entry with same entrez ID into prev symbol of exisitng
				logging.info("Merge " + _hugo_symbol + " into " + gene_dict[_entrez_id]["symbol"] + " as prev symbols.")
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
			logging.info("Exiting.....")
			logging.info("Please assign entrez ID to error entries above, go to " + ENTREZ_ID_SUPP_PATH)
			sys.exit()

		logging.info("Finished cleaning up entrez IDs ....\n")

# Remove all entires with `locus_type` value as `RNA, micro`
def remove_mirna():
	
	logging.info("Removing miRNA entries >>>>>>>>>>>>>>>")
	for _key in gene_dict.keys():
		_gene_obj = gene_dict[_key]
		if _gene_obj["locus_type"] == "RNA, micro":
			del gene_dict[_key]
	logging.info("Finished removing miRNA entries .... \n")

# Merge values `locus_group` and `locus_type` into one column `type`
def merge_type():
	
	logging.info("Checking resource: Gene Types mapping >>>>>>>>>>>>>>>")
	_type_mapping_dict = {} # "locus_group | locus_type" combination is entrez id
	with open(TYPE_MAPPING_PATH, "r") as _input_type_mapping:
		_headers = _input_type_mapping.readline()
		for _line in _input_type_mapping:
			_items = _line.rstrip("\r").rstrip("\n").split('\t')	
			_type_mapping_dict[_items[0] + "|" + _items[1]] = _items[2]
	
	logging.info("Merging Gene Types >>>>>>>>>>>>>>>")
	for _key in gene_dict.keys():
		_gene_obj = gene_dict[_key]
		_type_key = _gene_obj["locus_group"] + "|" + _gene_obj["locus_type"]
		_gene_obj["type"] = _type_mapping_dict[_type_key]
	logging.info("Finished merging gene types ....\n")

# Merging values in `alias_symbol` and `prev_symbol` into one column `synonyms`
# Remove duplicates by prioritizing: main > previous > alias 
# Meaning, if a symbol already exists as a main symbol, even if it is also a HGNC alias/prev symbol, do not add it into the alias table; if a symbol already exists as a prev symbol, even if it is also a HGNC alias symbol, do not add it to alias table
def merge_alias():

	_unavailable_symbols_for_alias = {}

	for _gene_obj in gene_dict.values():
		_unavailable_symbols_for_alias[_gene_obj["symbol"]] = ""

	logging.info("Merging Alias (from Previous Symbols) >>>>>>>>>>>>>>>")
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

	logging.info("Merging Alias (from Alias Symbols) >>>>>>>>>>>>>>>")
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

	logging.info("Finished Merging Alias .....\n")

# Translate the `location` column into two `chromosome` and `cytoband`
def translate_location():
	
	logging.info("Checking resource: Locations mapping >>>>>>>>>>>>>>>")
	_location_mapping_dict = {} # hgnc location vocabulary as key
	with open(LOCATION_MAPPING_PATH, "r") as _input_location_mapping:
		_headers = _input_location_mapping.readline()
		for _line in _input_location_mapping:
			_items = _line.rstrip("\r").rstrip("\n").split('\t')	
			_location_mapping_dict[_items[0]] = {
				"chr": _items[1],
				"cytoband": _items[2]
			}

	logging.info("Translating HGNC location >>>>>>>>>>>>>")
	for _gene_obj in gene_dict.values():
		if _location_mapping_dict.has_key(_gene_obj["location"]):
			# special format (ref mapping)
			_gene_obj["chromosome"] = _location_mapping_dict[_gene_obj["location"]]["chr"]
			_gene_obj["cytoband"] = _location_mapping_dict[_gene_obj["location"]]["cytoband"]
		else: 
			# parsing standard format (e.g. 19q13.12, 4q31.21-q31.22)
			for _index in range(len(_gene_obj["location"])):
				if _gene_obj["location"][_index] in ["q", "p"]:
					_gene_obj["chromosome"] = _gene_obj["location"].split(_gene_obj["location"][_index])[0]
					if "not on reference assembly" in _gene_obj["location"]:
						_gene_obj["cytoband"] = _gene_obj["location"].replace(" not on reference assembly", "")
					else:
						_gene_obj["cytoband"] = _gene_obj["location"]
					break
		
	logging.info("Finished translating HGNC location >>>>>>>>>>>>>\n")


# Concatenate gene entries `main-supp.txt`
def add_supp_main():

	logging.info("Adding main supplement genes >>>>>>>>>>>>>")
	with open(MAIN_SUPP_PATH, "r") as _input_main_supp:
		_headers = _input_main_supp.readline()
		_exiting_flag = 0
		for _line in _input_main_supp:
			_items = _line.rstrip("\r").rstrip("\n").split('\t')	
			if gene_dict.has_key(_items[0]):
				_exiting_flag = 1
				logging.error("Duplicate entrez ID detected:" + _items[1] + "\t" + _items[0])
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
	logging.info("Finished adding main supplement genes >>>>>>>>>>>>>\n")

	# if an supplment gene's entrez ID already exist in HGNC, system would exit
	# Remove this gene from supp-main, or make it as an alias. 
	if _exiting_flag == 1:
		logging.info("Exiting.....")
		logging.info("Please fix the entries with duplicate entrez IDs listed as errors above, under " + MAIN_SUPP_PATH)
		sys.exit()

# merge the supplemental alias list `alias-supp.txt`
def add_supp_alias():

	logging.info("Adding alias supplement genes >>>>>>>>>>>>>")

	_alias_items = {} # key is entrez id
	with open(ALIAS_SUPP_PATH, "r") as _input_alias_supp:
		_header = _input_alias_supp.readline()
		for _line in _input_alias_supp:
			_items = _line.rstrip("\r").rstrip("\n").split('\t')
			_alias_items[_items[0]] = _items[1]
	_input_alias_supp.close()

	for _key in _alias_items.keys():
		if gene_dict.has_key(_key): 
			if gene_dict[_key]["synonyms"] == "":
				gene_dict[_key]["synonyms"] = _alias_items[_key]
			else:
				gene_dict[_key]["synonyms"] = gene_dict[_key]["synonyms"] + "|" + _alias_items[_key]
		else: # with HGNC update, some entrez ID may become unavailable
			logging.warning(_key + "\t" + _alias_items[_key] + "entry is skipped - entrez ID does not exist in main table")
			logging.warning("Please remove entry: " + _key + "\t" + _alias_items[_key])

	logging.info("Finished adding alias supplement genes >>>>>>>>>>>>>\n")

# merge the supplemental location list `location-supp.txt`
def add_supp_location():

	logging.info("Adding supplemental location info >>>>>>>>>>>>>")

	_location_supp_items = {} # key is entrez id
	with open(LOCATION_SUPP_PATH, "r") as _input_location_supp:
		_header = _input_location_supp.readline()
		for _line in _input_location_supp:
			_items = _line.rstrip("\r").rstrip("\n").split('\t')
			_location_supp_items[_items[0]] = {
				"entrez_id": _items[0],
				"symbol": _items[1],
				"chr": _items[2],
				"cytoband": _items[3]
			}
	_input_location_supp.close()

	for _key in _location_supp_items.keys():
		if gene_dict.has_key(_key): 
			if gene_dict[_key]["chromosome"] != "-" and gene_dict[_key]["cytoband"] != "-":
				# with HGNC update, some location information may become available.
				# the location info in the supp file here needs to be removed, to reduce redundancy and also avoid conflicts
				logging.warning(_key + "\t" + _location_supp_items[_key]["symbol"] + "entry already have location info.")
				logging.warning("Please remove entry: " + _key + "\t" + _location_supp_items[_key]["symbol"])
			if gene_dict[_key]["chromosome"] == "-":
				gene_dict[_key]["chromosome"] = _location_supp_items[_key]["chr"]
			if gene_dict[_key]["cytoband"] == "-":
				gene_dict[_key]["cytoband"] = _location_supp_items[_key]["cytoband"]

		else: # with HGNC update, some entrez ID may become unavailable
			logging.warning(_key + "\t" + _location_supp_items[_key]["symbol"] + "entry is skipped - entrez ID does not exist in main table")
			logging.warning("Please remove entry: " + _key + "\t" + _location_supp_items[_key]["symbol"])

	logging.info("Finished adding alias supplement genes >>>>>>>>>>>>>\n")

def generate_output(_output_file_name):
	_output_file = open(_output_file_name, "w")
	_output_file.write("entrez_id\tsymbol\tchromosome\tcytoband\ttype\tsynonyms\thgnc_id\tensembl_id\n")
	for _gene_obj in gene_dict.values():
		_output_file.write(
				_gene_obj["entrez_id"] + "\t" + 
				_gene_obj["symbol"] + "\t" + 
				_gene_obj["chromosome"] + "\t" + 
				_gene_obj["cytoband"] + "\t" + 
				_gene_obj["type"] + "\t" + 
				_gene_obj["synonyms"] + "\t" + 
				_gene_obj["hgnc_id"] + "\t" + 
				_gene_obj["ensembl_gene_id"] + "\n"				
			)
	_output_file.close()

def main():
	
	parser = argparse.ArgumentParser()
	parser.add_argument('-i','--input-hgnc-file', action = 'store', dest = 'input_hgnc_file', required = True, help = '(Required)Downloaded HGNC file')
	parser.add_argument('-o','--output-file-name', action = 'store', dest = 'output_file_name', required = False, help = '(Optional)Name of the output file')
	args = parser.parse_args()

	_input_hgnc_file = args.input_hgnc_file

	# output folder & file name
	_output_dir = date.today().strftime("%b-%d-%Y") + "-output"
	if os.path.exists(_output_dir):
	    shutil.rmtree(_output_dir)
	os.makedirs(_output_dir)
	if args.output_file_name is None:
		_output_file_name = _output_dir + "/" + "gene-import-input-" + date.today().strftime("%b-%d-%Y") + ".txt"
	else:
		_output_file_name = _output_dir + "/" + + args.output_file_name 

	# logging
	logging.basicConfig(filename= _output_dir + "/gene-import-input-" + date.today().strftime("%b-%d-%Y") + ".log", encoding='utf-8', level=logging.DEBUG)

	# steps
	cleanup_entrez_id(_input_hgnc_file)
	remove_mirna()
	merge_type()
	merge_alias()
	translate_location()
	add_supp_main()
	add_supp_alias()
	add_supp_location()
	generate_output(_output_file_name)

if __name__ == '__main__':
	main()