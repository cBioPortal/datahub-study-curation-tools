import sys
import os
import pandas as pd

#--------------------Script to read data files and update the invalid entrez ids to the ids corresponding to the hugo symbol----------------#
#LOGIC:
#1. If the given entrez id is invalid (not seen in main or alias tables), fall back on hugo symbol for assigning correct entrez id.
#2. If hugo symbol in main table and not in alias table, assign the new entrez id to main table entrez id. (no duplicate entrez ids in main table)
#3. If hugo symbol not in main table and in alias table, count the number of entrez ids available for the given hugo symbol.
#               - If multiple entrez ids. Its a ambiguos case. How to pick the id ?????
#               - If only one entrez id, assign the entrez id to symbol.

dh_path = "/path/to/datahub/public/" #Update the path
hgnc_gene_table_path = "/path/to/hgnc/final_main_table.txt"
hgnc_alias_table_path = "path/to/hgnc/final_alias_table.txt"

df = pd.read_csv(hgnc_gene_table_path, comment='#', sep='\t', header=0, keep_default_na=False, dtype=str, low_memory=False)
main_table_entrez_dict = dict(zip(df['entrez_id'],df['symbol']))
main_table_hugo_dict = dict(zip(df['symbol'],df['entrez_id']))

df1 = pd.read_csv(hgnc_alias_table_path, comment='#', sep='\t', header=0, keep_default_na=False, dtype=str, low_memory=False)
df2 = df1.groupby(['entrez_id'],sort=False)['symbol'].unique().apply(list).reset_index()
alias_table_entrez_dict = dict(zip(df2['entrez_id'],df2['symbol']))
df3 = df1.groupby(['symbol'],sort=False)['entrez_id'].unique().apply(list).reset_index()
alias_table_hugo_dict = dict(zip(df3['symbol'],df3['entrez_id']))

studies_list = os.listdir(dh_path)
if '.DS_Store' in studies_list: studies_list.remove('.DS_Store')
exluded_files_list = ['data_bcr_clinical_data_patient.txt','data_bcr_clinical_data_sample.txt','data_clinical_patient.txt','data_clinical_sample.txt','data_clinical_supp_hypoxia.txt','data_gene_matrix.txt','data_microbiome.txt','data_mutational_signature_confidence.txt','data_mutational_signature_contribution.txt','data_timeline_labtest.txt','data_timeline_procedure.txt','data_timeline_specimen.txt','data_timeline_status.txt','data_timeline_surgery.txt','data_timeline_treatment.txt','data_timeline.txt','data_subtypes.txt']

def entrez_gene(entrez_index, gene_index, fpath):
    with open(fpath,'r') as data_file:
        data = ""
        for line in data_file:
            if line.startswith('#') or line.startswith('Entrez_Gene_Id') or line.startswith('Hugo_Symbol'):
                data += line
            else:
                line = line.strip('\n').split('\t')
                hugo = line[gene_index]
                entrez = line[entrez_index]
                if entrez not in main_table_entrez_dict and entrez not in alias_table_entrez_dict:
                    if hugo in main_table_hugo_dict and hugo not in alias_table_hugo_dict:
                        line[entrez_index] = main_table_hugo_dict[hugo]
                        data += '\t'.join(line)+'\n'
                    elif hugo not in main_table_hugo_dict and hugo in alias_table_hugo_dict:
                        if len(alias_table_hugo_dict[hugo]) > 1:
                            #line[entrez_index] = "ambiguos symbol"
                            data += '\t'.join(line)+'\n' #ambiguos case : ???????
                        else:
                            line[entrez_index] = alias_table_hugo_dict[hugo][0]
                        data += '\t'.join(line)+'\n'
                    else:
                        data += '\t'.join(line)+'\n'
                else:
                    data += '\t'.join(line)+'\n'
                #There are no cases in the main and alias table where a hugo symbol is in both of them.
        os.remove(fpath)
        with open(fpath,'w') as outfile:
            outfile.write(data)

for study in studies_list:
    study_files = os.listdir(dh_path+'/'+study)
    for file_name in study_files:
        if file_name.startswith('data') and not file_name.endswith('.seg') and not file_name in exluded_files_list:
            file_path = dh_path+'/'+study+'/'+file_name
            with open(file_path,'r') as data_file:
                for line in data_file:
                    if line.startswith('Hugo_Symbol') or line.startswith('Entrez_Gene_Id'):
                        header_cols = line.strip('\n').split('\t')
                        if 'Entrez_Gene_Id' in header_cols and 'Hugo_Symbol' in header_cols:
                            entrez_index = header_cols.index('Entrez_Gene_Id')
                            gene_index = header_cols.index('Hugo_Symbol')
                            entrez_gene(entrez_index, gene_index, file_path)
                        break
