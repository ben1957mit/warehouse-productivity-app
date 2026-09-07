import streamlit as st
import pandas as pd

st.set_page_config(page_title="Warehouse Productivity Dashboard", layout="wide")

st.title("Warehouse Productivity Dashboard")
st.write("Upload your 30-day CSV dataset to begin.")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:

    # Load CSV safely
    df = pd.read_csv(uploaded_file, dtype=str)

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()

    # Fix Excel BOM issues
    if "ï»¿timestamp" in df.columns:
        df.rename(columns={"ï»¿timestamp": "timestamp"}, inplace=True)

    # Ensure timestamp column exists
    if "timestamp" not in df.columns:
        st.error("Your CSV is missing a 'timestamp' column. Please check your header row.")
        st.stop()

    # Convert timestamp safely
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Warn if any timestamps failed
    bad_rows = df[df["timestamp"].isna()]
    if len(bad_rows) > 0:
        st.warning(f"{len(bad_rows)} rows had invalid timestamps and were skipped.")

    # Convert numeric columns safely
    numeric_cols = ["units", "lines", "workers", "errors", "cycle_time"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Create fatigue score
    df["fatigue_score"] = (
        (df["cycle_time"] / df["cycle_time"].max()) * 60
        + (1 - (df["units"] / df["units"].max())) * 40
    )

    # Display dataset
    st.subheader("Raw Dataset")
    st.dataframe(df, use_container_width=True)

    # Summary stats
    st.subheader("Summary Statistics")
    st.write(df.describe())

    # Preview
    st.subheader("Preview (first 10 rows)")
    st.write(df.head(10))

    # Fatigue trend chart
    st.subheader("Fatigue Trend Over Time")
    fatigue_chart = df[["timestamp", "fatigue_score"]].set_index("timestamp")
    st.line_chart(fatigue_chart)

    # Daily fatigue averages
    st.subheader("Daily Fatigue Averages")
    daily_fatigue = df.groupby(df["timestamp"].dt.date)["fatigue_score"].mean()
    st.bar_chart(daily_fatigue)
