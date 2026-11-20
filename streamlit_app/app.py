from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from streamlit_app.database import get_connection, read_query, DB_PATH

st.set_page_config(page_title="OLA Ride Insights", page_icon="🚕", layout="wide")

# ---------------------------------------------------------------------------
# Visual theme (styling only - no data or logic is touched by this block)
# ---------------------------------------------------------------------------
INK = "#0F1B2D"
TEAL = "#12805C"
LIME = "#C6F135"
PALETTE = ["#12805C", "#0F1B2D", "#9BC91B", "#F2A900", "#3B82F6", "#8A94A6"]

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Sora:wght@600;700;800&display=swap');

:root {
    --ink: #0F1B2D;
    --ink-2: #1B2D47;
    --teal: #12805C;
    --lime: #C6F135;
    --mist: #F2F6F3;
    --line: rgba(15, 27, 45, .10);
}

html, body, [class*="css"], .stApp {
    font-family: 'Manrope', sans-serif;
    color: var(--ink);
}

/* Page background: soft city-map grid over a pale green-grey wash */
.stApp {
    background:
        linear-gradient(rgba(15,27,45,.035) 1px, transparent 1px) 0 0 / 48px 48px,
        linear-gradient(90deg, rgba(15,27,45,.035) 1px, transparent 1px) 0 0 / 48px 48px,
        linear-gradient(180deg, #E9F1EC 0%, #F6F9F7 38%, #EEF3F0 100%);
    background-attachment: fixed;
}

header[data-testid="stHeader"] {background: transparent;}
#MainMenu, footer {visibility: hidden;}

.block-container {
    max-width: 1280px;
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}

/* Hero banner */
.hero {
    position: relative;
    overflow: hidden;
    background:
        linear-gradient(rgba(255,255,255,.05) 1px, transparent 1px) 0 0 / 36px 36px,
        linear-gradient(90deg, rgba(255,255,255,.05) 1px, transparent 1px) 0 0 / 36px 36px,
        linear-gradient(125deg, #0F1B2D 0%, #17304B 60%, #12805C 135%);
    border-radius: 22px;
    padding: 38px 42px 34px 42px;
    margin-bottom: 26px;
    box-shadow: 0 18px 40px -18px rgba(15,27,45,.55);
}
.hero::after {
    content: "";
    position: absolute;
    left: 0; right: 0; bottom: 0;
    height: 6px;
    background: repeating-linear-gradient(90deg, var(--lime) 0 38px, transparent 38px 56px);
}
.hero h1 {
    font-family: 'Sora', sans-serif;
    font-weight: 800;
    font-size: 2.6rem;
    letter-spacing: -0.02em;
    color: #FFFFFF;
    margin: 0 0 8px 0;
    padding: 0;
}
.hero p {
    color: rgba(255,255,255,.78);
    font-size: 1.05rem;
    margin: 0 0 18px 0;
    max-width: 760px;
}
.hero .chip {
    display: inline-block;
    padding: 6px 14px;
    margin-right: 8px;
    border-radius: 999px;
    font-size: .82rem;
    font-weight: 600;
    color: var(--ink);
    background: var(--lime);
}
.hero .chip.ghost {
    color: #fff;
    background: rgba(255,255,255,.12);
    border: 1px solid rgba(255,255,255,.22);
}

/* Section headings */
h3, [data-testid="stHeading"] h3 {
    font-family: 'Sora', sans-serif;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: var(--ink);
    border-left: 6px solid var(--lime);
    padding-left: 12px !important;
    margin-top: 1.4rem;
}
[data-testid="stCaptionContainer"] {color: #55637A;}

/* KPI cards */
[data-testid="stMetric"] {
    background: #FFFFFF;
    padding: 18px 20px;
    border-radius: 16px;
    border: 1px solid var(--line);
    border-top: 5px solid var(--teal);
    box-shadow: 0 10px 24px -16px rgba(15,27,45,.35);
}
[data-testid="stMetricLabel"] p {
    font-weight: 600;
    color: #55637A;
}
[data-testid="stMetricValue"] {
    font-family: 'Sora', sans-serif;
    font-weight: 700;
    color: var(--ink);
}

/* Chart cards */
div[data-testid="stPlotlyChart"] {
    background: #FFFFFF;
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 8px 8px 2px 8px;
    box-shadow: 0 10px 24px -16px rgba(15,27,45,.35);
}

/* Tables */
div[data-testid="stDataFrame"] {
    background: #FFFFFF;
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 4px;
    box-shadow: 0 10px 24px -16px rgba(15,27,45,.35);
    overflow: hidden;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F1B2D 0%, #17304B 100%);
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: #E8EEF5;
}
[data-testid="stSidebar"] h2 {
    font-family: 'Sora', sans-serif;
    border-left: 6px solid var(--lime);
    padding-left: 10px;
}
[data-testid="stSidebar"] span[data-baseweb="tag"] {
    background-color: var(--lime);
}
[data-testid="stSidebar"] span[data-baseweb="tag"] span {
    color: var(--ink);
    font-weight: 600;
}
[data-testid="stSidebar"] hr {border-color: rgba(255,255,255,.15);}

/* Inputs */
div[data-baseweb="select"] > div,
.stTextArea textarea {
    border-radius: 12px;
}
.stTextArea textarea {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    background: #FFFFFF;
    color: var(--ink);
    border: 1px solid var(--line);
}

/* Buttons */
.stButton > button {
    border-radius: 12px;
    font-weight: 700;
    padding: .55rem 1.4rem;
    border: 1px solid var(--ink);
    transition: transform .12s ease, box-shadow .12s ease;
}
.stButton > button[kind="primary"] {
    background: var(--lime);
    color: var(--ink);
    border-color: var(--lime);
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 18px -10px rgba(15,27,45,.6);
}
.stButton > button:focus-visible {outline: 3px solid var(--teal);}

/* Footer strip */
.site-footer {
    margin-top: 2.2rem;
    padding: 16px 22px;
    border-radius: 14px;
    background: var(--ink);
    color: rgba(255,255,255,.75);
    font-size: .88rem;
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
}
.site-footer b {color: var(--lime);}

@media (max-width: 720px) {
    .hero {padding: 26px 22px 28px 22px;}
    .hero h1 {font-size: 1.8rem;}
}
</style>
""",
    unsafe_allow_html=True,
)


def style_fig(fig):
    """Apply the site look to a Plotly figure (layout only, data unchanged)."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=PALETTE,
        font=dict(family="Manrope, sans-serif", color=INK),
        title=dict(font=dict(family="Sora, sans-serif", size=17, color=INK)),
        margin=dict(l=18, r=18, t=60, b=18),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(showgrid=False, linecolor="rgba(15,27,45,.25)")
    fig.update_yaxes(gridcolor="rgba(15,27,45,.08)", zeroline=False)
    return fig


# Hero banner (same title and caption as before).
st.markdown(
    """
<div class="hero">
    <h1>🚕 OLA Ride Insights</h1>
    <p>End-to-end ride booking analytics | SQLite-powered business intelligence</p>
    <span class="chip">SQLite database</span>
    <span class="chip ghost">Source period: July 2024 workbook</span>
</div>
""",
    unsafe_allow_html=True,
)

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
        style_fig(px.pie(status_df, names="status", values="bookings", hole=0.45,
                         title="Booking status breakdown")),
        use_container_width=True,
    )

if has("vehicle_type"):
    vehicle_df = filtered.groupby("vehicle_type", dropna=False).size().reset_index(name="bookings")
    right.plotly_chart(
        style_fig(px.bar(vehicle_df, x="vehicle_type", y="bookings", title="Bookings by vehicle type")),
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
        style_fig(px.bar(rev, x="payment_method", y="booking_value",
                         title="Successful booking value by payment method")),
        use_container_width=True,
    )

if has("ride_distance") and has("vehicle_type"):
    dist = filtered.groupby("vehicle_type", dropna=False)["ride_distance"].mean().reset_index()
    right.plotly_chart(
        style_fig(px.bar(dist, x="vehicle_type", y="ride_distance",
                         title="Average ride distance by vehicle")),
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

st.markdown(
    """
<div class="site-footer">
    <span><b>OLA Ride Insights</b> &nbsp;|&nbsp; Ride booking analytics</span>
    <span>Database: ola_analytics.db &nbsp;|&nbsp; Source period: July 2024 workbook</span>
</div>
""",
    unsafe_allow_html=True,
)