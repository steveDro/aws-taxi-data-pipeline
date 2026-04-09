from io import StringIO
import boto3
import pandas as pd


BUCKET_NAME = "stv-taxi-data-pipeline"
FILE_KEY = "raw/taxi-data/yellow_tripdata_2021-01.csv"

URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2021-01.parquet"


def fetch_data():
    data = pd.read_parquet(URL)
    print("Data fetched successfully")
    return data


def upload_to_s3(data):
    csv_buffer = StringIO()
    data.to_csv(csv_buffer, index=False)

    s3 = boto3.client(
        "s3",
        aws_access_key_id="AKIARIOKTUWT72LZPAEO",
        aws_secret_access_key="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",
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
