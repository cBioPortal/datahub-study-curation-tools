#Script to modify data files based on the new HGNC genes and entrez ID mappings

import sys
import os
import pandas as pd

dh_path = "/path/to/datahub/public/" #Update the path

#---------------------Script to replace old Entrez_Gene_Ids with new Ids----------------------------->

#1: Read the old to new entrez id mapping file (consolidated from all sub categories of the analysis)
case1_dir = {}
with open('outdated_entrez_ids_list.txt','r') as case1_file:
    for line in case1_file:
        line = line.strip().split('\t')
        case1_dir[line[0]] = line[1]

#2: Read the old to new hugo symbol mapping file (consolidated from all sub categories of the analysis)
case2_dir = {}
with open('outdated_hugo_symbols_list.txt','r') as case2_file:
    for line in case2_file:
        line = line.strip().split('\t')
        case2_dir[line[0]] = line[1]

#3--------------------Read files from datahub folder and replace to new ids/symbols------------------->
#dh_path = "/Users/rmadupuri/GitHub/datahub/public"
studies_list = os.listdir(dh_path)
if '.DS_Store' in studies_list: studies_list.remove('.DS_Store')
exluded_files_list = ['data_bcr_clinical_data_patient.txt','data_bcr_clinical_data_sample.txt','data_clinical_patient.txt','data_clinical_sample.txt','data_clinical_supp_hypoxia.txt','data_gene_matrix.txt','data_microbiome.txt','data_mutational_signature_confidence.txt','data_mutational_signature_contribution.txt','data_timeline_labtest.txt','data_timeline_procedure.txt','data_timeline_specimen.txt','data_timeline_status.txt','data_timeline_surgery.txt','data_timeline_treatment.txt','data_timeline.txt','data_subtypes.txt']

for study in studies_list:
    study_files = os.listdir(dh_path+'/'+study)
    for file_name in study_files:
        if file_name.startswith('data') and not file_name.endswith('.seg') and not file_name in exluded_files_list:
            df = pd.read_csv(dh_path+'/'+study+'/'+file_name, comment='#', sep='\t', header=0, keep_default_na=False, dtype=str, low_memory=False)
            if 'Entrez_Gene_Id' in df.columns:
                df = df.replace({'Entrez_Gene_Id':case1_dir})
            if 'Hugo_Symbol' in df.columns:
                df = df.replace({'Hugo_Symbol':case2_dir})
            os.remove(dh_path+'/'+study+'/'+file_name)
            df.to_csv(dh_path+'/'+study+'/'+file_name, sep='\t', index=False)
