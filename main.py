import streamlit as st
import pandas as pd

st.set_page_config(page_title="Warehouse Productivity Dashboard", layout="wide")

st.title("Warehouse Productivity Dashboard")
st.write("Upload your 30-day CSV dataset to begin.")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:
    # Load CSV
    df = pd.read_csv(uploaded_file)

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()

    # Fix Excel UTF-8 BOM issues
    if "ï»¿timestamp" in df.columns:
        df.rename(columns={"ï»¿timestamp": "timestamp"}, inplace=True)

    # Convert timestamp safely
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    else:
        st.error("Your CSV is missing a 'timestamp' column. Please check your header row.")
        st.stop()

    # Display dataframe
    st.subheader("Raw Dataset")
    st.dataframe(df, use_container_width=True)

    # Basic stats
    st.subheader("Summary Statistics")
    st.write(df.describe())

    # Show first 10 rows
    st.subheader("Preview (first 10 rows)")
    st.write(df.head(10))
