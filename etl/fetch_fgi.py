import requests
import pandas as pd
from etl.to_csv import append_unique_rows



def fetch_fgi(url='https://api.alternative.me/fng/?limit=250', timeout=10):
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()

    data = response.json()
    data_list = data.get("data", [])
    if not data_list:
        return None

    rows = []
    for item in data_list:
        ts = pd.to_datetime(pd.to_numeric(item['timestamp'], errors='coerce'), unit='s', utc=True)
        value = int(item['value'])
        classification = item['value_classification']
        rows.append({
            "date": ts,
            "value": value,
            "classification": classification
        })

    df = pd.DataFrame(rows).sort_values(by="date", ascending=True)
    
    return df

def main():
    raw = fetch_fgi()
    if raw is not None:
        append_unique_rows(raw, 'data/fgi.csv', subset_cols=["date"])
    else:
        print("No FGI data available.")

if __name__ == "__main__":
    main()