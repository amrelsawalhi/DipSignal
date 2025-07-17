import pandas as pd
from fredapi import Fred
import yfinance as yf
from etl.to_csv import append_unique_rows


def fetch_macro_data(start_date="2018-02-1", end_date=None):
    FRED_API_KEY = "2cb3f8eded5f36f1beb5cc1a202f6a0b"
    fred = Fred(api_key=FRED_API_KEY)

    # FRED series
    fred_series = {
        "cpi": "CPIAUCSL",
        "interest_rate": "FEDFUNDS",
        "sp500": "SP500"
    }

    df_list = []
    for name, series_id in fred_series.items():
        s = fred.get_series(series_id, start_date, end_date)
        s.name = name
        df_list.append(s)

    fred_df = pd.concat(df_list, axis=1)

    # Fetch DXY from Yahoo Finance
    dxy = yf.download("DX-Y.NYB", start=start_date, end=end_date, interval="1d", auto_adjust=False)["Close"]
    dxy.name = "dxy"

    # Merge and detect market closed days
    macro_df = pd.concat([fred_df, dxy], axis=1)
    full_index = pd.date_range(start=macro_df.index.min(), end=macro_df.index.max(), freq="D")
    macro_df = macro_df.reindex(full_index)
    macro_df.index.name = "date"

    # Detect missing data before fill
    macro_df["market_closed"] = macro_df[["cpi", "interest_rate", "sp500", "DX-Y.NYB"]].isna().all(axis=1)

    # Forward fill and round
    macro_df = macro_df.ffill().round(2).reset_index()

    # Reorder and select columns
    macro_df['dxy'] = macro_df['DX-Y.NYB']
    macro_df = macro_df[["date", "dxy", "sp500", "cpi", "interest_rate", "market_closed"]]
    return macro_df

def main():
    df_new = fetch_macro_data()
    append_unique_rows(df_new, 'data/macro.csv', subset_cols=["date"])

if __name__ == "__main__":
    main()