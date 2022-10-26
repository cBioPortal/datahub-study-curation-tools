import sys
import os
import argparse
import pandas as pd

#---Read gene, gene-alias tables and outdated to new entrez id mappings--->
#---Currently reading from a file. This logic will be replaced to read the gene/alias data from cbioportal API once the new gene tables become available--->
print("\nFetching the reference gene and gene-alias info..\n")
df = pd.read_csv('gene_info.txt', sep='\t', header=0, keep_default_na=False, dtype=str, low_memory=False)
main_table_entrez_dict = dict(zip(df['entrez_id'],df['symbol']))
alias_table_entrez_dict = dict(zip(df['entrez_id'],df['synonyms'].str.split("|", n=-1, expand=False)))

keys_with_no_synonyms = []
for key in alias_table_entrez_dict:
	if len(alias_table_entrez_dict[key]) == 1 and alias_table_entrez_dict[key][0] == '':
		keys_with_no_synonyms.append(key)
for key in keys_with_no_synonyms:
	del alias_table_entrez_dict[key]

#Read the outdated to new entrez id mapping file (consolidated from all sub categories of the analysis)
outdated_entrez_df = pd.read_csv('outdated_entrez_ids.txt', sep='\t', header=0, keep_default_na=False, dtype=str)
outdated_entrez_dict = dict(zip(outdated_entrez_df['old_entrez_id'],outdated_entrez_df['updated_entrez_id']))
	
#Read the outdated to new hugo symbol mapping file (for cases where the file has only hugo symbol column)
outdated_hugo_df = pd.read_csv('outdated_hugo_symbols.txt', sep='\t', header=0, dtype=str)
outdated_hugo_dict = dict(zip(outdated_hugo_df['outdated_hugo_symbol'],outdated_hugo_df['new_hugo_symbol']))

def interface():
	parser = argparse.ArgumentParser(description='Script to propagate changes in hugo symbols and entrez gene ids in data files.')
	parser.add_argument('-path', '--source_path', required=True, help='Path to the data file or directory that needs to be migrated.')
	output_mode = parser.add_mutually_exclusive_group()
	output_mode.add_argument('-l', '--stdout_log', required=False, action = 'store_true', help='Dry-run the script. Preview the changes that will be made to the files.')
	output_mode.add_argument('-o', '--override_file', required=False, action = 'store_true', help='Override the old data files.')
	output_mode.add_argument('-n', '--create_new_file', required=False, action = 'store_true', help='Save the migrated data to new file without overriding the old files.')
	args = parser.parse_args()
	return args

#---Check the input type (file/directory) and get the list of files (1 or many)--->
def check_path(source_path):
	files_list = []
	exluded_files_list = ['data_bcr_clinical_data_patient.txt','data_bcr_clinical_data_sample.txt','data_clinical_patient.txt','data_clinical_sample.txt','data_clinical_supp_hypoxia.txt','data_gene_matrix.txt','data_microbiome.txt','data_mutational_signature_confidence.txt','data_mutational_signature_contribution.txt','data_timeline_labtest.txt','data_timeline_procedure.txt','data_timeline_specimen.txt','data_timeline_status.txt','data_timeline_surgery.txt','data_timeline_treatment.txt','data_timeline.txt','data_subtypes.txt']
	
	if os.path.exists(source_path):
		if os.path.isdir(source_path):
			for data_file in os.listdir(source_path):
				if not data_file.startswith('.') and not data_file.endswith('.gz') and os.path.isfile(os.path.join(source_path,data_file)) and not data_file.endswith('.seg') and not data_file in exluded_files_list: files_list.append(os.path.join(source_path,data_file))
		elif os.path.isfile(source_path) and not data_file.endswith('.gz') and not source_path.endswith('.seg') and not os.path.basename(source_path) in exluded_files_list:
			files_list.append(source_path)
		return files_list
	else:
		print("ERROR: Invalid path or file '"+source_path+"'")
		sys.exit(1)

