from airflow import DAG
from airflow.models.param import Param
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from datetime import datetime

default_args = {
	'owner': 'airflow',
	'depends_on_past': False,
	'email_on_failure': False,
	'start_date': datetime(2024, 9, 10),
	'email_on_retry': False,
}

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


def git_push(**kwargs):
	import subprocess
	import os

	try:
		ti = kwargs['ti']
		study_path = ti.xcom_pull(task_ids='identify_release_create_study_dir')
		if study_path is None:
			raise ValueError("Error: No STUDY_PATH found in XCom.")
	except Exception as e:
		raise ValueError(f"Error retrieving STUDY_PATH from XCom: {str(e)}")

	try:
		# Initializing a tmp git location for testing purposes
		# TODO: Update in production to work on the genie git repo
		subprocess.run(['git', 'config', 'url."https://<TOKEN>ttps://github.com/".insteadOf', 'https://github.com/'], check=True)
		os.chdir(study_path)
		if not os.path.isdir(os.path.join(study_path, '.git')):
			subprocess.run(['git', 'init'], check=True)
	
		# Push changes to Git
		subprocess.run(['git', 'add', '.'], check=True)
		commit_message = 'Update genie data from Synapse'
		subprocess.run(['git', 'commit', '-m', commit_message], check=True)
		subprocess.run(['git', 'push', 'origin', 'main'], check=True)
	
		print("Data pushed to GitHub")

	except subprocess.CalledProcessError as e:
		raise RuntimeError(f"Git command failed: {str(e)}")
	except Exception as e:
		raise RuntimeError(f"Unexpected error occurred: {str(e)}")

