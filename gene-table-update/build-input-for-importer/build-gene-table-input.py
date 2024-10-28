import os
import sys
import argparse
import logging
import shutil
from datetime import date

# Custom HTML Formatter for Logging
class HTMLFormatter(logging.Formatter):
    def format(self, record):
        message = super().format(record)
        levelname = record.levelname
        
       
        if levelname == "DEBUG":
            if "Conflict" in message:
                levelname_color = "blue"
                message_color = "purple"
            else:
                levelname_color = "gray"
                message_color = "black"
        elif levelname == "INFO":
            levelname_color = "green"
            message_color = "black"
        elif levelname == "WARNING":
            levelname_color = "orange"
            message_color = "black"
        elif levelname == "ERROR":
            levelname_color = "red"
            message_color = "black"
        elif levelname == "CRITICAL":
            levelname_color = "darkred"
            message_color = "black"
        else:
            levelname_color = "black"
            message_color = "black"
        
        # HTML formatting of log message
        return f'<div style="color:{message_color};"><strong style="color:{levelname_color};">[{levelname}]</strong>: {message}</div>'

# Define paths for mappings and supplemental files
TYPE_MAPPING_PATH = "/Users/bsatravada/Desktop/tets_hgnc_build/build-input-for-importer/mappings/type-mapping.txt"
LOCATION_MAPPING_PATH = "/Users/bsatravada/Desktop/tets_hgnc_build/build-input-for-importer/mappings/location-mapping.txt"
MAIN_SUPP_PATH = "/Users/bsatravada/Desktop/tets_hgnc_build/build-input-for-importer/supp-files/main-supp/complete-supp-main.txt"
ALIAS_SUPP_PATH = "/Users/bsatravada/Desktop/tets_hgnc_build/build-input-for-importer/supp-files/alias-supp.txt"
ENTREZ_ID_SUPP_PATH = "/Users/bsatravada/Desktop/tets_hgnc_build/build-input-for-importer/supp-files/entrez-id-supp.txt"
LOCATION_SUPP_PATH = "/Users/bsatravada/Desktop/tets_hgnc_build/build-input-for-importer/supp-files/location-supp.txt"

gene_dict = {}

def setup_logger(log_file_path):
    """Sets up logger with custom HTML formatter."""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # File handler (HTML)
    html_handler = logging.FileHandler(log_file_path, mode='w')
    html_formatter = HTMLFormatter('%(message)s')
    html_handler.setFormatter(html_formatter)
    logger.addHandler(html_handler)

def cleanup_entrez_id(_input_file_name):
    logging.info("Checking resource: Entrez ID mapping")
    _entrez_id_dict = {}  # hugo_symbol as key
    with open(ENTREZ_ID_SUPP_PATH, "r") as _input_entrez_id_supp:
        _headers = _input_entrez_id_supp.readline()
        for line_number, _line in enumerate(_input_entrez_id_supp, start=2):
            _items = _line.rstrip("\r").rstrip("\n").split('\t')
            if len(_items) < 2:
                logging.warning(f"Skipping invalid line in Entrez ID mapping at line {line_number}: {_line}")
                continue
            _entrez_id_dict[_items[0]] = _items[1]

    _exiting_flag = 0
    logging.info("Cleaning up Entrez IDs")
    with open(_input_file_name, "r") as _input_hgnc:
        _headers = _input_hgnc.readline().rstrip('\n').rstrip('\r').split('\t')
        required_columns = ["entrez_id", "symbol", "hgnc_id", "locus_group", "locus_type", "location", "alias_symbol", "prev_symbol", "ensembl_gene_id"]
        for column in required_columns:
            if column not in _headers:
                logging.error(f"Missing expected column '{column}' in HGNC file")
                sys.exit(f"Error: Missing expected column '{column}' in HGNC file")
        
        for line_number, _line in enumerate(_input_hgnc, start=2):
            _items = _line.rstrip("\r").rstrip("\n").split('\t')
            if len(_items) < len(_headers):
                logging.warning(f"Skipping invalid line in HGNC file at line {line_number}: {_line}")
                continue
            
            _entrez_id = _items[_headers.index("entrez_id")]
            _hugo_symbol = _items[_headers.index("symbol")]

            if _entrez_id == "":
                if _hugo_symbol in _entrez_id_dict:
                    if _entrez_id_dict[_hugo_symbol] == "R":
                        logging.info(f"Deleted entry: {_hugo_symbol}")
                        continue
                    else:
                        logging.info(f"Added entrez ID {_entrez_id_dict[_hugo_symbol]} to: {_hugo_symbol}")
                        _entrez_id = _entrez_id_dict[_hugo_symbol]
                else:
                    logging.error(f"Assign entrez ID to (OR delete) : {_hugo_symbol}")
                    _exiting_flag = 1

            if _entrez_id in gene_dict:
                logging.info(f"Merge {_hugo_symbol} into {gene_dict[_entrez_id]['symbol']} as previous symbol.")
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

    if _exiting_flag == 1:
        logging.error(f"Please assign entrez ID to error entries and check {ENTREZ_ID_SUPP_PATH}")
    else:
        logging.info("Finished cleaning up Entrez IDs")
    return _exiting_flag

