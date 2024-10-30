from airflow import DAG
from airflow.models.param import Param
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.decorators import task
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

with DAG(
	'genie_data_dag',
	description='Prepare GENIE data for import to cBioPortal from Synapse',
	default_args=default_args,
	schedule_interval=None,
	params={
		"repos_dir": Param("/opt/airflow/git_repos", type="string", title="Path to store genie repository"),
		"synapse_download_path": Param("/opt/airflow/git_repos/synapse_download", type="string", title="Path to store synapse download"),
		"syn_ID": Param("syn5521835", type="string", title="ID of the data folder that needs to be downloaded for import"),
		"push_to_repo": Param(False, type="boolean", title="Push data to remote Genie repository"),
		"trigger_import": Param(False, type="boolean", title="Trigger Genie import DAG"),
	},
	tags=["genie"]
) as dag:

	synapse_auth_token = Variable.get("synapse_auth_token")

	"""
	Clone the genie repo (if it doesn't already exist)
	"""
	clone_genie_repo = BashOperator(
		task_id='clone_genie_repo',
		env={
			"REPOS_DIR": "{{ params.repos_dir }}",
		},
		append_env=True,
		bash_command="scripts/clone_genie_repo.sh"
	)

	"""
	Fetch the genie repo
	"""
	fetch_genie_repo = BashOperator(
		task_id='fetch_genie_repo',
		env={
			"REPOS_DIR": "{{ params.repos_dir }}",
		},
		append_env=True,
		bash_command="scripts/fetch_genie_repo.sh"
	)

	"""
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
		bash_command="scripts/pull_data_from_synapse.sh",
		trigger_rule="none_failed"
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
	@task
	def transform_data_update_gene_matrix(**kwargs):
		import dags.scripts.genie_data_transformations as genie
		genie.transform_data_update_gene_matrix(**kwargs)
	
	"""
	The data_sv.txt file downloaded from Synapse has missing or empty gene2 symbols in some cases for intragenic structural variants.
	For these intragenic variants, gene1 and gene2 are the same. This task updates the gene2 symbol in the file to match gene1 for such cases.
	"""
	@task
	def transform_data_update_sv_file(**kwargs):
		import dags.scripts.genie_data_transformations as genie
		genie.transform_data_update_sv_file(**kwargs)

	"""
	Push the data to genie Git repo
	"""
	git_push = BashOperator(
		task_id='git_push',
		env={
			"REPOS_DIR": "{{ params.repos_dir }}",
			"PUSH_TO_REPO": "{{ params.push_to_repo }}"
		},
		append_env=True,
		bash_command="scripts/git_push.sh",
	)

	# Add branch / short circuit here
	@task.short_circuit()
	def decide_to_trigger_genie_import(trigger_import):
		return trigger_import == "True"
	
	"""
	Trigger the Genie import
	"""
	trigger_genie_import = TriggerDagRunOperator(
        task_id="trigger_genie_import",
        trigger_dag_id="genie_import_dag",
    )

clone_genie_repo >> fetch_genie_repo >> pull_data_from_synapse >> identify_release_create_study_dir >> [transform_data_cleanup_files, transform_data_update_gene_matrix(), transform_data_update_sv_file()] >> git_push >> decide_to_trigger_genie_import("{{ params.trigger_import }}") >> trigger_genie_import