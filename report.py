# report.py
import pandas as pd
from pathlib import Path
from utils import ensure_dirs

DATA_DIR = Path("data")
OUT_DIR = Path("outputs")
SNAPSHOT_FILE = DATA_DIR / "crypto_snapshot.csv"
ensure_dirs(OUT_DIR)

def generate_report():
    if not SNAPSHOT_FILE.exists():
        print("[INFO] Snapshot missing. Run scraper.py first.")
        return
    df = pd.read_csv(SNAPSHOT_FILE)
    if 'price_change_pct' not in df.columns and 'price_change_24h' in df.columns:
        df['price_change_pct'] = df['price_change_24h']
    df['price_change_pct'] = pd.to_numeric(df.get('price_change_pct', 0), errors='coerce').fillna(0.0)
    summary = df[['id','symbol','name','current_price','price_change_pct','market_cap']].copy()
    summary.to_csv(OUT_DIR / "crypto_summary.csv", index=False)
    top_gainers = df.nlargest(10, 'price_change_pct')[['name','price_change_pct']]
    top_losers = df.nsmallest(10, 'price_change_pct')[['name','price_change_pct']]
    top_gainers.to_csv(OUT_DIR / "top_gainers.csv", index=False)
    top_losers.to_csv(OUT_DIR / "top_losers.csv", index=False)
    print("[OK] Reports saved to outputs/")

if __name__ == "__main__":
    generate_report()