# Removes all entries with locus_type value as RNA, micro
def remove_mirna():
    logging.info("Removing miRNA entries")
    for _key in list(gene_dict.keys()):
        _gene_obj = gene_dict[_key]
        if _gene_obj["locus_type"] == "RNA, micro":
            del gene_dict[_key]
    logging.info("Finished removing miRNA entries")


# Merge values locus_group and locus_type into one column type
def merge_type():
    logging.info("Checking resource: Gene Types mapping >>>>>>>>>>>>>>>")
    _type_mapping_dict = {}  # "locus_group | locus_type" combination is entrez id
    with open(TYPE_MAPPING_PATH, "r") as _input_type_mapping:
        _headers = _input_type_mapping.readline()
        for _line in _input_type_mapping:
            _items = _line.rstrip("\r").rstrip("\n").split('\t')    
            _type_mapping_dict[_items[0] + "|" + _items[1]] = _items[2]
    
    logging.info("Merging Gene Types >>>>>>>>>>>>>>>")
    for _key in gene_dict.keys():
        _gene_obj = gene_dict[_key]
        _type_key = _gene_obj["locus_group"] + "|" + _gene_obj["locus_type"]
        _gene_obj["type"] = _type_mapping_dict.get(_type_key, "")
    logging.info("Finished merging gene types ....\n")

