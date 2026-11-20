# OLA Ride Insights — SQLite + Streamlit + Power BI

An end-to-end analytics starter project for the supplied OLA ride-booking workbook.

## Architecture

`Excel workbook → Python ETL (Pandas) → SQLite database → Streamlit + Power BI`

SQLite is the single source of truth. Streamlit reads it with Python's built-in `sqlite3`.
Power BI can connect through a compatible 64-bit SQLite ODBC driver. SQLite has no
standard native Power BI connector in every installation, so ODBC driver compatibility
must be checked on the machine running Power BI.

## 1. Setup (Windows PowerShell)

```powershell
cd OLA_RIDE_INSIGHTS
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 2. Build the database

The supplied workbook is expected at `data/raw/OLA_DataSet.xlsx`.

```powershell
python src/run_pipeline.py
```

The pipeline:
- finds the most suitable worksheet (prefers `July`);
- standardizes column names;
- preserves the imported source rows in `bookings_raw`;
- creates a cleaned `bookings` table;
- creates SQL views and a run log;
- exports a cleaned CSV and a data-quality report.

It deliberately does not replace missing cancellation reasons with zero or invent values.
Rows are retained; duplicate booking IDs are flagged and excluded from the curated table
only when the ID column is present and duplicates are detected. Review the quality report.

## 3. Run Streamlit

```powershell
streamlit run streamlit_app/app.py
```

## 4. SQLite database

Default path: `data/ola_analytics.db`

Useful tables:
- `bookings_raw` — standardized imported source records
- `bookings` — cleaned, analysis-ready records
- `etl_runs` — pipeline execution metadata

Useful views:
- `vw_booking_status`
- `vw_daily_booking_trend`
- `vw_vehicle_performance`
- `vw_payment_revenue`
- `vw_cancellation_reasons`

## 5. Power BI connection (after pipeline succeeds)

1. Install a trusted, compatible **64-bit SQLite ODBC driver**.
2. Open Power BI Desktop → **Get data** → **ODBC**.
3. Select/configure the SQLite DSN pointing to `data/ola_analytics.db`.
4. Select `bookings` and the `vw_` views.
5. Prefer Import mode initially; refresh after rerunning the ETL pipeline.
6. Validate booking counts and totals against Streamlit/SQLite.

Driver names and DSN setup vary by ODBC driver vendor/version. Do not assume a MySQL ODBC driver will work with SQLite.

## 6. Important data notes

- This workbook describes a limited July 2024 dataset, not a live OLA feed.
- The app detects common column-name variants. If your workbook uses unusual headers,
  review `src/data_utils.py` and add the matching alias.
- "Revenue" in this project means the sum of `booking_value` for successful bookings,
  unless a chart/query explicitly states otherwise.
- Ratings and cancellation reasons are analyzed only where values exist.
- A one-month dataset cannot establish year-over-year trends or causal surge-pricing effects.

## 7. SQL scripts

Open `sql/business_analysis.sql` in DB Browser for SQLite or run the queries in the
Streamlit SQL Playground. Queries use SQLite SQL syntax.

## 8. Rebuild

Close applications using the database, then run `python src/run_pipeline.py` again.
The curated database tables and views are rebuilt from the raw workbook.

## Run Exploratory Data Analysis (EDA)

After the ETL pipeline has completed successfully, run:

```powershell
python src/run_eda.py
```

The script reads the curated `bookings` table from `data/ola_analytics.db` and creates:

- `reports/eda/EDA_REPORT.md` — EDA overview and data-quality notes
- `reports/eda/missing_values_summary.csv` — missing values and distinct counts
- `reports/eda/descriptive_statistics.csv` — descriptive statistics
- `reports/eda/booking_status_summary.csv` — booking status distribution
- `reports/eda/outlier_summary.csv` — IQR outlier flags (records are not deleted)
- `reports/eda/charts/` — PNG charts for booking status, daily/hourly trends, vehicle performance, payment methods, successful revenue, ride distance and ratings

The EDA step does not alter the SQLite database. If you change the ETL code or source data, rerun `python src/run_pipeline.py` before rerunning EDA.
