from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "ola_analytics.db"

def get_connection():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"SQLite database not found at {DB_PATH}. Run: python src/run_pipeline.py"
        )
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def read_query(query, params=None):
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params or ())
