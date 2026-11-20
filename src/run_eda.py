"""Create a reproducible EDA report and chart pack from the ETL SQLite database."""
from pathlib import Path
import sqlite3
import sys
import textwrap

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "ola_analytics.db"
OUT = ROOT / "reports" / "eda"
CHARTS = OUT / "charts"


def save_bar(series, title, xlabel, ylabel, filename, horizontal=False, rotate=0):
    if series.empty:
        return
    fig, ax = plt.subplots(figsize=(10, 5.5))
    if horizontal:
        series.sort_values().plot(kind="barh", ax=ax)
    else:
        series.plot(kind="bar", ax=ax)
        if rotate:
            ax.tick_params(axis="x", labelrotation=rotate)
    ax.set_title(title, fontsize=14, weight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=.25)
    fig.tight_layout()
    fig.savefig(CHARTS / filename, dpi=160, bbox_inches="tight")
    plt.close(fig)


def save_hist(values, title, xlabel, filename, bins=35):
    values = pd.to_numeric(values, errors="coerce").dropna()
    if values.empty:
        return
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(values, bins=bins, edgecolor="white")
    ax.set_title(title, fontsize=14, weight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Number of bookings")
    ax.grid(axis="y", alpha=.25)
    fig.tight_layout()
    fig.savefig(CHARTS / filename, dpi=160, bbox_inches="tight")
    plt.close(fig)


def main():
    if not DB.exists():
        raise FileNotFoundError(f"Database not found: {DB}. Run `python src/run_pipeline.py` first.")
    OUT.mkdir(parents=True, exist_ok=True)
    CHARTS.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB) as conn:
        df = pd.read_sql_query("SELECT * FROM bookings", conn)
    if df.empty:
        raise ValueError("The bookings table is empty. Re-run the ETL pipeline.")

    # Parse dates and ensure numeric measures are numeric for analysis.
    if "booking_datetime" in df:
        df["booking_datetime"] = pd.to_datetime(df["booking_datetime"], errors="coerce")
    elif "date" in df:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    numeric_cols = [c for c in ["booking_value", "ride_distance", "driver_ratings", "customer_rating", "v_tat", "c_tat"] if c in df]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Core data quality outputs.
    quality = pd.DataFrame({
        "column": df.columns,
        "data_type": [str(df[c].dtype) for c in df.columns],
        "missing_count": [int(df[c].isna().sum()) for c in df.columns],
        "missing_percent": [round(float(df[c].isna().mean() * 100), 2) for c in df.columns],
        "distinct_values": [int(df[c].nunique(dropna=True)) for c in df.columns],
    }).sort_values("missing_percent", ascending=False)
    quality.to_csv(OUT / "missing_values_summary.csv", index=False)
    df.describe(include="all").transpose().to_csv(OUT / "descriptive_statistics.csv")

    duplicates = int(df["booking_id"].duplicated().sum()) if "booking_id" in df else 0
    status_counts = df["booking_status"].fillna("Missing").value_counts() if "booking_status" in df else pd.Series(dtype=int)
    status_counts.rename_axis("booking_status").reset_index(name="bookings").to_csv(OUT / "booking_status_summary.csv", index=False)

    # Charts.
    if "booking_status" in df:
        save_bar(status_counts, "Booking status distribution", "Booking status", "Bookings", "01_booking_status.png", rotate=20)
    if "booking_datetime" in df and df["booking_datetime"].notna().any():
        daily = df.dropna(subset=["booking_datetime"]).set_index("booking_datetime").resample("D").size()
        daily.rename("bookings").to_csv(OUT / "daily_booking_trend.csv", header=True)
        fig, ax = plt.subplots(figsize=(11, 5))
        daily.plot(ax=ax, marker="o", linewidth=1.5)
        ax.set_title("Daily booking volume", fontsize=14, weight="bold")
        ax.set_xlabel("Date")
        ax.set_ylabel("Bookings")
        ax.grid(alpha=.25)
        fig.tight_layout(); fig.savefig(CHARTS / "02_daily_booking_trend.png", dpi=160); plt.close(fig)
        if "booking_hour" in df:
            hourly = pd.to_numeric(df["booking_hour"], errors="coerce").dropna().astype(int).value_counts().sort_index()
            hourly.rename("bookings").to_csv(OUT / "hourly_booking_distribution.csv", header=True)
            save_bar(hourly, "Bookings by hour of day", "Hour (24-hour clock)", "Bookings", "03_hourly_bookings.png")

    if "vehicle_type" in df:
        vehicle_counts = df["vehicle_type"].fillna("Missing").value_counts()
        save_bar(vehicle_counts, "Bookings by vehicle type", "Vehicle type", "Bookings", "04_vehicle_bookings.png", rotate=20)
        if "ride_distance" in df:
            vehicle_distance = df.groupby("vehicle_type", dropna=False)["ride_distance"].mean().sort_values(ascending=False)
            vehicle_distance.rename("average_ride_distance_km").to_csv(OUT / "vehicle_average_distance.csv", header=True)
            save_bar(vehicle_distance, "Average ride distance by vehicle", "Vehicle type", "Average distance (km)", "05_vehicle_avg_distance.png", rotate=20)
        if "customer_rating" in df:
            vehicle_rating = df.groupby("vehicle_type")["customer_rating"].mean().sort_values(ascending=False)
            vehicle_rating.rename("average_customer_rating").to_csv(OUT / "vehicle_customer_rating.csv", header=True)
            save_bar(vehicle_rating, "Average customer rating by vehicle", "Vehicle type", "Average customer rating", "06_vehicle_customer_rating.png", rotate=20)

    if "payment_method" in df:
        payment_counts = df["payment_method"].fillna("Not recorded").value_counts()
        save_bar(payment_counts, "Bookings by payment method", "Payment method", "Bookings", "07_payment_methods.png", rotate=20)
        if "booking_value" in df:
            successful = df[df.get("is_successful", pd.Series(0, index=df.index)).eq(1)]
            payment_revenue = successful.groupby("payment_method", dropna=False)["booking_value"].sum().sort_values(ascending=False)
            payment_revenue.rename("successful_booking_value").to_csv(OUT / "successful_revenue_by_payment.csv", header=True)
            save_bar(payment_revenue, "Successful booking value by payment method", "Payment method", "Booking value", "08_revenue_by_payment.png", rotate=20)

    if "booking_value" in df:
        save_hist(df.loc[df.get("is_successful", pd.Series(0, index=df.index)).eq(1), "booking_value"], "Successful booking value distribution", "Booking value", "09_booking_value_distribution.png")
    if "ride_distance" in df:
        save_hist(df["ride_distance"], "Ride distance distribution", "Ride distance (km)", "10_ride_distance_distribution.png")
    if "driver_ratings" in df:
        save_hist(df["driver_ratings"], "Driver rating distribution", "Driver rating", "11_driver_rating_distribution.png", bins=20)
    if "customer_rating" in df:
        save_hist(df["customer_rating"], "Customer rating distribution", "Customer rating", "12_customer_rating_distribution.png", bins=20)

    # Cancellation and incomplete-ride reason frequencies.
    for col, filename, title in [
        ("cancelled_rides_by_customer", "customer_cancellation_flags.csv", "Customer cancellation flags"),
        ("cancelled_rides_by_driver", "driver_cancellation_flags.csv", "Driver cancellation flags"),
        ("incomplete_ride_reason", "incomplete_ride_reasons.csv", "Incomplete ride reasons"),
    ]:
        if col in df:
            counts = df[col].fillna("Not recorded").value_counts().head(20)
            counts.rename_axis(col).reset_index(name="bookings").to_csv(OUT / filename, index=False)
            if col == "incomplete_ride_reason":
                save_bar(counts, title, "Reason", "Bookings", "13_incomplete_ride_reasons.png", horizontal=True)

    # Outlier flags are descriptive only; rows are not removed.
    outlier_rows = []
    for col in ["booking_value", "ride_distance", "driver_ratings", "customer_rating", "v_tat", "c_tat"]:
        if col not in df:
            continue
        x = df[col].dropna()
        if x.empty:
            continue
        q1, q3 = x.quantile([.25, .75]); iqr = q3 - q1
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outlier_rows.append({"column": col, "q1": q1, "q3": q3, "iqr_lower_bound": low,
                             "iqr_upper_bound": high, "outlier_count": int(((x < low) | (x > high)).sum()),
                             "outlier_percent": round(float(((x < low) | (x > high)).mean() * 100), 2)})
    pd.DataFrame(outlier_rows).to_csv(OUT / "outlier_summary.csv", index=False)

    # Compact factual narrative generated from the dataset.
    total = len(df)
    success_count = int(df.get("is_successful", pd.Series(0, index=df.index)).sum())
    cancelled_count = int(df.get("is_cancelled", pd.Series(0, index=df.index)).sum())
    lines = [
        "# OLA Ride Insights — EDA Report", "",
        f"- Curated booking records analysed: **{total:,}**",
        f"- Duplicate booking IDs found in curated table: **{duplicates:,}**",
        f"- Successful bookings (ETL success flag): **{success_count:,} ({success_count / total:.1%})**",
        f"- Cancelled bookings (ETL cancellation flag): **{cancelled_count:,} ({cancelled_count / total:.1%})**",
        f"- Columns analysed: **{len(df.columns)}**", "",
        "## Data quality notes", "",
        f"- Columns with missing values: **{int((quality.missing_count > 0).sum())} of {len(quality)}**.",
        f"- Highest-missingness field: **{quality.iloc[0].column} ({quality.iloc[0].missing_percent:.2f}%)**." if len(quality) else "- No columns found.",
        "- IQR outliers are flagged in `outlier_summary.csv`; they are not automatically deleted.",
        "- Missing payment method values are retained as missing / Not recorded, not guessed.", "",
        "## Key outputs", "",
        "- `missing_values_summary.csv` — missingness and distinct-value profile.",
        "- `descriptive_statistics.csv` — descriptive statistics.",
        "- `booking_status_summary.csv` — booking-status counts.",
        "- `outlier_summary.csv` — IQR-based outlier flags.",
        "- `charts/` — EDA chart pack (PNG).", "",
        "## Interpretation caution", "",
        "Revenue totals in this report use successful bookings only. Do not interpret missing payment methods as a payment category, and validate business definitions before presenting conclusions.",
    ]
    (OUT / "EDA_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("EDA completed successfully")
    print(f"Rows analysed: {total:,}")
    print(f"Successful bookings: {success_count:,}")
    print(f"Cancelled bookings: {cancelled_count:,}")
    print(f"EDA report: {OUT / 'EDA_REPORT.md'}")
    print(f"Charts: {CHARTS}")


if __name__ == "__main__":
    main()
