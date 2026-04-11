from airflow import DAG
# from airflow.operators.python import PythonOperator
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.hooks.postgres_hook import PostgresHook
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

# hook = PostgresHook(postgres_conn_id="postgres_default")
# conn = hook.get_conn()

conn = psycopg2.connect(
    host="postgres",
    database="airflow", 
    user="airflow",
    password="airflow"
)

def etl_pipeline():
    df = fetch_data()
    upload_to_s3(df)

def load_to_postgres():

    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    file_key = f"raw/taxi-data/year={year}/month={month}/data.parquet"

    s3 = boto3.client("s3")
    buffer = BytesIO()
    s3.download_fileobj("stv-taxi-data-pipeline", file_key, buffer)
    buffer.seek(0)

    # conn = psycopg2.connect(
    #     host="postgres", database="airflow",
    #     user="airflow", password="airflow"
    # )
    cursor = conn.cursor()

    df = pd.read_parquet(buffer, columns=[
        "VendorID", "tpep_pickup_datetime",
        "tpep_dropoff_datetime", "passenger_count", "trip_distance"
    ])

    # Handle nulls
    df["passenger_count"] = df["passenger_count"].fillna(0).astype("int32")
    df["VendorID"] = df["VendorID"].fillna(0).astype("int32")
    df["trip_distance"] = df["trip_distance"].fillna(0.0).astype("float64")
    df["tpep_pickup_datetime"] = pd.to_datetime(df["tpep_pickup_datetime"])
    df["tpep_dropoff_datetime"] = pd.to_datetime(df["tpep_dropoff_datetime"])

    # Convert to a list of plain Python tuples so psycopg2 handles types correctly
    # rows = list(df.itertuples(index=False, name=None))

    # Build native Python tuples
    rows = [
        (
            int(row.VendorID),
            row.tpep_pickup_datetime.to_pydatetime(),
            row.tpep_dropoff_datetime.to_pydatetime(),
            int(row.passenger_count),
            float(row.trip_distance)
        )
        for row in df.itertuples(index=False)
]

    execute_values(
        cursor,
        "INSERT INTO trips(vendor_id, pickup_datetime, dropoff_datetime, passenger_count, trip_distance) VALUES %s",
        rows
        # df.itertuples(index=False, name=None)
    )

    conn.commit()
    cursor.close()
    conn.close()

def check_data():
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM trips")
    count = cursor.fetchone()[0]

    if count == 0:
        raise ValueError("No data loaded!")

    print(f"Data check passed: {count} rows")

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
                id SERIAL PRIMARY KEY,
                vendor_id BIGINT,
                passenger_count BIGINT,
                pickup_datetime TIMESTAMP,
                dropoff_datetime TIMESTAMP,
                trip_distance FLOAT
            )
            """
    )

    data_quality_check = PythonOperator(
        task_id="check_data_quality",
        python_callable=check_data
    )

run_etl >> create_table >> load_task >> data_quality_check
    