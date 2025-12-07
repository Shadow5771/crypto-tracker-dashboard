# utils.py
import os
from pathlib import Path
import pandas as pd

def ensure_dirs(*dirs):
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def atomic_write_csv(path: str, df: pd.DataFrame):
    """
    Atomically write DataFrame to CSV to avoid partial-file issues.
    """
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False)
    tmp.replace(path)
