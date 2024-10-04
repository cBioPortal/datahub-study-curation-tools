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
        "importer": Param("importer", type="string", title="which importer to use, will affect which db is imported into", description="Must be one of: ['genie']"),
    }
) as dag:

    conn_id = "genie_importer_ssh"
    import_scripts_path = "/data/portal-cron/scripts"

    DEFAULT_ENVIRONMENT_VARS={
        "IMPORT_SCRIPTS_PATH": import_scripts_path
    }

    start = DummyOperator(
        task_id="start",
    )

    @task
    def parse_args(importer: str):
        if not importer.strip() not in ['genie']:
            raise TypeError('Required argument \'importer\' is incorrect or missing a value.')

    # [START GENIE import setup] --------------------------------
    """
    Does a db check for specified importer/pipeline
    Fetches latest commit from GENIE repository
    Refreshes CDD/Oncotree caches=
    """
    setup_import = SSHOperator(
        task_id="GENIE Import Setup",
        ssh_conn_id=conn_id,
        command=f"{import_scripts_path}/setup_import.sh {{ params.importer }}",
        environment=DEFAULT_ENVIRONMENT_VARS,
        dag=dag,
    )
    # [END GENIE import setup] --------------------------------

    import_genie = SSHOperator(
        task_id="GENIE Import",
        ssh_conn_id=conn_id,
        commmand=f"{import_scripts_path}/import_genie.sh {{ params.importer }}",
        environment=DEFAULT_ENVIRONMENT_VARS,
        dag=dag,
    )

    end = DummyOperator(
        task_id="end",
    )

    parsed_args = parse_args("{{ params.importer }}")
    start >> parsed_args >> setup_import >> import_genie >> end