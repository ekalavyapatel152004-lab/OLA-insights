import streamlit as st
import plotly.express as px
from streamlit_app.database import read_query

st.title("Vehicle Performance")
try:
    df = read_query("SELECT * FROM vw_vehicle_performance")
    st.dataframe(df, use_container_width=True, hide_index=True)
    if not df.empty:
        st.plotly_chart(px.bar(df, x="vehicle_type", y="total_bookings", title="Bookings by vehicle type"), use_container_width=True)
except Exception as e:
    st.info(f"Vehicle performance view is not available: {e}")
