from airflow import DAG
# from airflow.operators.python import PythonOperator
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from datetime import datetime, timedelta
from psycopg2.extras import execute_values
import sys
import pandas as pd
import psycopg2
from io import BytesIO 
import boto3

sys.path.append('/opt/airflow')

from src.ingestion.ingest_data import fetch_data, upload_to_s3

default_args = {
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

def etl_pipeline():
    df = fetch_data()
    upload_to_s3(df)

def load_to_postgres():
    conn = psycopg2.connect(
        host="postgres",
        database="airflow",
        user="airflow",
        password="airflow"
    )
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    file_key = f"raw/taxi-data/year={year}/month={month}/data.parquet"

    s3 = boto3.client("s3")
    buffer = BytesIO()
    s3.download_fileobj("stv-taxi-data-pipeline", file_key, buffer)
    buffer.seek(0)

    conn = psycopg2.connect(
        host="postgres", database="airflow",
        user="airflow", password="airflow"
    )
    cursor = conn.cursor()

    df = pd.read_parquet(buffer, columns=[
        "VendorID", "tpep_pickup_datetime",
        "tpep_dropoff_datetime", "passenger_count", "trip_distance"
    ])

    df = df.astype({
        "VendorID": "int32",
        "trip_distance": "float64",
        "passenger_count": "int32",
    })
    df["tpep_pickup_datetime"] = pd.to_datetime(df["tpep_pickup_datetime"])
    df["tpep_dropoff_datetime"] = pd.to_datetime(df["tpep_dropoff_datetime"])

    # Convert to a list of plain Python tuples so psycopg2 handles types correctly
    rows = list(df.itertuples(index=False, name=None))

    execute_values(
        cursor,
        "INSERT INTO trips VALUES %s",
        rows
        # df.itertuples(index=False, name=None)
    )

    conn.commit()
    cursor.close()
    conn.close()


with DAG(
    dag_id="taxi_data_pipeline",
    start_date=datetime(2026, 4, 9),
    schedule="@daily",
    catchup=False,
    default_args=default_args,
    tags=["data-engineering", "aws"]
) as dag:

    run_etl = PythonOperator(
        task_id="run_etl_pipeline",
        python_callable=etl_pipeline
    )

    load_task = PythonOperator(
        task_id="load_to_postgres",
        python_callable=load_to_postgres
    )

    create_table = SQLExecuteQueryOperator(
        task_id="create_trips_table",
        conn_id="postgres_default",
        sql="""
            DROP TABLE IF EXISTS trips;
            CREATE TABLE trips (
                vendor_id BIGINT,
                passenger_count BIGINT,
                pickup_datetime TIMESTAMP,
                dropoff_datetime TIMESTAMP,
                trip_distance FLOAT
            )
            """
    )

run_etl >> create_table >> load_task
    