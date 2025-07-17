import pandas as pd
import requests
from datetime import datetime
import os



def append_unique_rows(new_data: pd.DataFrame, csv_path: str, subset_cols=["date"]):
    if "date" not in new_data.columns:
        raise ValueError("new_data must contain a 'date' column")

    # Ensure date is datetime64[ns] and normalized
    new_data["date"] = pd.to_datetime(new_data["date"]).dt.normalize()

    if os.path.exists(csv_path):
        existing_data = pd.read_csv(csv_path)
        existing_data["date"] = pd.to_datetime(existing_data["date"]).dt.normalize()

        combined = pd.concat([existing_data, new_data], ignore_index=True)
        combined = combined.drop_duplicates(subset=subset_cols, keep="first")
    else:
        combined = new_data.drop_duplicates(subset=subset_cols)

    combined.to_csv(csv_path, index=False)

    new_rows = len(combined) - (len(existing_data) if 'existing_data' in locals() else 0)
    print(f"✅ Updated {csv_path} with {new_rows} new row{'s' if new_rows != 1 else ''}")



def main():
    btc_df = pd.read_csv("data/btc_technical.csv")
    fgi_df = pd.read_csv("data/fgi.csv")
    macro_df = pd.read_csv("data/macro.csv")

    # Merge data on date
    merged = btc_df.merge(fgi_df, on="date", how="inner").merge(macro_df, on="date", how="inner")
    merged.rename(columns={
        "open": "btc_open_price",
        "high": "btc_high_price",
        "low": "btc_low_price",
        "close": "btc_close_price",
        "volume": "btc_volume",
        "sma_20": "btc_simple_moving_average_20",
        "sma_50": "btc_simple_moving_average_50",
        "sma_200": "btc_simple_moving_average_200",
        "rsi": "btc_rsi",
        "macd": "btc_macd",
        "pct_change": "btc_pct_change",
        "value": "fear_and_greed_index_value",
        "classification": "fear_and_greed_index_classification",
        "dxy": "dollar_index",
        "cpi": "us_consumer_price_index",
        "sp500": "sp500_index",
        "interest_rate": "us_fund_rate",
    }, inplace=True)

    # Format date
    merged['date'] = pd.to_datetime(merged['date'])
    merged = merged[["date", "btc_close_price", "btc_volume",
                    "btc_simple_moving_average_20", "btc_simple_moving_average_50",
                    "btc_simple_moving_average_200", "btc_rsi", "btc_macd", "btc_pct_change",
                    "fear_and_greed_index_value", "fear_and_greed_index_classification", "dollar_index"
                    ]]
    merged.sort_values("date", inplace=True)

    # Select last 30 entries
    last_30 = merged.tail(30)

    # Convert to markdown-style table
    prompt_table = last_30.to_markdown(index=True)

    prompt = f"""
    You are a financial assistant LLM that analyzes macroeconomic and technical indicators to generate a decision on Bitcoin.
    You will be given a table with the last 30 days of metrics. Based on the patterns in the data and any signals from technical indicators or macro conditions, give a recommendation on whether to Buy, Hold, or Sell Bitcoin.

    Respond with the following format:
    1. Decision: Buy / Hold / Sell
    2. Confidence: Float between 0 and 1
    3. Rationale: A brief explanation using the data trends.

    {prompt_table}
    """

    # Call LLaMA
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.1",
            "prompt": prompt,
            "stream": False
        }
    )

    # Parse response and save to CSV
    if response.status_code == 200:
        output = response.json()["response"]

        # Extract fields from response
        lines = output.strip().splitlines()
        decision = next((line.split(":")[1].strip() for line in lines if "Decision" in line), "")
        confidence = next((line.split(":")[1].strip() for line in lines if "Confidence" in line), "")
        rationale = next((line.split(":")[1].strip() for line in lines if "Rationale" in line), "")

        today = pd.to_datetime(datetime.today().date())

        result_df = pd.DataFrame([{
            "date": today,
            "recommendation": decision,
            "confidence": confidence,
            "rationale": rationale
        }])
        append_unique_rows(result_df, 'data/llama_recommendations.csv', subset_cols=["date"])

    else:
        print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main()