import pandas as pd
import os
from datetime import datetime

DATA_DIR = "data"
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

SNAPSHOT_FILE = os.path.join(DATA_DIR, "crypto_snapshot.csv")
ALERT_FILE = os.path.join(LOG_DIR, "alerts.csv")
THRESHOLD = 5  # ±5% change

def main():
    if not os.path.exists(SNAPSHOT_FILE):
        print("Snapshot file not found!")
        return

    df = pd.read_csv(SNAPSHOT_FILE)
    df = df[["id","symbol","name","current_price","price_change_24h"]]

    alerts = df[abs(df["price_change_24h"]) >= THRESHOLD].copy()
    alerts["alert_time"] = datetime.utcnow()

    if alerts.empty:
        print("No alerts.")
        return

    alerts.to_csv(ALERT_FILE, index=False)
    print(f"🚨 Alerts Generated: {len(alerts)} rows. Saved to {ALERT_FILE}")

if __name__ == "__main__":
    main()
