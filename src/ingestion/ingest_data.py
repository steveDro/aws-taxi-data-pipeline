from io import StringIO
import boto3
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

FILE_KEY = os.getenv("FILE_KEY")

URL = os.getenv("URL")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REGION = os.getenv("AWS_DEFAULT_REGION")
BUCKET_NAME = os.getenv("BUCKET_NAME")

def fetch_data():
    data = pd.read_parquet(URL)
    print("Data fetched successfully")
    return data


def upload_to_s3(data):
    csv_buffer = StringIO()
    data.to_csv(csv_buffer, index=False)

    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
    )

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=FILE_KEY,
        Body=csv_buffer.getvalue()
    )

    print("Upload to S3 successful!")


if __name__ == "__main__":
    df = fetch_data()
    upload_to_s3(df)
