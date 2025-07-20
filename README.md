# 📈 DipSignal

DipSignal is a data-powered crypto signal engine that combines technical indicators, sentiment analysis, and local LLM inference to analyze the news and generate daily buy/sell/hold signals for Bitcoin and Ethereum.

---

![Screenshot 1](https://raw.githubusercontent.com/amrelsawalhi/DipSignal/master/DashboardScreenshot.png)
![Screenshot 2](https://raw.githubusercontent.com/amrelsawalhi/DipSignal/master/DashboardScreenshot2.png)

---

🚀 Overview

- DipSignal is a personal crypto analytics pipeline that aggregates technical indicators, macroeconomic data, and sentiment signals to generate daily trading recommendations for major coins using a local LLaMA 3.1 model. 
- It ingests data, enriches it with features, and uses AI to simulate reasoning and generate actionable buy/hold/sell signals.

---

⚙️ Features

- ✅ Binance price data ingestion (OHLCV)
- ✅ Technical indicator calculation (SMA20/50/200, RSI, MACD, etc.)
- ✅ Macroeconomic data integration (CPI, DXY, SP500, US interest rates)
- ✅ Fear and Greed Index (FGI) fetching and merging
- ✅ LLaMA 3.1 (local via Ollama) decision engine
- ✅ Coin-specific recommendation CSV outputs
- ✅ Automated with GitHub Actions (self-hosted runner)
- ✅ Power BI Dashboard for visual insights

---

🗂️ Project Structure
<pre>
DipSignal/
├── data/
│   ├── *_technical.csv                 # Daily OHLCV + indicators per coin (BTC, ETH, SOL, etc.)
│   ├── llama_recommendations_*.csv     # LLaMA daily decisions
│   ├── fgi.csv                         # Fear and Greed Index
│   ├── macro.csv                       # CPI, interest rates, SP500, DXY
│   ├── news_scored.csv / raw_news.csv  # Optional news scoring
├── etl/                                # Data ingestion and feature engineering
│   ├── fetch_binance.py
│   ├── fetch_fgi.py
│   ├── fetch_macro.py
│   ├── news.py
├── llama/                              # LLaMA prompt logic
│   ├── llama_prediction.py             # Prompts model with coin-specific features
│   ├── llama_news.py                   # news sentiment-based LLaMA prompts
├── dipsignal_dashboard.pbix            # Power BI dashboard
├── main_script.py / onetime.py         # Entry points for running the full pipeline
├── requirements.txt
</pre>
---

🧠 How LLaMA is Used

Model: llama3.1:latest
Host: Local inference using Ollama

Prompt Templates:
<pre>
You are a financial assistant LLM that analyzes macroeconomic and technical indicators to generate a decision on {coin}.
You will be given a table with the last 30 days of metrics. Based on the patterns in the data and any signals from technical indicators or macro conditions, give a recommendation on whether to Buy, Hold, or Sell {coin}.

Respond with the following format:
1. Decision: Buy / Hold / Sell
2. Confidence: Float between 0 and 1
3. Rationale: A brief explanation using the data trends.

{table}</pre>

<pre>"You are an expert sentiment analyst. Given the following crypto news articles, "
        "assess each article’s sentiment.\n\n"
        "Respond using this exact format:\n"
        "1. Sentiment: <value> Confidence: <value> Rationale: <reasoning>\n"
        "2. Sentiment: <value> Confidence: <value> Rationale: <reasoning>\n"
        "...\n"
        "Where Sentiment ∈ {extremely negative, slightly negative, neutral, slightly positive, extremely positive}, "
        "Confidence is a float between 0 and 1, and Rationale is a one sentence justification.\n\n"
        "Articles:\n"</pre>

Dependencies: Ollama must be installed and running the LLaMA 3.1 model.

---

⏱️ Update Frequency

- The entire pipeline is automated daily via GitHub Actions using a self-hosted runner.
- This avoids Binance IP bans and allows local LLaMA inference without cloud cost or latency.

---

🎯 Target Audience

- Primary: Personal trading assistant
- Secondary: Open-source community, crypto investors (possible future)

📌 Goals

- Current stage: Minimum Viable Product (MVP)
- Future plan: Expand to cover other asset classes (e.g., commodities, equities, forex)

---

📈 Power BI Dashboard

- Located at: dipsignal_dashboard.pbix
- Visualizes recent signals, price movements, macro correlations, and model behavior

---

🧪 Requirements

Install required Python dependencies:

<pre> pip install -r requirements.txt</pre>

Make sure Ollama is installed and running:

<pre> ollama run llama3.1 </pre>

---

📬 License

MIT License

---

🙌 Acknowledgments

Binance API
Fear & Greed Index from alternative.me
US Macro data from FRED and YahooFinance
LLaMA 3.1 by Meta via Ollama