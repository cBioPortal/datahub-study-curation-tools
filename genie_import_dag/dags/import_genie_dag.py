"""
import_genie_dag.py
Imports Genie study to MySQL and ClickHouse databases
"""
from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.providers.ssh.operators.ssh import SSHOperator
from datetime import timedelta, datetime
from airflow.models.param import Param
from airflow.decorators import task
from airflow.utils.trigger_rule import TriggerRule

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
    max_active_runs=1,
    start_date=datetime(2024, 12, 3),
    schedule_interval=None,
    tags=["genie"],
    params={
        "importer": Param("genie", type="string", title="Import Pipeline", description="Determines which importer to use. Must be one of: ['genie']"),
        "data_repos": Param("genie,dmp", type="string", title="Data Repositories", description="Comma separated list of data repositories to pull updates from/cleanup. Acceped values: ['genie', 'dmp']")
    }
) as dag:

    conn_id = "genie_importer_ssh"
    import_scripts_path = "/data/portal-cron/scripts"
    
    start = DummyOperator(
        task_id="start",
    )

    @task
    def parse_args(importer: str, data_repos: str):
        to_use = []
        if importer.strip() not in ['genie']:
            raise TypeError('Required argument \'importer\' is incorrect or missing a value.')
        
        ACCEPTED_DATA_REPOS = ["genie", "dmp"]
        root_data_directory_path = "/data/portal-cron/cbio-portal-data"
        for data_repo in data_repos.split(","):
            if data_repo.strip() not in ACCEPTED_DATA_REPOS:
                raise TypeError('Required argument \'data_repos\' is incorrect.')
            to_use.append(root_data_directory_path + "/" + data_repo.strip())
        
        data_repositories_to_use = ' '.join(to_use)
        return data_repositories_to_use
        
    datarepos = "{{ task_instance.xcom_pull(task_ids='parse_args') }}"

    # [START GENIE database clone] --------------------------------
    """
    Determines which database is "production" vs "not production"
    Drops tables in the non-production database
    Clones the production MySQL database into the non-production database
    """
    clone_database = SSHOperator(
        task_id="clone_database",
        ssh_conn_id=conn_id,
        command=f"{import_scripts_path}/clone_db_wrapper.sh {import_scripts_path}",
        dag=dag,
    )
    # [END GENIE database clone] --------------------------------
    
    # [START GENIE import setup] --------------------------------
    """
    Does a db check for specified importer/pipeline
    Fetches latest commit from GENIE repository
    Refreshes CDD/Oncotree caches
    """
    setup_import = SSHOperator(
        task_id="setup_import",
        ssh_conn_id=conn_id,
        command=f"{import_scripts_path}/setup_import.sh {{{{ params.importer }}}} {import_scripts_path}",
        dag=dag,
    )
    # [END GENIE import setup] --------------------------------

    # [START GENIE import] --------------------------------
    """
    Imports cancer types
    Imports genie-portal column in portal-configuration spreadsheet
    """
    import_genie = SSHOperator(
        task_id="import_genie",
        ssh_conn_id=conn_id,
        command=f"{import_scripts_path}/import_genie.sh {{{{ params.importer }}}} {import_scripts_path}",
        dag=dag,
    )
    # [END GENIE import] --------------------------------

    # [START Clickhouse import] --------------------------------
    """
    Drops ClickHouse tables
    Copies MySQL tables to ClickHouse
    Creates derived ClickHouse tables
    """
    import_clickhouse = SSHOperator(
        task_id="import_clickhouse",
        ssh_conn_id=conn_id,
        command=f"{import_scripts_path}/import_clickhouse.sh {import_scripts_path}",
        dag=dag,
    )
    # [END Clickhouse import] --------------------------------

    # [START GENIE repo cleanup] --------------------------------
    """
    Removes untracked files/LFS objects from Genie repo
    """
    cleanup_genie = SSHOperator(
        task_id="cleanup_genie",
        ssh_conn_id=conn_id,
        trigger_rule=TriggerRule.ALL_DONE,
        command=f"{import_scripts_path}/datasource-repo-cleanup.sh {datarepos}",
        dag=dag,
    )

    # [END GENIE repo cleanup] --------------------------------
    end = DummyOperator(
        task_id="end",
    )

    parsed_args = parse_args("{{ params.importer }}", "{{ params.data_repos }}")
    start >> parsed_args >> clone_database >> setup_import >> import_genie >> import_clickhouse >> cleanup_genie >> end
