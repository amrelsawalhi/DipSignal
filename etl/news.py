import feedparser
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import re

# RSS Feed URLs
FEEDS = {
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "Cointelegraph": "https://cointelegraph.com/rss",
    "Decrypt": "https://decrypt.co/feed"
}

def clean_html(text):
    return BeautifulSoup(text, "html.parser").get_text().strip()

def parse_date(entry):
    if "published_parsed" in entry and entry.published_parsed:
        return datetime(*entry.published_parsed[:3]).strftime("%Y-%m-%d")
    return None

def fetch_feed(source, url):
    parsed = feedparser.parse(url)
    articles = []
    for entry in parsed.entries:
        articles.append({
            "date": parse_date(entry),
            "source": source,
            "title": entry.get("title", "").strip(),
            "summary": clean_html(entry.get("summary", entry.get("description", ""))),
            "url": entry.get("link", "")
        })
    return articles

def fetch_all_news():
    all_data = []
    for source, url in FEEDS.items():
        all_data.extend(fetch_feed(source, url))
    df = pd.DataFrame(all_data)
    df.dropna(subset=["date", "title", "url"], inplace=True)
    df.sort_values("date", ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)
    df = df[
    ~df['summary'].str.contains(r'Degenz Live|DEGENZ|http[s]?://', flags=re.IGNORECASE, na=False)]

    for col in ["sentiment", "confidence", "rationale"]:
        if col not in df.columns:
            df[col] = None

    return df
def append_unique_rows(new_data: pd.DataFrame, csv_path1: str, csv_path2: str = None, subset_cols=["date"]):
    if "date" not in new_data.columns:
        raise ValueError("new_data must contain a 'date' column")

    new_data["date"] = pd.to_datetime(new_data["date"]).dt.date

    # Load already scored (existing) data to filter out duplicates
    if os.path.exists(csv_path1):
        existing_data = pd.read_csv(csv_path1)
        existing_data["date"] = pd.to_datetime(existing_data["date"]).dt.date
    else:
        existing_data = pd.DataFrame(columns=new_data.columns)

    # Keep only rows not in scored data
    merged = pd.merge(
        new_data,
        existing_data[subset_cols].drop_duplicates(),
        on=subset_cols,
        how="left",
        indicator=True
    )
    new_unique = merged[merged["_merge"] == "left_only"].drop(columns="_merge")

    if new_unique.empty:
        print("⚠️ No new rows to append.")
        return

    if csv_path2 is None:
        csv_path2 = csv_path1

    if os.path.exists(csv_path2):
        old_raw = pd.read_csv(csv_path2)
        old_raw["date"] = pd.to_datetime(old_raw["date"]).dt.date
        new_unique = pd.concat([old_raw, new_unique], ignore_index=True)

    new_unique.to_csv(csv_path2, index=False)
    print(f"✅ Appended {len(new_unique)} new rows to {csv_path2}")

def main():
    df_news = fetch_all_news()
    append_unique_rows(df_news, csv_path1='data/news_scored.csv', csv_path2='data/raw_news.csv', subset_cols=['date', 'title', 'source', 'summary', 'url'])

if __name__ == "__main__":
    main()