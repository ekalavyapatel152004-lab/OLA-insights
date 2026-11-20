"""Basic SQLite validation report."""
from pathlib import Path
import sqlite3
DB = Path(__file__).resolve().parents[1] / "data" / "ola_analytics.db"
with sqlite3.connect(DB) as conn:
    print("Tables/views:")
    for row in conn.execute("SELECT type, name FROM sqlite_master WHERE type IN ('table','view') ORDER BY type,name"):
        print(row)
    print("\nBooking rows:", conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0])
    print("\nColumns:")
    for row in conn.execute("PRAGMA table_info(bookings)"):
        print(row[1], row[2])
