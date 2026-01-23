"""
Generate TCGA Imaging Resource Files for cBioPortal

This script downloads TCGA imaging data from the NCI Imaging Data Commons (IDC)
and generates cBioPortal-compatible resource files linking patients to their
imaging studies via OHIF and SLIM viewer URLs.

Input:
    - TCGA Pan Cancer Atlas 2018 study directories with data_clinical_patient.txt files

Output:
    - idc_tcga.txt: TCGA imaging data exported from IDC (intermediate file)
    - data_resource_patient.txt: Patient-to-imaging study mappings
    - data_resource_definition.txt: Resource type definitions
"""

import pandas as pd
import numpy as np
import os
from idc_index import IDCClient

# Step 1: Download TCGA imaging data from IDC
print("Downloading TCGA imaging data from IDC...")
client = IDCClient()
client.sql_query("SELECT * FROM index WHERE collection_id LIKE '%tcga%'").to_csv("idc_tcga.txt", sep='\t', index=None)
print("Downloaded data to idc_tcga.txt")

# Step 2: Read IDC TCGA imaging data
df_tcga = pd.read_csv("idc_tcga.txt", sep='\t', dtype=str)

# Remove modalities that cannot directly be viewed along with Other type
df_tcga = df_tcga[~df_tcga['Modality'].isin(['ANN', 'SEG', 'SR', 'OT'])]

# Group the patients by collection_id, PatientID, StudyInstanceUID, Modality
cols = ['PatientID', 'StudyInstanceUID', 'Modality']
resource_df = df_tcga[cols].drop_duplicates().reset_index(drop=True)

# Map modalities to cBioPortal resource IDs
modality_map = {
    'CR': 'IDC_OHIF_CR',
    'CT': 'IDC_OHIF_CT',
    'DX': 'IDC_OHIF_DX',
    'MG': 'IDC_OHIF_MG',
    'MR': 'IDC_OHIF_MR',
    'NM': 'IDC_OHIF_NM',
    'PT': 'IDC_OHIF_PT',
    'SM': 'IDC_SLIM'
}
resource_df['Modality'] = resource_df['Modality'].replace(modality_map)

# Generate viewer URLs based on modality
# SLIM viewer for slide microscopy, OHIF viewer for all other modalities
resource_df['StudyInstanceUID'] = np.where(
    resource_df['Modality'] == 'IDC_SLIM',
    'https://viewer.imaging.datacommons.cancer.gov/slim/studies/' + resource_df['StudyInstanceUID'],
    'https://viewer.imaging.datacommons.cancer.gov/viewer/' + resource_df['StudyInstanceUID']
)

# Rename columns to match cBioPortal format
resource_df = resource_df[['PatientID', 'Modality', 'StudyInstanceUID']]
resource_df.columns = ['PATIENT_ID', 'RESOURCE_ID', 'URL']

# Resource definition mappings for display names
definition_map = {
    'IDC_OHIF_CR': 'Computed Radiography',
    'IDC_OHIF_CT': 'CT Scan',
    'IDC_OHIF_DX': 'Digital Radiography',
    'IDC_OHIF_MG': 'Mammography',
    'IDC_OHIF_MR': 'Magnetic Resonance',
    'IDC_OHIF_NM': 'Nuclear Medicine',
    'IDC_OHIF_PT': 'PET Scan',
    'IDC_SLIM': 'H&E Slide'
}

# Path to datahub public studies
dh_files_path = "/Users/madupurr/Github/datahub/public"

# Process each TCGA Pan Cancer Atlas 2018 study
for st in os.listdir(dh_files_path):
    if 'tcga_pan_can_atlas_2018' in st:
        patient_file = os.path.join(dh_files_path, st, 'data_clinical_patient.txt')
        resource_file = os.path.join(dh_files_path, st, 'data_resource_patient.txt')
        resource_def_file = os.path.join(dh_files_path, st, 'data_resource_definition.txt')
        
        # Read existing clinical patient data
        clinical_df = pd.read_csv(patient_file, sep='\t', skiprows=4, dtype=str)
        patient_ids = clinical_df['PATIENT_ID'].unique()    
        
        # Filter resource_df for only matching patients in this study
        filtered_resource_df = resource_df[resource_df['PATIENT_ID'].isin(patient_ids)]
        
        # Write patient resource file
        filtered_resource_df = filtered_resource_df.sort_values(by='PATIENT_ID').reset_index(drop=True)
        filtered_resource_df.to_csv(resource_file, sep='\t', index=False)
        print(f"Written {len(filtered_resource_df)} resources to {resource_file}")
        
        # Get unique resource IDs present in this study
        resource_ids_in_study = filtered_resource_df['RESOURCE_ID'].unique()
        
        # Build and write resource definition file
        if len(resource_ids_in_study) > 0:
            resource_def_df = pd.DataFrame({
                'RESOURCE_ID': resource_ids_in_study,
                'DISPLAY_NAME': [definition_map[rid] for rid in resource_ids_in_study],
                'RESOURCE_TYPE': 'PATIENT',
                'DESCRIPTION': [definition_map[rid] for rid in resource_ids_in_study],
                'OPEN_BY_DEFAULT': 'TRUE',
                'PRIORITY': 1
            })
            
            resource_def_df.to_csv(resource_def_file, sep='\t', index=False)
            print(f"Written definitions to {resource_def_file}")
