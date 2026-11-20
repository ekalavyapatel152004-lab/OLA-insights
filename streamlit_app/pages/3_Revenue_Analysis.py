import streamlit as st
import plotly.express as px
from streamlit_app.database import read_query

st.title("Revenue Analysis")
try:
    df = read_query("SELECT * FROM vw_payment_revenue")
    st.dataframe(df, use_container_width=True, hide_index=True)
    if not df.empty:
        st.plotly_chart(px.bar(df, x="payment_method", y="successful_revenue", title="Successful booking value by payment method"), use_container_width=True)
except Exception as e:
    st.info(f"Revenue view is not available: {e}")
