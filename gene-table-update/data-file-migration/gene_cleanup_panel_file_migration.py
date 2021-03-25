import sys
import os
import argparse
import pandas as pd

def interface():
	parser = argparse.ArgumentParser(description='Script to update changes in hugo symbols in gene panel files.')
	parser.add_argument('-path', '--source_path', required=True, help='Path to the gene panel file.')
	output_mode = parser.add_mutually_exclusive_group()
	output_mode.add_argument('-o', '--override_file', required=False, action = 'store_true', help='Override the old panel file.')
	output_mode.add_argument('-n', '--create_new_file', required=False, action = 'store_true', help='Save to a new file without overriding the old file.')
	args = parser.parse_args()
	return args

def fetch_gene_info():
	print("\nFetching the reference gene and gene-alias info..\n")
	df = pd.read_csv('gene_info.txt', sep='\t', header=0, keep_default_na=False, dtype=str, low_memory=False)
	main_symbols = df['symbol'].unique().tolist()

	alias_symbols = set()
	for value in df['synonyms']:
		alias_symbols.update(value.split('|'))
	if '' in alias_symbols:
		alias_symbols.remove('')
	alias_symbols = list(alias_symbols)

	#Read the outdated to new hugo symbol mapping file (for cases where the file has only hugo symbol column)
	outdated_hugo_df = pd.read_csv('outdated_hugo_symbols.txt', sep='\t', header=0, dtype=str)
	outdated_hugo_dict = dict(zip(outdated_hugo_df['outdated_hugo_symbol'],outdated_hugo_df['new_hugo_symbol']))

	return main_symbols, alias_symbols, outdated_hugo_dict

def update_hugo_symbols(gene_symbols, main_symbol_list, alias_symbol_list, outdated_hugo_dict):
	updated_symbols = []
	log = ""
	for gene in gene_symbols:
		if gene in main_symbol_list:
			updated_symbols.append(gene)
		elif gene in alias_symbol_list:
			updated_symbols.append(gene)
			log += "WARNING: "+gene+" is an alias symbol\n"
		elif gene in outdated_hugo_dict:
			updated_symbols.append(outdated_hugo_dict[gene])
			log += gene+'\t\t---hugo symbol updated to---\t\t'+outdated_hugo_dict[gene]+'\n'
		else:
			updated_symbols.append(gene)
			log += "ERROR: "+gene+" symbol not known to the cBioPortal instance. This panel will not be loaded.\n"
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

	main_symbol_list,alias_symbol_list,outdated_hugo_dict = fetch_gene_info()
	
	panel_meta_data = ""
	gene_list = []
	with open(parsed_args.source_path,'r') as datafile:
		for line in datafile:
			if line.startswith('gene_list'):
				gene_symbols = line.split(':')[1].strip().split('\t')
				updated_symbols, log = update_hugo_symbols(gene_symbols, main_symbol_list,alias_symbol_list,outdated_hugo_dict)
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
