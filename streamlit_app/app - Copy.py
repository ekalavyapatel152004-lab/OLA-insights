from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from streamlit_app.database import get_connection, read_query, DB_PATH

st.set_page_config(page_title="OLA Ride Insights", page_icon="🚕", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {
    background: rgba(120,120,120,.08);
    padding: 14px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

st.title("🚕 OLA Ride Insights")
st.caption("End-to-end ride booking analytics | SQLite-powered business intelligence")

# Check and load the SQLite database.
if not DB_PATH.exists():
    st.error(f"Database not found: {DB_PATH}. Run the ETL pipeline first.")
    st.stop()

try:
    with get_connection() as conn:
        table_check = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='bookings'",
            conn,
        )
        if table_check.empty:
            st.error("The bookings table is missing from the database.")
            st.stop()
        cols = [row[1] for row in conn.execute("PRAGMA table_info(bookings)").fetchall()]

    df = read_query("SELECT * FROM bookings")
except Exception as exc:
    st.error(f"Could not read the bookings database: {exc}")
    st.stop()

if df.empty:
    st.warning("The bookings table contains no records.")
    st.stop()

def has(column):
    return column in df.columns

# Filters. Missing values are included as "Unknown" so they are not
# silently removed from the KPI calculations.
st.sidebar.header("Filters")
filtered = df.copy()

def apply_category_filter(data, column, label):
    if column not in data.columns:
        return data

    helper = data[column].astype("string").fillna("Unknown").str.strip()
    helper = helper.replace("", "Unknown")
    options = sorted(helper.unique().tolist())
    selected = st.sidebar.multiselect(label, options, default=options, key=f"filter_{column}")

    if selected:
        data = data.loc[helper.isin(selected)].copy()
    return data

filtered = apply_category_filter(filtered, "booking_status", "Booking status")
filtered = apply_category_filter(filtered, "vehicle_type", "Vehicle type")
filtered = apply_category_filter(filtered, "payment_method", "Payment method")

# Executive overview.
st.subheader("Executive overview")
total = len(filtered)

if has("is_successful"):
    successful = int(pd.to_numeric(filtered["is_successful"], errors="coerce").fillna(0).sum())
else:
    successful = 0

# Count cancellation records from the actual status text. This handles
# both "Canceled" and "Cancelled", irrespective of capitalization.
if has("booking_status"):
    status_text = filtered["booking_status"].astype("string").fillna("")
    cancelled = int(status_text.str.contains("cancel", case=False, regex=False, na=False).sum())
elif has("is_cancelled"):
    cancelled = int(pd.to_numeric(filtered["is_cancelled"], errors="coerce").fillna(0).sum())
else:
    cancelled = 0

if has("is_successful") and has("booking_value"):
    success_mask = pd.to_numeric(filtered["is_successful"], errors="coerce").fillna(0).eq(1)
    revenue = float(
        pd.to_numeric(filtered.loc[success_mask, "booking_value"], errors="coerce").fillna(0).sum()
    )
else:
    revenue = 0.0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total bookings", f"{total:,}")
c2.metric("Successful bookings", f"{successful:,}")
c3.metric("Cancelled bookings", f"{cancelled:,}")
c4.metric("Successful booking value", f"₹{revenue:,.2f}")

# Booking status and vehicle charts.
left, right = st.columns(2)
if has("booking_status"):
    status_df = (
        filtered["booking_status"].fillna("Unknown").value_counts()
        .rename_axis("status").reset_index(name="bookings")
    )
    left.plotly_chart(
        px.pie(status_df, names="status", values="bookings", hole=0.45,
               title="Booking status breakdown"),
        use_container_width=True,
    )

if has("vehicle_type"):
    vehicle_df = filtered.groupby("vehicle_type", dropna=False).size().reset_index(name="bookings")
    right.plotly_chart(
        px.bar(vehicle_df, x="vehicle_type", y="bookings", title="Bookings by vehicle type"),
        use_container_width=True,
    )

# Revenue and ride performance.
st.subheader("Revenue and ride performance")
left, right = st.columns(2)

if has("payment_method") and has("booking_value"):
    rev = filtered.copy()
    if has("is_successful"):
        success_mask = pd.to_numeric(rev["is_successful"], errors="coerce").fillna(0).eq(1)
        rev = rev.loc[success_mask].copy()
    rev["payment_method"] = rev["payment_method"].fillna("Unknown")
    rev = rev.groupby("payment_method", dropna=False)["booking_value"].sum().reset_index()
    left.plotly_chart(
        px.bar(rev, x="payment_method", y="booking_value",
               title="Successful booking value by payment method"),
        use_container_width=True,
    )

if has("ride_distance") and has("vehicle_type"):
    dist = filtered.groupby("vehicle_type", dropna=False)["ride_distance"].mean().reset_index()
    right.plotly_chart(
        px.bar(dist, x="vehicle_type", y="ride_distance",
               title="Average ride distance by vehicle"),
        use_container_width=True,
    )

# Booking explorer.
st.subheader("Booking explorer")
st.caption(f"Showing {len(filtered):,} of {len(df):,} records")
st.dataframe(filtered, use_container_width=True, hide_index=True)

# Read-only SQL playground.
st.subheader("SQL playground")
st.caption("Read-only SQL against the curated bookings table and project views.")

examples = {
    "Booking status summary": (
        "SELECT booking_status, COUNT(*) AS bookings FROM bookings "
        "GROUP BY booking_status ORDER BY bookings DESC;"
    ),
    "Average distance by vehicle": (
        "SELECT vehicle_type, ROUND(AVG(ride_distance), 2) AS avg_distance "
        "FROM bookings GROUP BY vehicle_type ORDER BY avg_distance DESC;"
    ),
    "Successful booking value": (
        "SELECT ROUND(SUM(booking_value), 2) AS successful_value "
        "FROM bookings WHERE is_successful = 1;"
    ),
    "Top 5 customers": (
        "SELECT customer_id, COUNT(*) AS bookings FROM bookings "
        "GROUP BY customer_id ORDER BY bookings DESC LIMIT 5;"
    ),
    "Cancellation status counts": (
        "SELECT booking_status, COUNT(*) AS bookings FROM bookings "
        "WHERE LOWER(booking_status) LIKE '%cancel%' "
        "GROUP BY booking_status ORDER BY bookings DESC;"
    ),
}

choice = st.selectbox("Choose an example query", list(examples))
query = st.text_area("SQL query", value=examples[choice], height=130)

if st.button("Run SQL query", type="primary"):
    cleaned = query.strip().rstrip(";").strip()
    lowered = cleaned.lower()
    blocked = {"insert", "update", "delete", "drop", "alter", "create", "replace"}
    if not lowered.startswith("select"):
        st.error("Only a read-only SELECT statement is allowed.")
    elif ";" in cleaned:
        st.error("Please run only one SQL statement at a time.")
    elif blocked.intersection(lowered.split()):
        st.error("Only read-only SELECT queries are allowed.")
    else:
        try:
            result = read_query(cleaned)
            st.dataframe(result, use_container_width=True, hide_index=True)
            st.success(f"{len(result):,} rows returned.")
        except Exception as exc:
            st.error(f"Query error: {exc}")

st.sidebar.divider()
st.sidebar.caption("Database: ola_analytics.db")
st.sidebar.caption("Source period: July 2024 workbook")
