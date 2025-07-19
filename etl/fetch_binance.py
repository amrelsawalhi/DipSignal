import pandas as pd
import pandas_ta as ta
import requests
import time
from to_csv import append_unique_rows

def fetch_ohlcv_binance_full(symbol="BTCUSDT", interval="1d", start_date="2018-02-01", days=4000):
    """
    Fetch up to `days` of OHLCV data by paginating Binance API (1000 data limit per request).

    Parameters:
        symbol (str): Trading pair (e.g., 'BTCUSDT')
        interval (str): Interval (e.g., '1d')
        start_date (str): Start date in 'YYYY-MM-DD' format
        days (int): Total number of days to fetch

    Returns:
        pd.DataFrame: Full OHLCV data
    """
    url = "https://api.binance.com/api/v3/klines"
    all_data = []
    limit = 1000
    start_ts = int(pd.to_datetime(start_date).timestamp() * 1000)
    one_day_ms = 24 * 60 * 60 * 1000
    total_batches = (days // limit) + (1 if days % limit else 0)

    for _ in range(total_batches):
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "startTime": start_ts,
            "limit": min(limit, days)
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break

        all_data.extend(batch)
        start_ts = batch[-1][0] + one_day_ms
        days -= limit
        time.sleep(0.5)  # Avoid hitting rate limits

    df = pd.DataFrame(all_data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])

    df["date"] = pd.to_datetime(df["open_time"], unit="ms").dt.date
    df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
    return df[["date", "open", "high", "low", "close", "volume"]]

def fetch_ohlcv_binance(symbol: str, interval="1d", limit=250):
    """
    Fetch OHLCV data from Binance for a given symbol, interval, and limit.
    
    Parameters:
        symbol (str): Trading pair symbol (e.g., BTCUSDT)
        interval (str): Candlestick interval (e.g., '1d', '4h', etc.)
        limit (int): Number of candles to fetch (max 1000)

    Returns:
        pd.DataFrame: DataFrame with date, open, high, low, close, volume
    """

    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "limit": limit
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])

    # Process relevant columns
    df["date"] = pd.to_datetime(df["open_time"], unit="ms").dt.date
    df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
    df["symbol"] = symbol
    df = df[["date", "symbol", "open", "high", "low", "close", "volume"]]
    return df

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Given a OHLCV DataFrame with 'close' column, compute:
    - SMA20, SMA50, SMA200
    - RSI
    - MACD (macd line only)
    - Daily % change
    Returns new DataFrame with added columns.
    """

    df = df.copy()

    # Simple Moving Averages
    df['sma_20'] = ta.sma(df['close'], length=20).round(2)
    df['sma_50'] = ta.sma(df['close'], length=50).round(2)
    df['sma_200'] = ta.sma(df['close'], length=200).round(2)

    # RSI
    df['rsi'] = ta.rsi(df['close'], length=14).round(2)

    # MACD
    macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
    df['macd'] = macd['MACD_12_26_9'].round(2)

    # Daily percentage change
    df['pct_change'] = (df['close'].pct_change() * 100).round(2)


    return df

def main():
    
    symbol_matching = {
        "BTCUSDT": "BTC",
        "ETHUSDT": "ETH",
        "BNBUSDT": "BNB",
        "XRPUSDT": "XRP",
        "ADAUSDT": "ADA",
        "SOLUSDT": "SOL",
    }

    df_raw = pd.concat([
        calculate_indicators(fetch_ohlcv_binance(symbol=symb))
        for symb in symbol_matching.keys()
        ], ignore_index=True)

    df_raw["symbol"] = df_raw["symbol"].map(symbol_matching)
    df_raw = df_raw.sort_values(by=["date", "symbol"]).reset_index(drop=True)

    if df_raw.empty:
        print("No data fetched from Binance.")
    else:
        print(f"Fetched {len(df_raw)} rows of raw data.")

    append_unique_rows(df_raw, "data/btc_technical.csv", subset_cols=["date", "symbol"])


if __name__ == "__main__":
    main()
