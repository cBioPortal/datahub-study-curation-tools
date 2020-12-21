import sys
import os
import pandas as pd

#PATH TO STUDIES AND HGNC TABLES - UPDATE TO CORRECT PATHS TO RUN THE SCRIPTS
dh_path = "/path/to/datahub/public/"
hgnc_gene_table_path = "/path/to/hgnc/final_main_table.txt"
hgnc_alias_table_path = "path/to/hgnc/final_alias_table.txt"
outdated_entrez_map_file = "Outdated_entrez_ID_mapping_final.txt"

main_table_df = pd.read_csv(hgnc_gene_table_path, comment='#', sep='\t', header=0, keep_default_na=False, dtype=str, low_memory=False)
alias_table_df = pd.read_csv(hgnc_alias_table_path, comment='#', sep='\t', header=0, keep_default_na=False, dtype=str, low_memory=False)
alias_table_df1 = alias_table_df.groupby(['entrez_id'],sort=False)['symbol'].unique().apply(list).reset_index()

main_table_entrez_dict = dict(zip(main_table_df['entrez_id'],main_table_df['symbol']))
alias_table_entrez_dict = dict(zip(alias_table_df1['entrez_id'],alias_table_df1['symbol']))

#Read the outdated to new entrez id mapping file (consolidated from all sub categories of the analysis)
outdated_entrez_df = pd.read_csv(outdated_entrez_map_file, sep='\t', header=0, keep_default_na=False, dtype=str)
outdated_entrez_dict = dict(zip(outdated_entrez_df['old_entrez_id'],outdated_entrez_df['updated_entrez_id']))

studies_list = os.listdir(dh_path)
if '.DS_Store' in studies_list: studies_list.remove('.DS_Store')
exluded_files_list = ['data_bcr_clinical_data_patient.txt','data_bcr_clinical_data_sample.txt','data_clinical_patient.txt','data_clinical_sample.txt','data_clinical_supp_hypoxia.txt','data_gene_matrix.txt','data_microbiome.txt','data_mutational_signature_confidence.txt','data_mutational_signature_contribution.txt','data_timeline_labtest.txt','data_timeline_procedure.txt','data_timeline_specimen.txt','data_timeline_status.txt','data_timeline_surgery.txt','data_timeline_treatment.txt','data_timeline.txt','data_subtypes.txt']

