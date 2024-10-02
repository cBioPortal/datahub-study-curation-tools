from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.providers.ssh.operators.ssh import SSHOperator
from datetime import timedelta, datetime

args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime.now() - timedelta(days=1),
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=5)
} 

with DAG(
    dag_id="genie_import_dag",
    default_args=args,
    description="Copies cbioportal formatted data and pushes to s3://cdm-deliverable bucket",
    schedule_interval="@once",
    dagrun_timeout=timedelta(minutes=360),
    tags=["genie"]
) as dag:
    
    start = DummyOperator(
        task_id="start",
    )

    test_ssh = SSHOperator(
        task_id='test_ssh',
        ssh_conn_id="genie_importer_ssh",
        command="echo hello",
        dag=dag
    )

    end = DummyOperator(
        task_id="end",
    )
    
    start >> test_ssh >> end
