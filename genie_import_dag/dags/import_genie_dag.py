"""
import_genie_dag.py
Pulls data from the s3://cdm-deliverable bucket to get the latest list of sample IDs and other metadata about the samples.
"""
from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.providers.ssh.operators.ssh import SSHOperator
from datetime import timedelta, datetime
from airflow.models.param import Param
from airflow.decorators import task

args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email": ["wanga5@mskcc.org"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="import_genie_dag",
    default_args=args,
    description="Checks importer/database version, fetches latest data, and refreshes CDD/Oncotree caches",
    dagrun_timeout=timedelta(minutes=360),
    tags=["genie"],
    params={
        "importer": Param("genie", type="string", title="Import Pipeline", description="Determines which importer to use. Must be one of: ['genie']"),
        "data_repos": Param(["genie"], type="array", title="Data Repository", description="Determines which data repository to pull updates from/cleanup. Acceped values: ['genie', 'dmp']", items={"type": "string"})
    }
) as dag:

    conn_id = "genie_importer_ssh"
    import_scripts_path = "/data/portal-cron/scripts"
    root_data_directory_path = "/data/portal-cron/cbio-portal-data"
    data_repositories_to_use = ""

    DEFAULT_ENVIRONMENT_VARS={
        "IMPORT_SCRIPTS_PATH": import_scripts_path
    }
    
    start = DummyOperator(
        task_id="start",
    )

    @task
    def parse_args(importer: str, data_repos: list):
        data_repo_list = []
        if importer.strip() not in ['genie']:
            raise TypeError('Required argument \'importer\' is incorrect or missing a value.')
        for data_repo in data_repos:
            if data_repo not in ACCEPTED_DATA_REPOS:
                raise TypeError('Required argument \'data_repos\' is incorrect.')
            data_repo_list.append(root_data_directory_path + "/" + data_repo)
        data_repositories_to_use = ' '.join(data_repo_list)
        

    # [START GENIE import setup] --------------------------------
    """
    Does a db check for specified importer/pipeline
    Fetches latest commit from GENIE repository
    Refreshes CDD/Oncotree caches=
    """
    setup_import = SSHOperator(
        task_id="setup_import",
        ssh_conn_id=conn_id,
        command=f"{import_scripts_path}/setup_import.sh {{{{ params.importer }}}} {import_scripts_path}",
        environment=DEFAULT_ENVIRONMENT_VARS,
        dag=dag,
    )
    # [END GENIE import setup] --------------------------------

    # [START GENIE import] --------------------------------
    import_genie = SSHOperator(
        task_id="import_genie",
        ssh_conn_id=conn_id,
        command=f"{import_scripts_path}/import_genie.sh {{{{ params.importer }}}} {import_scripts_path}",
        environment=DEFAULT_ENVIRONMENT_VARS,
        dag=dag,
    )
    # [END GENIE import] --------------------------------

    # [START GENIE repo cleanup] --------------------------------
    cleanup_genie = SSHOperator(
        task_id="cleanup_genie",
        ssh_conn_id=conn_id,
        command=f"{import_scripts_path}/datasource-repo-cleanup.sh {data_repositories_to_use}",
        environment=DEFAULT_ENVIRONMENT_VARS,
        dag=dag,
    )
    # [END GENIE repo cleanup] --------------------------------
    end = DummyOperator(
        task_id="end",
    )

    parsed_args = parse_args("{{ params.importer }}", "{{params.data_repos}}")
    start >> parsed_args >> setup_import >> import_genie >> end
