import pandas as pd

df = pd.read_parquet("s3://stv-taxi-data-pipeline/raw/taxi-data/year=2026/month=05/data.parquet")
print(df.dtypes)