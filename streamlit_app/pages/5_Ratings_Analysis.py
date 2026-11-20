import streamlit as st
import plotly.express as px
from streamlit_app.database import read_query

st.title("Ratings Analysis")
df = read_query("SELECT * FROM bookings")
for col, label in [("customer_rating","Customer ratings"),("driver_ratings","Driver ratings")]:
    if col in df and df[col].notna().any():
        hist = df[col].dropna()
        st.plotly_chart(px.histogram(hist, x=col, nbins=20, title=label), use_container_width=True)
if "vehicle_type" in df and "customer_rating" in df:
    avg = df.groupby("vehicle_type")["customer_rating"].mean().reset_index()
    st.plotly_chart(px.bar(avg, x="vehicle_type", y="customer_rating", title="Average customer rating by vehicle"), use_container_width=True)
