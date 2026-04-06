import requests
import pandas as pd

URL = "https://raw.githubusercontent.com/DataTalksClub/nyc-tlc-data/main/data/yellow_tripdata_2021-01.csv"


def fetch_data():
    df = pd.read_csv(URL)
    print("Data fetched successfully")
    return df


if __name__ == "__main__":
    df = fetch_data()
    print(df.head())