# Merging values in alias_symbol and prev_symbol into one column synonyms
def merge_alias():
    _unavailable_symbols_for_alias = {}

    # Dictionary to track alias and previous symbol conflicts
    alias_conflicts = {}

    # Step 1: Track all main symbols so they are not added to synonyms
    for _gene_obj in gene_dict.values():
        _unavailable_symbols_for_alias[_gene_obj["symbol"]] = ""

    logging.info("Merging Previous Symbols >>>>>>>>>>>>>>>")
    # Step 2: Process previous symbols first and give them priority over alias symbols
    for _gene_obj in gene_dict.values():
        _prev_symbols = _gene_obj["prev_symbol"].split("|")
        initial_synonyms = _gene_obj["synonyms"]
        
        for _prev_symbol in _prev_symbols:
            _prev_symbol = _prev_symbol.strip()  # Remove any extra spaces
            if _prev_symbol != "":
                # If the symbol is a main symbol, skip adding it to synonyms
                if _prev_symbol in _unavailable_symbols_for_alias:
                    # Track conflicts and log all genes involved
                    if _prev_symbol not in alias_conflicts:
                        alias_conflicts[_prev_symbol] = [gene_dict[_gene_obj["entrez_id"]]["symbol"]]
                    if _gene_obj["symbol"] not in alias_conflicts[_prev_symbol]:
                        alias_conflicts[_prev_symbol].append(_gene_obj["symbol"])
                    # Improved conflict logging with the list of conflicting genes
                    conflicting_genes = ", ".join(alias_conflicts[_prev_symbol])
                    logging.debug(f"Conflict detected for prev_symbol {_prev_symbol} used in multiple genes: {conflicting_genes}")
                else:
                    # Mark it unavailable for alias and add to synonyms
                    _unavailable_symbols_for_alias[_prev_symbol] = ""
                    if _gene_obj["synonyms"].strip() == "":
                        _gene_obj["synonyms"] = _prev_symbol
                    else:
                        _gene_obj["synonyms"] += "|" + _prev_symbol

        # Log only if synonyms were actually updated
        if _gene_obj["synonyms"] != initial_synonyms:
            logging.debug(f"Updated synonyms for {_gene_obj['symbol']} (after prev_symbol): {_gene_obj['synonyms']}")

    logging.info("Merging Alias Symbols >>>>>>>>>>>>>>>")
    # Step 3: Process alias symbols and add them only if they are not main symbols or previous symbols
    for _gene_obj in gene_dict.values():
        _alias_symbols = _gene_obj["alias_symbol"].split("|")
        initial_synonyms = _gene_obj["synonyms"]  

        for _alias_symbol in _alias_symbols:
            _alias_symbol = _alias_symbol.strip()  # Remove any extra spaces
            if _alias_symbol != "":
                # Skip adding the alias if it is a main symbol or already used as a previous symbol
                if _alias_symbol in _unavailable_symbols_for_alias:
                    # Track conflicts and log all genes involved
                    if _alias_symbol not in alias_conflicts:
                        alias_conflicts[_alias_symbol] = [gene_dict[_gene_obj["entrez_id"]]["symbol"]]
                    if _gene_obj["symbol"] not in alias_conflicts[_alias_symbol]:
                        alias_conflicts[_alias_symbol].append(_gene_obj["symbol"])
                    # Improved conflict logging with the list of conflicting genes
                    conflicting_genes = ", ".join(alias_conflicts[_alias_symbol])
                    logging.debug(f"Conflict detected for alias_symbol {_alias_symbol} used in multiple genes: {conflicting_genes}")
                else:
                    # Mark it unavailable for alias and add to synonyms
                    _unavailable_symbols_for_alias[_alias_symbol] = ""
                    if _gene_obj["synonyms"].strip() == "":
                        _gene_obj["synonyms"] = _alias_symbol
                    else:
                        _gene_obj["synonyms"] += "|" + _alias_symbol

        # Log only if synonyms were actually updated
        if _gene_obj["synonyms"] != initial_synonyms:
            logging.debug(f"Updated synonyms for {_gene_obj['symbol']} (after alias_symbol): {_gene_obj['synonyms']}")

    logging.info("Finished Merging Alias .....\n")

    # Return conflicts for further analysis or logging
    return alias_conflicts

# Translate the location column into two chromosome and cytoband
def translate_location():
    logging.info("Checking resource: Locations mapping >>>>>>>>>>>>>>>")
    _location_mapping_dict = {}  # hgnc location vocabulary as key
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
        if _gene_obj["location"] in _location_mapping_dict:
            _gene_obj["chromosome"] = _location_mapping_dict[_gene_obj["location"]]["chr"]
            _gene_obj["cytoband"] = _location_mapping_dict[_gene_obj["location"]]["cytoband"]
        else: 
            # Parsing standard format (e.g. 19q13.12, 4q31.21-q31.22)
            for _index in range(len(_gene_obj["location"])):
                if _gene_obj["location"][_index] in ["q", "p"]:
                    _gene_obj["chromosome"] = _gene_obj["location"].split(_gene_obj["location"][_index])[0]
                    if "not on reference assembly" in _gene_obj["location"]:
                        _gene_obj["cytoband"] = _gene_obj["location"].replace(" not on reference assembly", "")
                    else:
                        _gene_obj["cytoband"] = _gene_obj["location"]
                    break
        
    logging.info("Finished translating HGNC location >>>>>>>>>>>>>\n")

