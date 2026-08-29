def transform_data_update_gene_matrix(**kwargs):
	import os
	import pandas as pd

	try:
		ti = kwargs['ti']
		study_path = ti.xcom_pull(task_ids='identify_release_create_study_dir')
		if study_path is None:
			raise ValueError("Error: No STUDY_PATH found in XCom.")
	except Exception as e:
		raise ValueError(f"Error retrieving STUDY_PATH from XCom: {str(e)}")

	try:
		# Check gene matrix and sv case list files exist
		gene_matrix_file = None
		if 'data_gene_matrix.txt' in os.listdir(study_path):
			gene_matrix_file = os.path.join(study_path, 'data_gene_matrix.txt')
		
		sv_case_list = None
		if 'cases_sv.txt' in os.listdir(os.path.join(study_path, 'case_lists')):
			sv_case_list = os.path.join(study_path, 'case_lists', 'cases_sv.txt')
		
		if gene_matrix_file is None or sv_case_list is None:
			raise FileNotFoundError("Error: gene matrix or the sv case list files are missing in the study folder.")
		
		with open(sv_case_list, 'r') as sv_caselist:
			for line in sv_caselist:
				if line.startswith('case_list_ids'):
					line = line.split(':')[1].strip().split('\t')
					sv_df = pd.DataFrame(line, columns=['SAMPLE_ID'])	

		matrix_df = pd.read_csv(gene_matrix_file, delimiter='\t', dtype=str)
		
		# Add structural variant column to gene panel matrix file
		# The sample list from cases_sv file
		# mutation panel is copied to SV column
		merged_df = pd.merge(matrix_df, sv_df, on='SAMPLE_ID', how='left', indicator=True)
		merged_df['structural_variants'] = merged_df.apply(lambda row: row['mutations'] if row['_merge'] == 'both' else None, axis=1)
		merged_df = merged_df.drop(columns=['_merge'])
		merged_df = merged_df.fillna('NA')

		# Replace the existing gene panel matrix file with updated data
		merged_df.to_csv(gene_matrix_file, index=None, sep='\t')

	except FileNotFoundError as e:
		raise ValueError(f"Error processing files in study folder: {str(e)}")
	except Exception as e:
		raise ValueError(f"Unexpected error occurred: {str(e)}")		


def transform_data_update_sv_file(**kwargs):
	import os
	import pandas as pd

	try:
		ti = kwargs['ti']
		study_path = ti.xcom_pull(task_ids='identify_release_create_study_dir')
		if study_path is None:
			raise ValueError("Error: No STUDY_PATH found in XCom.")
	except Exception as e:
		raise ValueError(f"Error retrieving STUDY_PATH from XCom: {str(e)}")

	# Set suffixes 
	suffixes = ['-intragenic', 'INTRAGENIC', '-intragenic - Archer']
	
	try:
		# Check sv data file exists
		sv_file = None
		if 'data_sv.txt' in os.listdir(study_path):
			sv_file = os.path.join(study_path, 'data_sv.txt')
		
		if sv_file is None:
			raise FileNotFoundError("Error: data_sv.txt file is missing in the study folder.")
	
		sv_data_df = pd.read_csv(sv_file, delimiter='\t', dtype=str)
		mask = sv_data_df['Event_Info'].str.endswith(tuple(suffixes))
		mask_no_missing = mask & ~sv_data_df['Site1_Hugo_Symbol'].isna()
		sv_data_df.loc[mask_no_missing, 'Site2_Hugo_Symbol'] = sv_data_df.loc[mask_no_missing, 'Site1_Hugo_Symbol']
	
		# Replace the existing sv data file with updated gene2 symbol data for intergenic sv's
		sv_data_df.to_csv(sv_file, index=None, sep='\t')
		
	except FileNotFoundError as e:
		raise ValueError(f"Error processing files in study folder: {str(e)}")
	except Exception as e:
		raise ValueError(f"Unexpected error occurred: {str(e)}")		