#---If the file has both hugo_symbol and entrez_id columns, update outdated entrez ids first and then update the invalid hugo symbols based on entrez ids--->	
def update_hugo_symbols(entrez_index, gene_index, data, log):
	entrez = data[entrez_index]
	hugo = data[gene_index]
	
	#If entrez id is in outdated list - update the entrez id to new entrez id.
	if entrez in outdated_entrez_dict:
		log += entrez+'\t\t---entrez id replaced to---\t\t'+outdated_entrez_dict[entrez]+'\n'
		entrez = outdated_entrez_dict[entrez]
		
	#If entrez id is valid i.e, It is present in either main or alias tables.
	if entrez in main_table_entrez_dict or entrez in alias_table_entrez_dict:
		#If entrez id is only in the gene table, and the hugo symbol in data file does not correspond to the symbol in the gene table for the given entrez id, update the symbol in data file to the symbol from gene table based on the entrez id.
		if entrez in main_table_entrez_dict and entrez not in alias_table_entrez_dict and hugo != main_table_entrez_dict[entrez]:
			log += hugo+'\t'+entrez+'\t\t---hugo symbol updated to---\t\t'+main_table_entrez_dict[entrez]+'\t'+entrez+'\n'
			hugo = main_table_entrez_dict[entrez]
			
		#If entrez id is only in alias table and the hugo symbol is not in gene-alias, update the hugo symbol to gene-alias based on entrez id.
		#If the entrez id matches to exactly one alias, update the hugo symbol to alias
		#If the entrez id matches to multiple alias symbols, how do we pick the symbol??????? - DO nothing as of now as the importer picks one during import.
		elif entrez not in main_table_entrez_dict and entrez in alias_table_entrez_dict and hugo not in alias_table_entrez_dict[entrez]:
			if len(alias_table_entrez_dict[entrez]) == 1:
				log += hugo+'\t'+entrez+'\t\t---hugo symbol updated to---\t\t'+alias_table_entrez_dict[entrez][0]+'\t'+entrez+'\n'
				hugo = alias_table_entrez_dict[entrez][0]
			else:
				log += hugo+'\t'+entrez+'\t\t---ambiguous hugo symbol not updated in file---\t\t'+', '.join(alias_table_entrez_dict[entrez])+'\t'+entrez+'\n'

		#If entrez id is in both main and alias tables and the hugo symbol is not in either main or alias tables, update the hugo symbol to main symbol.
		elif entrez in main_table_entrez_dict and entrez in alias_table_entrez_dict:
			if hugo != main_table_entrez_dict[entrez] and hugo not in alias_table_entrez_dict[entrez]:
				log += hugo+'\t'+entrez+'\t\t---hugo symbol updated to---\t\t'+main_table_entrez_dict[entrez]+'\t'+entrez+'\n'
				hugo = main_table_entrez_dict[entrez]

	#If entrez id is invalid and if hugo symbol is NA, update the hugo symbol to empty cell.
	# If not the record gets mapped to wrong gene on import. NA is alias of gene 7504.
	else:
		if hugo == "NA":
			log += hugo+'\t'+entrez+'\t\t---hugo symbol updated to empty---\t\t'+""+'\t'+entrez+'\n'
			hugo = ""
		elif hugo in outdated_hugo_dict:
			log += hugo+'\t'+entrez+'\t\t---hugo symbol updated to---\t\t'+outdated_hugo_dict[hugo]+'\t'+entrez+'\n'
			hugo = outdated_hugo_dict[hugo]
			
	return entrez,hugo,log

#---If the file has only entrez id and no hugo symbol, check for outdated entrez ids & update--->	
def update_outdated_entrezids(entrez_index, data, log):
		entrez = data[entrez_index]
		if entrez in outdated_entrez_dict:
			log += entrez+'\t\t---entrez id replaced to---\t\t'+outdated_entrez_dict[entrez]+'\n'
			entrez = outdated_entrez_dict[entrez]

		return entrez,log
		
#---If the file has only hugo_symbol column, update the symbol if outdated. The outdated list is pre-defined from our analysis--->
def update_outdated_hugo_symbols(gene_index, data, log):
	hugo = data[gene_index]
	if hugo in outdated_hugo_dict:
		log += hugo+'\t\t---hugo symbol replaced to---\t\t'+outdated_hugo_dict[hugo]+'\n'
		hugo = outdated_hugo_dict[hugo]

	return hugo,log