# Concatenate gene entries main-supp.txt
def add_supp_main():
    logging.info("Adding main supplement genes >>>>>>>>>>>>>")
    with open(MAIN_SUPP_PATH, "r") as _input_main_supp:
        _headers = _input_main_supp.readline()
        _exiting_flag = 0
        for _line in _input_main_supp:
            _items = _line.rstrip("\r").rstrip("\n").split('\t')    
            if _items[0] in gene_dict:
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

    # If a supplement gene's entrez ID already exists in HGNC, system would exit
    if _exiting_flag == 1:
        logging.info("Exiting.....")
        logging.info("Please fix the entries with duplicate entrez IDs listed as errors above, under " + MAIN_SUPP_PATH)
        # Note: Do not exit here to ensure ambiguities are checked and file is generated

# Merge the supplemental alias list alias-supp.txt
def add_supp_alias():
    logging.info("Adding alias supplement genes >>>>>>>>>>>>>")

    _alias_items = {}  # key is entrez id
    with open(ALIAS_SUPP_PATH, "r") as _input_alias_supp:
        _header = _input_alias_supp.readline()
        for _line in _input_alias_supp:
            _items = _line.rstrip("\r").rstrip("\n").split('\t')
            _alias_items[_items[0]] = _items[1]
    _input_alias_supp.close()

    for _key in _alias_items.keys():
        if _key in gene_dict: 
            if gene_dict[_key]["synonyms"] == "":
                gene_dict[_key]["synonyms"] = _alias_items[_key]
            else:
                gene_dict[_key]["synonyms"] = gene_dict[_key]["synonyms"] + "|" + _alias_items[_key]
        else:  # with HGNC update, some entrez ID may become unavailable
            logging.warning(_key + "\t" + _alias_items[_key] + " entry is skipped - entrez ID does not exist in main table")
            logging.warning("Please remove entry: " + _key + "\t" + _alias_items[_key])

    logging.info("Finished adding alias supplement genes >>>>>>>>>>>>>\n")

# Merge the supplemental location list location-supp.txt
def add_supp_location():
    logging.info("Adding supplemental location info >>>>>>>>>>>>>")

    _location_supp_items = {}  # key is entrez id
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
        if _key in gene_dict: 
            if gene_dict[_key]["chromosome"] != "-" and gene_dict[_key]["cytoband"] != "-":
                logging.warning(_key + "\t" + _location_supp_items[_key]["symbol"] + " entry already has location info.")
                logging.warning("Please remove entry: " + _key + "\t" + _location_supp_items[_key]["symbol"])
            if gene_dict[_key]["chromosome"] == "-":
                gene_dict[_key]["chromosome"] = _location_supp_items[_key]["chr"]
            if gene_dict[_key]["cytoband"] == "-":
                gene_dict[_key]["cytoband"] = _location_supp_items[_key]["cytoband"]
        else:  # with HGNC update, some entrez ID may become unavailable
            logging.warning(_key + "\t" + _location_supp_items[_key]["symbol"] + " entry is skipped - entrez ID does not exist in main table")
            logging.warning("Please remove entry: " + _key + "\t" + _location_supp_items[_key]["symbol"])

    logging.info("Finished adding alias supplement genes >>>>>>>>>>>>>\n")

def generate_output(_output_file_name):
    with open(_output_file_name, "w") as _output_file:
        _output_file.write("entrez_id\tsymbol\tchromosome\tcytoband\ttype\tsynonyms\thgnc_id\tensembl_id\n")
        missing_chromosome_entries = []  # List to track entries where chromosome is "-"
        
        for _gene_obj in gene_dict.values():
            # Write the gene entry to the output file
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
            
            # Check if the chromosome value is "-"
            if _gene_obj["chromosome"] == "-":
                missing_chromosome_entries.append({
                    'entrez_id': _gene_obj["entrez_id"],
                    'symbol': _gene_obj["symbol"],
                    'locus_group': _gene_obj["locus_group"]
                })
    
    # Log entries where chromosome is "-"
    if missing_chromosome_entries:
        logging.info("\n--- Genes with missing chromosome information ---\n")
        for entry in missing_chromosome_entries:
            logging.warning(
                f"Missing chromosome info for Gene: {entry['symbol']} "
                f"(Entrez ID: {entry['entrez_id']}, Type: {entry['locus_group']})"
            )
    else:
        logging.info("All genes have valid chromosome information.\n")


