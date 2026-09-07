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

    # -----------------------------
    # ⭐ FATIGUE MODULE STARTS HERE
    # -----------------------------

    # Create fatigue score (0 = fresh, 100 = exhausted)
    df["fatigue_score"] = (
        (df["cycle_time"] / df["cycle_time"].max()) * 60
        + (1 - (df["units"] / df["units"].max())) * 40
    )

    # Create fatigue zones
    def fatigue_zone(score):
        if score <= 20:
            return "Fresh (Green)"
        elif score <= 40:
            return "Warming Up (Light Green)"
        elif score <= 60:
            return "Noticeable Fatigue (Yellow)"
        elif score <= 80:
            return "High Fatigue (Orange)"
        else:
            return "Critical Fatigue (Red)"

    df["fatigue_zone"] = df["fatigue_score"].apply(fatigue_zone)

    # -----------------------------
    # ⭐ DISPLAY SECTION
    # -----------------------------

    st.subheader("Raw Dataset With Fatigue Score")
    st.dataframe(df, use_container_width=True)

    st.subheader("Summary Statistics")
    st.write(df.describe())

    st.subheader("Preview (first 10 rows)")
    st.write(df.head(10))

    # ⭐ Fatigue Trend Chart
    st.subheader("Fatigue Trend Over Time")
    fatigue_chart = df[["timestamp", "fatigue_score"]].set_index("timestamp")
    st.line_chart(fatigue_chart)

    # ⭐ Daily Fatigue Averages
    st.subheader("Daily Fatigue Averages")
    daily_fatigue = df.groupby(df["timestamp"].dt.date)["fatigue_score"].mean()
    st.bar_chart(daily_fatigue)

    # ⭐ Fatigue Zone Table
    st.subheader("Fatigue Zones (Color‑Coded Interpretation)")
    zone_table = df[["timestamp", "units", "cycle_time", "fatigue_score", "fatigue_zone"]]
    st.dataframe(zone_table, use_container_width=True)
