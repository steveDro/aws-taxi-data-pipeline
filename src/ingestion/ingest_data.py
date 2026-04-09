from io import StringIO
import boto3
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime
import logging

load_dotenv()

FILE_KEY = os.getenv("FILE_KEY")

URL = os.getenv("URL")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REGION = os.getenv("AWS_DEFAULT_REGION")
BUCKET_NAME = os.getenv("BUCKET_NAME")

logging.basicConfig(level=logging.INFO)

def fetch_data():
    logging.info("Fetching data...")
    data = pd.read_parquet(URL)
    logging.info(f"Fetched {len(data)} rows.")
    return data


def upload_to_s3(data):
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")

    file_key = f"raw/taxi-data/year={year}/month={month}/data.parquet"

    buffer = StringIO()
    data.to_parquet(buffer, index=False)

    s3 = boto3.client("s3")

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=file_key,
        Body=buffer.getvalue()
    )

    print(f"Upload to {file_key}")


if __name__ == "__main__":
    df = fetch_data()
    upload_to_s3(df)
