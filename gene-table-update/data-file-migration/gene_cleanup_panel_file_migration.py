import sys
import os
import argparse
import pandas as pd

# This script only updates the outdates gene symbols to new symbols. The comparison of gene symbols to database is done during the import of the panels to database.

def interface():
	parser = argparse.ArgumentParser(description='Script to update changes in hugo symbols in gene panel files.')
	parser.add_argument('-path', '--source_path', required=True, help='Path to the gene panel file.')
	output_mode = parser.add_mutually_exclusive_group()
	output_mode.add_argument('-o', '--override_file', required=False, action = 'store_true', help='Override the old panel file.')
	output_mode.add_argument('-n', '--create_new_file', required=False, action = 'store_true', help='Save to a new file without overriding the old file.')
	args = parser.parse_args()
	return args

def update_hugo_symbols(gene_symbols, outdated_hugo_dict):
	updated_symbols = []
	log = ""
	for gene in gene_symbols:
		if gene.upper() in outdated_hugo_dict:
			updated_symbols.append(outdated_hugo_dict[gene.upper()])
			log += gene+'\t\t---hugo symbol updated to---\t\t'+outdated_hugo_dict[gene.upper()]+'\n'
		else:
			updated_symbols.append(gene)
	return updated_symbols, log

def update_datafile_mode(override_file, create_new_file, updated_data, data_file):
	if parsed_args.override_file:
		os.remove(parsed_args.source_path)
		with open(parsed_args.source_path,'w') as outfile:
			outfile.write(updated_data)
		print("Overwritten file with updates: "+data_file)
	elif create_new_file:
		new_filename = data_file.replace('.txt','_updated.txt')
		with open(new_filename,'w') as outfile:
			outfile.write(updated_data)
		print("Created new file with updates: "+new_filename)

def main(parsed_args):
	if not any((parsed_args.override_file, parsed_args.create_new_file)):
		parsed_args.create_new_file = True
		
	if not os.path.exists(parsed_args.source_path):
		print("ERROR: Invalid path or file '"+parsed_args.source_path+"'")
		sys.exit(1)

	#main_symbol_list,alias_symbol_list,outdated_hugo_dict = fetch_gene_info()
	
	panel_meta_data = ""
	gene_list = []
	with open(parsed_args.source_path,'r') as datafile:
		for line in datafile:
			if line.startswith('gene_list'):
				gene_symbols = line.split(':')[1].strip().split('\t')
				updated_symbols, log = update_hugo_symbols(gene_symbols, outdated_hugo_dict)
				if log != "":
					print("<----------------------- Processing file: "+parsed_args.source_path+" ---------------------------------->\n")
					print(log+'\n')
				if gene_symbols == updated_symbols:
					print("No updates to file "+parsed_args.source_path+'\n')
				else:
					updated_data = panel_meta_data+"gene_list: "+'\t'.join(updated_symbols)+"\n"
					update_datafile_mode(parsed_args.override_file, parsed_args.create_new_file, updated_data, parsed_args.source_path)
			else:
				panel_meta_data += line

if __name__ == '__main__':
	parsed_args = interface()
	main(parsed_args)
