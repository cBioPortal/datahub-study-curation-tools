"""
import_genie_dag.py
Imports Genie study to MySQL and ClickHouse databases.
"""
from datetime import timedelta, datetime
from airflow import DAG
from airflow.decorators import task
from airflow.exceptions import AirflowException
from airflow.models.param import Param
from airflow.providers.ssh.operators.ssh import SSHOperator
from airflow.utils.trigger_rule import TriggerRule


args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email": ["chennac@mskcc.org"],
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
        "data_repos": Param("genie,dmp", type="string", title="Data Repositories", description="Comma-separated list of data repositories to pull updates from/cleanup. Accepted values: ['genie', 'dmp']")
    }
) as dag:

    conn_id = "genie_importer_ssh"
    import_scripts_path = "/data/portal-cron/scripts"
    
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

    """
    Determines which database is "production" vs "not production"
    Drops tables in the non-production MySQL database
    Clones the production MySQL database into the non-production database
    """
    clone_database = SSHOperator(
        task_id="clone_database",
        ssh_conn_id=conn_id,
        command=f"{import_scripts_path}/clone_db_wrapper.sh {import_scripts_path}",
        dag=dag,
    )
    
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

    """
    If any upstream tasks failed, mark the import attempt as abandoned.
    """
    set_import_status = SSHOperator(
        task_id="set_import_status",
        ssh_conn_id=conn_id,
        trigger_rule=TriggerRule.ONE_FAILED,
        command=f"{import_scripts_path}/set_import_status.sh abandoned {import_scripts_path}",
        dag=dag,
    )

    """
    Removes untracked files/LFS objects from Genie repo.
    """
    cleanup_genie = SSHOperator(
        task_id="cleanup_genie",
        ssh_conn_id=conn_id,
        trigger_rule=TriggerRule.ALL_DONE,
        command=f"{import_scripts_path}/datasource-repo-cleanup.sh {datarepos}",
        dag=dag,
    )

    """
    If any upstream tasks failed, this task will propagate the "Failed" status to the Dag Run.
    """
    @task(trigger_rule=TriggerRule.ONE_FAILED, retries=0)
    def watcher():
        raise AirflowException("Failing task because one or more upstream tasks failed.")

    parsed_args = parse_args("{{ params.importer }}", "{{ params.data_repos }}")
    parsed_args >> clone_database >> setup_import >> import_genie >> import_clickhouse >> set_import_status >> cleanup_genie >> watcher()
