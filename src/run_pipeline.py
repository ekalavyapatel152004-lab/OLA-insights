"""Run the Excel → clean data → SQLite ETL pipeline."""
from pathlib import Path
import sys, sqlite3, logging
from datetime import datetime, timezone
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data_utils import find_best_sheet, prepare_bookings, quality_report

RAW = ROOT / "data" / "raw" / "OLA_DataSet.xlsx"
PROCESSED = ROOT / "data" / "processed"
DB = ROOT / "data" / "ola_analytics.db"
LOG_DIR = ROOT / "logs"
PROCESSED.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "etl.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def main():
    if not RAW.exists():
        raise FileNotFoundError(f"Workbook not found: {RAW}")
    sheet = find_best_sheet(RAW)
    logging.info("Reading workbook sheet: %s", sheet)
    source = pd.read_excel(RAW, sheet_name=sheet)
    raw = source.copy()
    clean = prepare_bookings(source)

    duplicate_count = 0
    if "booking_id" in clean.columns:
        duplicate_count = int(clean["booking_id"].duplicated(keep="first").sum())
        # Preserve all records in raw table; keep first duplicate in curated table.
        clean = clean.drop_duplicates(subset=["booking_id"], keep="first")

    report = quality_report(prepare_bookings(raw))
    report.to_csv(PROCESSED / "data_quality_report.csv", index=False)
    clean.to_csv(PROCESSED / "ola_cleaned.csv", index=False)

    with sqlite3.connect(DB) as conn:
        raw_std = prepare_bookings(raw)
        raw_std.to_sql("bookings_raw", conn, if_exists="replace", index=False)
        clean.to_sql("bookings", conn, if_exists="replace", index=False)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS etl_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_timestamp_utc TEXT NOT NULL,
                source_file TEXT NOT NULL,
                source_sheet TEXT NOT NULL,
                source_rows INTEGER NOT NULL,
                curated_rows INTEGER NOT NULL,
                duplicate_booking_ids INTEGER NOT NULL,
                status TEXT NOT NULL
            )
        """)
        conn.execute("""
            INSERT INTO etl_runs
            (run_timestamp_utc, source_file, source_sheet, source_rows,
             curated_rows, duplicate_booking_ids, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(), RAW.name, sheet,
            len(raw), len(clean), duplicate_count, "SUCCESS"
        ))
        conn.executescript((ROOT / "sql" / "create_views.sql").read_text(encoding="utf-8"))
        conn.commit()

    print("ETL completed successfully")
    print(f"Source sheet: {sheet}")
    print(f"Source rows: {len(raw):,}")
    print(f"Curated rows: {len(clean):,}")
    print(f"Duplicate booking IDs removed from curated table: {duplicate_count:,}")
    print(f"Database: {DB}")
    print(f"Quality report: {PROCESSED / 'data_quality_report.csv'}")
    print("Available columns:", ", ".join(clean.columns))

if __name__ == "__main__":
    main()
