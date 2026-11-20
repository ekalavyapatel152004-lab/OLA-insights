from pathlib import Path
import sqlite3
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "ola_analytics.db"
EXPORT_DIR = PROJECT_ROOT / "data" / "powerbi"
CSV_PATH = EXPORT_DIR / "ola_bookings.csv"


def main():
    if not DB_PATH.exists():
        print(f"ERROR: Database not found: {DB_PATH}")
        print("Run this script from your OLA project after confirming the database exists.")
        sys.exit(1)

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        table_check = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='bookings'",
            conn,
        )
        if table_check.empty:
            print("ERROR: The SQLite database does not contain a 'bookings' table.")
            sys.exit(1)

        df = pd.read_sql_query("SELECT * FROM bookings", conn)

    if df.empty:
        print("ERROR: The bookings table is empty.")
        sys.exit(1)

    # Keep the source data intact; only normalize date/time text for Power BI import.
    for column in ("date", "booking_datetime"):
        if column in df.columns:
            parsed = pd.to_datetime(df[column], errors="coerce")
            if parsed.notna().any():
                df[column] = parsed.dt.strftime("%Y-%m-%d %H:%M:%S").fillna("")

    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

    print("\nPOWER BI DATA EXPORT COMPLETED")
    print("--------------------------------")
    print(f"Database : {DB_PATH}")
    print(f"CSV file : {CSV_PATH}")
    print(f"Rows     : {len(df):,}")
    print(f"Columns  : {len(df.columns):,}")

    if "booking_status" in df.columns:
        print("\nBooking status counts:")
        print(df["booking_status"].fillna("Unknown").value_counts(dropna=False).to_string())

    if "is_cancelled" in df.columns:
        print(
            "\nRows flagged is_cancelled = 1:",
            int(pd.to_numeric(df["is_cancelled"], errors="coerce").fillna(0).sum()),
        )

    print("\nNext: In Power BI Desktop, choose Get data > Text/CSV and select:")
    print(CSV_PATH)


if __name__ == "__main__":
    main()