def update_genes(entrez1_index, entrez2_index, gene1_index, gene2_index, event_info_index, line):
	log = ""
	if gene1_index != -1: gene1_infile = line[gene1_index]
	if gene2_index != -1: gene2_infile = line[gene2_index]

	#---If both Hugo symbol and entrez id in file, first update the outdated entrez ids and then hugo symbols--->
	if entrez1_index != -1 and gene1_index != -1:
		entrez,gene,log = update_hugo_symbols(entrez1_index, gene1_index, line, log)
		if line[entrez1_index] != entrez: line[entrez1_index] = entrez
		if line[gene1_index] != gene: line[gene1_index] = gene
		if event_info_index != -1 and gene1_infile in line[event_info_index]:
			line[event_info_index] = line[event_info_index].replace(gene1_infile, gene)
	if entrez2_index != -1 and gene2_index != -1:
		entrez,gene,log = update_hugo_symbols(entrez2_index, gene2_index, line, log)
		if line[entrez2_index] != entrez: line[entrez2_index] = entrez
		if line[gene2_index] != gene: line[gene2_index] = gene
		if event_info_index != -1 and gene2_infile in line[event_info_index]:
			line[event_info_index] = line[event_info_index].replace(gene2_infile, gene)

	#---If only entrez id in file, check for outdated entrez ids & update--->
	if entrez1_index != -1 and gene1_index == -1:
		entrez,log = update_outdated_entrezids(entrez1_index, line, log)
		if line[entrez1_index] != entrez: line[entrez1_index] = entrez
	if entrez2_index != -1 and gene2_index == -1:
		entrez,log = update_outdated_entrezids(entrez2_index, line, log)
		if line[entrez2_index] != entrez: line[entrez2_index] = entrez
		
	#---If only hugo symbol in file, check for outdated hugo symbols & update--->
	if entrez1_index == -1 and gene1_index != -1:
		gene,log = update_outdated_hugo_symbols(gene1_index, line, log)
		if line[gene1_index] != gene: line[gene1_index] = gene
		if event_info_index != -1 and gene1_infile in line[event_info_index]:
			line[event_info_index] = line[event_info_index].replace(gene1_infile, gene)
	if entrez2_index == -1 and gene2_index != -1:
		gene,log = update_outdated_hugo_symbols(gene2_index, line, log)
		if line[gene2_index] != gene: line[gene2_index] = gene
		if event_info_index != -1 and gene2_infile in line[event_info_index]:
			line[event_info_index] = line[event_info_index].replace(gene2_infile, gene)
	
	return line, log
	
#---based on the output mode passed by the user, either overwrite the file or create new file with _updated suffix--->		
def update_datafile_mode(override_file, create_new_file, updated_data, data_file):
	if override_file:
		os.remove(data_file)
		with open(data_file,'w') as outfile:
			outfile.write(updated_data)
		print("Overwritten file with updates: "+data_file)
	elif create_new_file:
		new_filename = data_file.replace('.txt','_updated.txt')
		with open(new_filename,'w') as outfile:
			outfile.write(updated_data)
		print("Created new file with updates: "+new_filename)
	
def main(parsed_args):
	#---default the output mode to dry-run when none of the -l, -o or -n options are passed--->
	if not any((parsed_args.stdout_log, parsed_args.override_file, parsed_args.create_new_file)):
		parsed_args.stdout_log = True

	#---The user can pass either a file or a directory as an input. Check the input type (file/directory) and get the list of files--->
	files_list = check_path(parsed_args.source_path)
	
	if len(files_list) == 0:
		print("The source directory has no valid data files to process.")
		sys.exit(1)
	
	#print("The file(s) to process are:")
	#for data_file in files_list: print(data_file)
	
	data_log = ""
	for data_file in files_list:
		with open(data_file,'r') as datafile:
			updated_data = ""
			log = ""
			entrez1_index = -1
			entrez2_index = -1
			gene1_index = -1
			gene2_index = -1
			event_info_index = -1
			for line in datafile:
				if line.startswith('#'):
					updated_data += line
				elif line.startswith('Entrez_Gene_Id') or line.startswith('Hugo_Symbol'):
					updated_data += line
					header_cols = line.strip('\n').split('\t')
					try: entrez1_index = header_cols.index('Entrez_Gene_Id')
					except: pass
					try: gene1_index = header_cols.index('Hugo_Symbol')
					except: pass					
				elif line.startswith('Sample_Id'):
					updated_data += line
					header_cols = line.strip('\n').split('\t')
					try: entrez1_index = header_cols.index('Site1_Entrez_Gene_Id')
					except: pass
					try: gene1_index = header_cols.index('Site1_Hugo_Symbol')
					except: pass	
					try: entrez2_index = header_cols.index('Site2_Entrez_Gene_Id')
					except: pass
					try: gene2_index = header_cols.index('Site2_Hugo_Symbol')
					except: pass
					try: event_info_index = header_cols.index('Event_Info')
					except: pass
				else:
					line = line.strip('\n').split('\t')
					line,log_msg = update_genes(entrez1_index, entrez2_index, gene1_index, gene2_index, event_info_index, line)
					log += log_msg
					updated_data += '\t'.join(line)+'\n'
	
			if log != "":
				data_log += "\n\n<-------------------------------------"+data_file+"--------------------------------->\n\n"
				data_log += log
				update_datafile_mode(parsed_args.override_file, parsed_args.create_new_file, updated_data, data_file)
	
	if data_log != "" and parsed_args.stdout_log:
		print('\n\nThe following are the changes that will be made to the data file(s):\n\n')
		print(data_log)
	elif data_log != "":
		with open('data_file_updates.log','a') as out_file:
			out_file.write(data_log)
			print('\nThe log of changes is written to file : '+os.path.abspath('data_file_updates.log')+'\n')

if __name__ == '__main__':
	parsed_args = interface()
	main(parsed_args)
