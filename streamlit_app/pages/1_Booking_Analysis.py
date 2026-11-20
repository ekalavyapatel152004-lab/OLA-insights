import streamlit as st
import plotly.express as px
from streamlit_app.database import read_query

st.title("Booking Analysis")
try:
    df = read_query("SELECT * FROM bookings")
except Exception as e:
    st.error(str(e)); st.stop()
if "booking_hour" in df:
    h = df.groupby("booking_hour").size().reset_index(name="bookings")
    st.plotly_chart(px.line(h, x="booking_hour", y="bookings", markers=True, title="Bookings by hour"), use_container_width=True)
if "date" in df:
    d = df.groupby("date").size().reset_index(name="bookings")
    st.plotly_chart(px.line(d, x="date", y="bookings", markers=True, title="Daily booking volume"), use_container_width=True)
st.dataframe(df, use_container_width=True, hide_index=True)
