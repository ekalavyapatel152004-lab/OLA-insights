
from pathlib import Path
import sys

import streamlit as st
import pandas as pd
import plotly.express as px

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from streamlit_app.database import read_query

st.title("Cancellation Analysis")
st.caption("Customer and driver cancellation trends")

try:
    # Overall cancellation count
    summary = read_query("""
        SELECT
            COUNT(*) AS total_cancelled,
            SUM(CASE
                WHEN booking_status = 'Canceled by Customer' THEN 1
                ELSE 0
            END) AS customer_cancelled,
            SUM(CASE
                WHEN booking_status = 'Canceled by Driver' THEN 1
                ELSE 0
            END) AS driver_cancelled
        FROM bookings
        WHERE is_cancelled = 1
    """)

    if summary.empty:
        st.warning("No cancellation records found.")
        st.stop()

    total = int(summary.iloc[0]["total_cancelled"] or 0)
    customer = int(summary.iloc[0]["customer_cancelled"] or 0)
    driver = int(summary.iloc[0]["driver_cancelled"] or 0)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Cancelled", f"{total:,}")
    c2.metric("Cancelled by Customer", f"{customer:,}")
    c3.metric("Cancelled by Driver", f"{driver:,}")

    st.divider()

    # Cancellation status breakdown
    status_df = pd.DataFrame({
        "Cancelled By": ["Customer", "Driver"],
        "Bookings": [customer, driver]
    })

    left, right = st.columns(2)

    left.plotly_chart(
        px.pie(
            status_df,
            names="Cancelled By",
            values="Bookings",
            hole=0.45,
            title="Customer vs Driver Cancellations"
        ),
        use_container_width=True
    )

    # Read actual cancellation reason columns
    reasons = read_query("""
        SELECT
            'Customer' AS cancelled_by,
            TRIM(CAST(cancelled_rides_by_customer AS TEXT)) AS reason,
            COUNT(*) AS booking_count
        FROM bookings
        WHERE is_cancelled = 1
          AND cancelled_rides_by_customer IS NOT NULL
          AND TRIM(CAST(cancelled_rides_by_customer AS TEXT)) <> ''
        GROUP BY TRIM(CAST(cancelled_rides_by_customer AS TEXT))

        UNION ALL

        SELECT
            'Driver' AS cancelled_by,
            TRIM(CAST(cancelled_rides_by_driver AS TEXT)) AS reason,
            COUNT(*) AS booking_count
        FROM bookings
        WHERE is_cancelled = 1
          AND cancelled_rides_by_driver IS NOT NULL
          AND TRIM(CAST(cancelled_rides_by_driver AS TEXT)) <> ''
        GROUP BY TRIM(CAST(cancelled_rides_by_driver AS TEXT))

        ORDER BY booking_count DESC
    """)

    if not reasons.empty:
        right.plotly_chart(
            px.bar(
                reasons,
                x="cancelled_by",
                y="booking_count",
                color="reason",
                barmode="group",
                title="Cancellation Reasons"
            ),
            use_container_width=True
        )

        st.subheader("Cancellation Reasons Details")
        st.dataframe(reasons, use_container_width=True, hide_index=True)
    else:
        right.info("No populated cancellation reasons were found.")

    # Cancellation counts by booking status
    st.subheader("Cancellation Status Summary")

    status_detail = read_query("""
        SELECT
            booking_status,
            COUNT(*) AS total_bookings
        FROM bookings
        WHERE is_cancelled = 1
        GROUP BY booking_status
        ORDER BY total_bookings DESC
    """)

    st.dataframe(status_detail, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Cancellation analysis error: {e}")