# Function to log ambiguities 
def check_ambiguities(alias_conflicts):
    # Check for genes with multiple Entrez IDs
    symbol_to_entrez = {}
    for _gene_obj in gene_dict.values():
        symbol = _gene_obj["symbol"]
        entrez_id = _gene_obj["entrez_id"]
        if symbol in symbol_to_entrez:
            symbol_to_entrez[symbol].append(entrez_id)
        else:
            symbol_to_entrez[symbol] = [entrez_id]

    for symbol, entrez_ids in symbol_to_entrez.items():
        if len(entrez_ids) > 1:
            message = f"Ambiguity: Gene '{symbol}' has multiple Entrez IDs assigned: {', '.join(entrez_ids)}"
            logging.warning(message)

    # Check for Entrez IDs with multiple gene symbols
    entrez_to_symbol = {}
    for _gene_obj in gene_dict.values():
        symbol = _gene_obj["symbol"]
        entrez_id = _gene_obj["entrez_id"]
        if entrez_id in entrez_to_symbol:
            entrez_to_symbol[entrez_id].append(symbol)
        else:
            entrez_to_symbol[entrez_id] = [symbol]

    for entrez_id, symbols in entrez_to_symbol.items():
        if len(symbols) > 1:
            message = f"Ambiguity: Entrez ID '{entrez_id}' has multiple gene symbols assigned: {', '.join(symbols)}"
            logging.warning(message)

    # Log alias and previous symbol conflicts
    for alias, symbols in alias_conflicts.items():
        if len(symbols) > 1:
            message = f"Conflict: '{alias}' is listed as a synonym for multiple genes: {', '.join(symbols)}"
            logging.warning(message)

# List to track entries where chromosome is "-"
def generate_output(_output_file_name):
    with open(_output_file_name, "w") as _output_file:
        _output_file.write("entrez_id\tsymbol\tchromosome\tcytoband\ttype\tsynonyms\thgnc_id\tensembl_id\n")
        missing_chromosome_entries = [] 

        for _gene_obj in gene_dict.values():
            # Write the gene entry to the output file
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

            # Check if the chromosome value is "-"
            if _gene_obj["chromosome"] == "-":
                logging.warning(f"Missing chromosome info for Gene: {_gene_obj['symbol']} (Entrez ID: {_gene_obj['entrez_id']}, Location: {_gene_obj['location']})")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-hgnc-file', action='store', dest='input_hgnc_file', required=True, help='(Required) Downloaded HGNC file')
    parser.add_argument('-o', '--output-file-name', action='store', dest='output_file_name', required=False, help='(Optional) Name of the output file')
    args = parser.parse_args()

    _input_hgnc_file = args.input_hgnc_file

    # Create output directory
    _output_dir = date.today().strftime("%b-%d-%Y") + "-output"
    if os.path.exists(_output_dir):
        shutil.rmtree(_output_dir)
    os.makedirs(_output_dir)

    # Define file paths
    _output_file_name = _output_dir + "/" + (args.output_file_name or f"gene-info-{date.today().strftime('%b-%d-%Y')}.txt")
    log_file_path = _output_dir + "/gene-import-log-{date.today().strftime('%b-%d-%Y')}.html"

    # Set up logger with HTML output
    setup_logger(log_file_path)

    logging.info("Process started...")

    # Steps
    exiting_flag = cleanup_entrez_id(_input_hgnc_file)
    remove_mirna()
    merge_type()
    alias_conflicts = merge_alias()
    translate_location()
    add_supp_main()
    add_supp_alias()
    add_supp_location()

    check_ambiguities(alias_conflicts)

    # Generate output if no critical errors
    if exiting_flag == 0:
        generate_output(_output_file_name)
        logging.info("Process completed successfully.")
    else:
        logging.error("Process encountered issues. Check the log file for details.")

    print(f"Process completed. Check the output folder for results.")

if __name__ == '__main__':
    main()