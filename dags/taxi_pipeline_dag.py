from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys

sys.path.append('/opt/airflow')

from src.ingestion.ingest_data import fetch_data, upload_to_s3

default_args = {
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

def etl_pipeline():
    df = fetch_data()
    upload_to_s3(df)

with DAG(
    dag_id="taxi_data_pipeline",
    start_date=datetime(2026, 4, 1),
    schedule="@daily",
    catchup=False,
    default_args=default_args,
    tags=["data-engineering", "aws"]
) as dag:

    run_etl = PythonOperator(
        task_id="run_etl_pipeline",
        python_callable=etl_pipeline
    )
    