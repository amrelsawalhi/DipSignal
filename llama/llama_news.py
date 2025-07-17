import pandas as pd
import requests
import time
import os

BATCH_SIZE = 10
RAW_FILE = "data/raw_news.csv"
SCORED_FILE = "data/news_scored.csv"

def build_batched_prompt(batch):
    prompt = (
        "You are an expert sentiment analyst. Given the following crypto news articles, "
        "assess each article’s sentiment.\n\n"
        "Respond using this exact format:\n"
        "1. Sentiment: <value> Confidence: <value> Rationale: <reasoning>\n"
        "2. Sentiment: <value> Confidence: <value> Rationale: <reasoning>\n"
        "...\n"
        "Where Sentiment ∈ {extremely negative, slightly negative, neutral, slightly positive, extremely positive}, "
        "Confidence is a float between 0 and 1, and Rationale is a one sentence justification.\n\n"
        "Articles:\n"
    )
    for i, row in enumerate(batch.itertuples(), start=1):
        prompt += f"{i}. Title: {row.title}\n   Summary: {row.summary}\n"
    return prompt

def parse_batched_response(response_text, batch_size):
    lines = response_text.strip().splitlines()
    results = []

    for i in range(1, batch_size + 1):
        line = next((l for l in lines if l.startswith(f"{i}.")), None)
        if line:
            try:
                sentiment = line.split("Sentiment:")[1].split("Confidence:")[0].strip()
                confidence = line.split("Confidence:")[1].split("Rationale:")[0].strip()
                rationale = line.split("Rationale:")[1].strip()
            except Exception:
                sentiment, confidence, rationale = "parse_error", 0, "parse_error"
        else:
            sentiment, confidence, rationale = "missing", 0, "missing"
        results.append((sentiment, confidence, rationale))
    return results

def get_batch_sentiment(batch):
    prompt = build_batched_prompt(batch)
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.1",
                "prompt": prompt,
                "stream": False
            }
        )
        if response.status_code == 200:
            return parse_batched_response(response.json()["response"], len(batch))
        else:
            return [("error", 0, "http_error")] * len(batch)
    except Exception:
        return [("exception", 0, "exception_thrown")] * len(batch)

def process_batches():
    if not os.path.exists(RAW_FILE):
        print("No raw_news.csv file found.")
        return
    
    raw_df = pd.read_csv(RAW_FILE)
    if len(raw_df.index) == 0:
        print("raw_news.csv is empty.")
        return

    while not raw_df.empty or len(raw_df.index) > 0:
        batch = raw_df.head(BATCH_SIZE).copy()
        results = get_batch_sentiment(batch)

        batch['sentiment'], batch['confidence'], batch['rationale'] = zip(*results)

        # Append to scored file
        if not os.path.exists(SCORED_FILE):
            batch.to_csv(SCORED_FILE, index=False)
        else:
            batch.to_csv(SCORED_FILE, mode='a', header=False, index=False)

        # Remove processed rows from raw_df and update file
        raw_df = raw_df.iloc[BATCH_SIZE:]
        raw_df.to_csv(RAW_FILE, index=False)

        print(f"Processed batch of {len(batch)} articles.")
        time.sleep(1)

if __name__ == "__main__":
    process_batches()