def entrez_gene(entrez_index, gene_index, fpath):
    with open(fpath,'r') as data_file:
        path = fpath.split('/')
        study_name,file_name = path[len(path)-2:]
        data = ""
        log = ""
        for line in data_file:
            if line.startswith('#') or line.startswith('Entrez_Gene_Id') or line.startswith('Hugo_Symbol'):
                data += line
            else:
                line = line.strip('\n').split('\t')
                hugo = line[gene_index]
                entrez = line[entrez_index]

                #If entrez id is in outdated list - update the entrez id to new entrez id.
                if entrez in outdated_entrez_dict:
                    log += hugo+'\t'+entrez+'\t\t---entrez id replaced to---\t\t'+hugo+'\t'+outdated_entrez_dict[entrez]+'\n'
                    line[entrez_index] = entrez = outdated_entrez_dict[entrez]

                #If entrez id is valid i.e, It is present in either main or alias hgnc tables.
                if entrez in main_table_entrez_dict or entrez in alias_table_entrez_dict:

                    #if entrez id is only in main table and the hugo symbol does not match to hgnc main, update the hugo symbol to hgnc main based on entrez id.
                    if entrez in main_table_entrez_dict and entrez not in alias_table_entrez_dict and hugo != main_table_entrez_dict[entrez]:
                        line[gene_index] = main_table_entrez_dict[entrez]
                        log += hugo+'\t'+entrez+'\t\t---hugo symbol updated to---\t\t'+line[gene_index]+'\t'+entrez+'\n'
                        data += '\t'.join(line)+'\n'

                    #If entrez id is only in alias table (25 cases) and the hugo symbol is not in hgnc alias, update the hugo symbol to hgnc alias based on entrez id.
                    #If the entrez id matches to exactly one alias, update the hugo symbol to alias
                    #If the entrez id matches to multiple alias symbols, how do we pick the symbol??????? - DO nothing as of now as the importer picks one during import.
                    elif entrez not in main_table_entrez_dict and entrez in alias_table_entrez_dict and hugo not in alias_table_entrez_dict[entrez]:
                        if len(alias_table_entrez_dict[entrez]) == 1:
                            line[gene_index] = alias_table_entrez_dict[entrez][0]
                            log += hugo+'\t'+entrez+'\t\t---hugo symbol updated to---\t\t'+alias_table_entrez_dict[entrez][0]+'\t'+entrez+'\n'
                            data += '\t'.join(line)+'\n'
                        else:
                            log += hugo+'\t'+entrez+'\t\t---ambiguos hugo symbol not updated in file---\t\t'+', '.join(alias_table_entrez_dict[entrez])+'\t'+entrez+'\n'
                            data += '\t'.join(line)+'\n'

                    #If entrez id is in both main and alias tables and the hugo symbol is not in either main or alias tables, update the hugo symbol to main symbol.
                    elif entrez in main_table_entrez_dict and entrez in alias_table_entrez_dict:
                        if hugo != main_table_entrez_dict[entrez] and hugo not in alias_table_entrez_dict[entrez]:
                            line[gene_index] = main_table_entrez_dict[entrez]
                            log += hugo+'\t'+entrez+'\t\t---hugo symbol updated to---\t\t'+main_table_entrez_dict[entrez]+'\t'+entrez+'\n'
                            data += '\t'.join(line)+'\n'
                        else:
                            data += '\t'.join(line)+'\n'

                    #If entrez in main or alias and the hugo in main or alias: DO nothing
                    else:
                        data += '\t'.join(line)+'\n'

                #If entrez id is invalid and if hugo symbol is NA, update the hugo symbol to empty cell.
                # If not the record gets mapped to wrong gene on import. NA is alias of gene 7504.
                else:
                    if hugo == "NA":
                        line[gene_index] = ""
                        log += hugo+'\t'+entrez+'\t\t---hugo symbol updated to empty---\t\t'+""+'\t'+entrez+'\n'
                        data += '\t'.join(line)+'\n'
                    else:
                        data += '\t'.join(line)+'\n'
        os.remove(fpath)
        with open(fpath,'w') as data_file:
            data_file.write(data)

        if log != "":
            log = "<--------------Changes made in file: "+file_name+" ------------------>\n"+log+'\n'
        return(log)

log_file = open('datahub_hgnc_updates_log.txt','w')

for study in studies_list:
    study_files = os.listdir(dh_path+'/'+study)
    final_log = ""
    for file_name in study_files:
        if file_name.startswith('data') and not file_name.endswith('.seg') and not file_name in exluded_files_list:
            file_path = dh_path+'/'+study+'/'+file_name
            with open(file_path,'r') as data_file:
                for line in data_file:
                    if line.startswith('Hugo_Symbol') or line.startswith('Entrez_Gene_Id'):
                        header_cols = list(map(lambda value: value.lower(),line.strip('\n').split('\t')))
                        if 'entrez_gene_id' in header_cols and 'hugo_symbol' in header_cols:
                            entrez_index = header_cols.index('entrez_gene_id')
                            gene_index = header_cols.index('hugo_symbol')
                            log = entrez_gene(entrez_index, gene_index, file_path)
                            final_log += log
                        break
    if final_log != "":
        log_file.write("<-------------------------------------"+study+"--------------------------------->\n\n")
        log_file.write(final_log)

print('log file written to '+os.getcwd()+'/datahub_hgnc_updates_log.txt')
