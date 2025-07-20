import pandas as pd
import requests
from datetime import datetime
import os


def append_unique_rows(new_data: pd.DataFrame, csv_path: str, subset_cols=["date"]):
    if "date" not in new_data.columns:
        raise ValueError("new_data must contain a 'date' column")

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


def make_llama_prompt(merged: pd.DataFrame, coin: str) -> str:
    table = merged.tail(30).to_markdown(index=True)
    prompt = f"""
    You are a financial assistant LLM that analyzes macroeconomic and technical indicators to generate a decision on {coin}.
    You will be given a table with the last 30 days of metrics. Based on the patterns in the data and any signals from technical indicators or macro conditions, give a recommendation on whether to Buy, Hold, or Sell {coin}.

    Respond with the following format:
    1. Decision: Buy / Hold / Sell
    2. Confidence: Float between 0 and 1
    3. Rationale: A brief explanation using the data trends.

    {table}
    """
    return prompt


def main():
    # Load external data once
    fgi_df = pd.read_csv("data/fgi.csv")
    macro_df = pd.read_csv("data/macro.csv")
    fgi_df["date"] = pd.to_datetime(fgi_df["date"])
    macro_df["date"] = pd.to_datetime(macro_df["date"])

    symbol_matching = {
        "BTC": "btc",
        "ETH": "eth",
        "BNB": "bnb",
        "XRP": "xrp",
        "ADA": "ada",
        "SOL": "sol",
    }

    for coin, short in symbol_matching.items():
        technical_path = f"data/{short}_technical.csv"
        if not os.path.exists(technical_path):
            print(f"⚠️ Skipping {coin} — no technical data file found.")
            continue

        tech_df = pd.read_csv(technical_path)
        if tech_df.empty:
            print(f"⚠️ Skipping {coin} — technical file is empty.")
            continue

        tech_df["date"] = pd.to_datetime(tech_df["date"])

        # Merge with external data
        merged = tech_df.merge(fgi_df, on="date", how="inner").merge(macro_df, on="date", how="inner")
        merged.sort_values("date", inplace=True)

        # Rename columns to include coin-specific prefix
        rename_cols = {
            "open": f"{short}_open_price",
            "high": f"{short}_high_price",
            "low": f"{short}_low_price",
            "close": f"{short}_close_price",
            "volume": f"{short}_volume",
            "sma_20": f"{short}_simple_moving_average_20",
            "sma_50": f"{short}_simple_moving_average_50",
            "sma_200": f"{short}_simple_moving_average_200",
            "rsi": f"{short}_rsi",
            "macd": f"{short}_macd",
            "pct_change": f"{short}_pct_change",
            "value": "fear_and_greed_index_value",
            "classification": "fear_and_greed_index_classification",
            "dxy": "dollar_index",
            "cpi": "us_consumer_price_index",
            "sp500": "sp500_index",
            "interest_rate": "us_fund_rate",
        }
        merged.rename(columns=rename_cols, inplace=True)

        # Select relevant columns
        features = [col for col in merged.columns if short in col or "fear" in col or "dollar" in col]
        features = ["date"] + sorted(set(features))
        merged = merged[features]

        # Prepare LLaMA prompt
        prompt = make_llama_prompt(merged, coin)

        # Call LLaMA
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.1",
                "prompt": prompt,
                "stream": False
            }
        )

        if response.status_code == 200:
            output = response.json()["response"]
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

            output_path = f"data/llama_recommendations_{short}.csv"
            append_unique_rows(result_df, output_path, subset_cols=["date"])
        else:
            print(f"❌ LLaMA API error for {coin}: {response.status_code} - {response.text}")


if __name__ == "__main__":
    main()