with DAG(
	'genie_import_dag',
	description='Import GENIE data to cBioPortal from Synapse',
	default_args=default_args,
	schedule_interval=None,
	params={
		"synapse_download_path": Param("/opt/airflow/data/synapse_download", type="string", title="Path to store synapse download"),
		"syn_ID": Param("syn5521835", type="string", title="ID of the data folder that needs to be downloaded for import"),
		"data_dir": Param("/opt/airflow/data", type="string", title="Where to write Genie data")
	}
) as dag:

	synapse_auth_token = Variable.get("synapse_auth_token")

	"""
	TASK1:
	Download data from Synapse using the synID var.
	Data gets written to $SYNAPSE_DOWNLOAD_PATH
	"""
	pull_data_from_synapse = BashOperator(
		task_id='pull_data_from_synapse',
		env={
			"SYNAPSE_DOWNLOAD_PATH": "{{ params.synapse_download_path }}",
			"SYN_ID": "{{ params.syn_ID }}",
			"SYNAPSE_AUTH_TOKEN": synapse_auth_token
		},
		append_env=True,
		bash_command=f"""
		set -e
		set -o pipefail
		
		handle_error() {{
			echo "$1" >&2
			exit 1
		}}
		
		if [ -d $SYNAPSE_DOWNLOAD_PATH ]; then
			echo 'Removing existing directory..'
			rm -rf $SYNAPSE_DOWNLOAD_PATH || handle_error "Failed to remove directory $SYNAPSE_DOWNLOAD_PATH"
		fi
		
		echo 'Downloading data from Synapse..'
		synapse -p $SYNAPSE_AUTH_TOKEN get -r $SYN_ID --downloadLocation $SYNAPSE_DOWNLOAD_PATH --followLink || handle_error "Failed to download data from Synapse"
		echo -e '\\nFiles are downloaded to: $SYNAPSE_DOWNLOAD_PATH\\n'
		"""
	)


	"""
	TASK2:
	From the meta_study.txt file, identify the Study ID
	Rename the downloaded directory accordingly
	"""
	identify_release_create_study_dir = BashOperator(
		task_id='identify_release_create_study_dir',
		env={
			"SYNAPSE_DOWNLOAD_PATH": "{{ params.synapse_download_path }}",
			"DATA_DIR": "{{ params.data_dir }}"
		},
		append_env=True,
		bash_command=f"""
		set -e
		set -o pipefail
		
		handle_error() {{
			echo "$1" >&2
			exit 1
		}}
		
		if [ ! -f "$SYNAPSE_DOWNLOAD_PATH/meta_study.txt" ]; then
			handle_error "Error: meta_study.txt not found in $SYNAPSE_DOWNLOAD_PATH"
		fi
		
		study_identifier=$(grep "cancer_study_identifier" $SYNAPSE_DOWNLOAD_PATH/meta_study.txt | awk -F ": " '{{print $2}}')
		if [ -z "$study_identifier" ]; then
			handle_error "Error: Study identifier not found or empty in meta_study.txt"
		fi
		echo "Study Identifier: $study_identifier"
		
		GENIE_STUDY_PATH="$DATA_DIR/$study_identifier"
		if [ -d "$GENIE_STUDY_PATH" ]; then
			echo 'Removing existing directory..'
			rm -rf "$GENIE_STUDY_PATH" || handle_error "Failed to remove directory $GENIE_STUDY_PATH"
		fi
		
		echo -e "Moving files to $GENIE_STUDY_PATH...\n"
		mv $SYNAPSE_DOWNLOAD_PATH "$GENIE_STUDY_PATH" || handle_error "Failed to move files to $GENIE_STUDY_PATH"
		echo "$GENIE_STUDY_PATH"
		""",
		do_xcom_push=True
	)
	

	"""
	TASK3: 
	Remove files not required for import into cBioPortal
	"""
	transform_data_cleanup_files = BashOperator(
		task_id='transform_data_cleanup_files',
		bash_command="""
		set -e
		set -o pipefail
		
		STUDY_PATH="{{ ti.xcom_pull(task_ids='identify_release_create_study_dir') }}"
		
		if [ -z "$STUDY_PATH" ]; then
			echo "Error: STUDY_PATH is empty or unset." >&2
			exit 1
		fi
		
		if [ ! -d "$STUDY_PATH" ]; then
			echo "Error: Study directory $STUDY_PATH does not exist." >&2
			exit 1
		fi
		
		files_to_remove=("*.pdf" "*.csv" "*.html" "*.bed" "assay_information.txt" "genomic_information.txt" "SYNAPSE_METADATA_MANIFEST.tsv" "case_lists/SYNAPSE_METADATA_MANIFEST.tsv")
	
		for pattern in "${files_to_remove[@]}"; do
			for dir in "$STUDY_PATH" "$STUDY_PATH/case_lists"; do
				for file in "$dir"/$pattern; do
					if [ -e "$file" ]; then
						rm "$file"
						echo -e "Removed $(basename "$file") from $dir"
					fi
				done
			done
		done
	
		echo "$STUDY_PATH"
		""",
		do_xcom_push=True
	)
	
	"""
	TASK4:
	The gene matrix file from synapse is missing the structural_variants column required for import. This task will update the matrix file based on the information from the cases_sv.txt file:
	- Add structural_variants column to gene panel matrix file
	- Uses the sample list from the cases_sv.txt file
	- Copies the mutation panel IDs as SV panel IDs
	"""
	transform_data_update_gene_matrix = PythonOperator(
		task_id='transform_data_update_gene_matrix',
		python_callable=transform_data_update_gene_matrix,
		provide_context=True
	)
	
	"""
	TASK5:
	The data_sv.txt file downloaded from Synapse has missing or empty gene2 symbols in some cases for intragenic structural variants.
	For these intragenic variants, gene1 and gene2 are the same. This task updates the gene2 symbol in the file to match gene1 for such cases.
	"""
	transform_data_update_sv_file = PythonOperator(
		task_id='transform_data_update_sv_file',
		python_callable=transform_data_update_sv_file,
		provide_context=True
	)

	"""
	TASK6:
	Push the data to genie Git repo
	"""
	git_push = PythonOperator(
		task_id='git_push',
		python_callable=git_push,
		provide_context=True,
	)

pull_data_from_synapse >> identify_release_create_study_dir >> [transform_data_cleanup_files, transform_data_update_gene_matrix, transform_data_update_sv_file] >> git_push