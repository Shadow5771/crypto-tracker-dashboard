import requests
import pandas as pd
from datetime import datetime
import os
import logging

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

SNAPSHOT_FILE = os.path.join(DATA_DIR, "crypto_snapshot.csv")
HISTORY_FILE = os.path.join(DATA_DIR, "crypto_history.csv")
TOP_N = 60

def fetch_top_coins():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": TOP_N, "page": 1, "sparkline": False}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()

def main():
    logging.info(f"Requesting CoinGecko (top {TOP_N} coins)...")
    data = fetch_top_coins()
    logging.info(f"Received {len(data)} records")

    df = pd.DataFrame(data)
    df = df[["id","symbol","name","current_price","market_cap","total_volume","price_change_24h"]]
    df["scrape_time"] = datetime.utcnow()

    # Save snapshot
    df.to_csv(SNAPSHOT_FILE, index=False)
    logging.info(f"✅ Saved snapshot: {SNAPSHOT_FILE}")

    # Append to history
    if os.path.exists(HISTORY_FILE):
        df.to_csv(HISTORY_FILE, mode="a", index=False, header=False)
    else:
        df.to_csv(HISTORY_FILE, index=False)
    logging.info(f"✅ Appended to history: {HISTORY_FILE}")

if __name__ == "__main__":
    main()