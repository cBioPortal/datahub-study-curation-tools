from airflow import DAG
from airflow.models.param import Param
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dags.executor_config_genie import k8s_executor_config_genie

default_args = {
	'owner': 'airflow',
	'depends_on_past': False,
	'email_on_failure': False,
	'start_date': datetime(2024, 9, 10),
	'email_on_retry': False,
	'executor_config': k8s_executor_config_genie
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
	'genie_data_dag',
	description='Prepare GENIE data for import to cBioPortal from Synapse',
	default_args=default_args,
	schedule_interval=None,
	params={
		"repos_dir": Param("/opt/airflow/git_repos", type="string", title="Path to store synapse download"),
		"synapse_download_path": Param("/opt/airflow/git_repos/synapse_download", type="string", title="Path to store synapse download"),
		"syn_ID": Param("syn5521835", type="string", title="ID of the data folder that needs to be downloaded for import"),
	},
	tags=["genie"]
) as dag:

	synapse_auth_token = Variable.get("synapse_auth_token")

	clone_genie_repo = BashOperator(
		task_id='clone_genie_repo',
		env={
			"REPOS_DIR": "{{ params.repos_dir }}",
		},
		append_env=True,
		bash_command="scripts/clone_genie_repo.sh"
	)

	"""
	Download data from Synapse using the synID var.
	Data gets written to $SYNAPSE_DOWNLOAD_PATH
	"""
	pull_data_from_synapse = BashOperator(
		task_id='pull_data_from_synapse',
		env={
			"SYNAPSE_DOWNLOAD_PATH": "{{ params.synapse_download }}",
			"SYN_ID": "{{ params.syn_ID }}",
			"SYNAPSE_AUTH_TOKEN": synapse_auth_token
		},
		append_env=True,
		bash_command="scripts/pull_data_from_synapse.sh"
	)


	"""
	From the meta_study.txt file, identify the Study ID
	Rename the downloaded directory accordingly
	"""
	identify_release_create_study_dir = BashOperator(
		task_id='identify_release_create_study_dir',
		env={
			"SYNAPSE_DOWNLOAD_PATH": "{{ params.synapse_download_path }}",
			"REPOS_DIR": "{{ params.repos_dir }}",
		},
		append_env=True,
		bash_command="scripts/identify_release_create_study_dir.sh",
		do_xcom_push=True
	)
	

	"""
	Remove files not required for import into cBioPortal
	"""
	transform_data_cleanup_files = BashOperator(
		task_id='transform_data_cleanup_files',
		bash_command="scripts/transform_data_cleanup_files.sh",
		do_xcom_push=True
	)
	
	"""
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
	The data_sv.txt file downloaded from Synapse has missing or empty gene2 symbols in some cases for intragenic structural variants.
	For these intragenic variants, gene1 and gene2 are the same. This task updates the gene2 symbol in the file to match gene1 for such cases.
	"""
	transform_data_update_sv_file = PythonOperator(
		task_id='transform_data_update_sv_file',
		python_callable=transform_data_update_sv_file,
		provide_context=True
	)

	"""
	Push the data to genie Git repo
	"""
	git_push = PythonOperator(
		task_id='git_push',
		python_callable=git_push,
		provide_context=True,
	)

	"""
	Trigger the Genie import
	"""
	trigger_genie_import = TriggerDagRunOperator(
        task_id="trigger_genie_import",
        trigger_dag_id="genie_import_dag",
    )

pull_data_from_synapse >> identify_release_create_study_dir >> [transform_data_cleanup_files, transform_data_update_gene_matrix, transform_data_update_sv_file] >> git_push >> trigger_genie_import