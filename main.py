import streamlit as st
import pandas as pd

st.set_page_config(page_title="Warehouse Productivity Dashboard", layout="wide")

st.title("Warehouse Productivity Dashboard")
st.write("Upload your 30-day CSV dataset to begin.")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:

    # -----------------------------
    # SAFE CSV LOADING & CLEANUP
    # -----------------------------
    df = pd.read_csv(uploaded_file, dtype=str)

    df.columns = df.columns.str.strip().str.lower()

    if "ï»¿timestamp" in df.columns:
        df.rename(columns={"ï»¿timestamp": "timestamp"}, inplace=True)

    if "timestamp" not in df.columns:
        st.error("Your CSV is missing a 'timestamp' column. Please check your header row.")
        st.stop()

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    bad_rows = df[df["timestamp"].isna()]
    if len(bad_rows) > 0:
        st.warning(f"{len(bad_rows)} rows had invalid timestamps and were skipped.")

    numeric_cols = ["units", "lines", "workers", "errors", "cycle_time"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # -----------------------------
    # FATIGUE ENGINE
    # -----------------------------
    df["fatigue_score"] = (
        (df["cycle_time"] / df["cycle_time"].max()) * 60
        + (1 - (df["units"] / df["units"].max())) * 40
    )

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
    # FATIGUE KPIs
    # -----------------------------
    avg_fatigue = df["fatigue_score"].mean()
    peak_fatigue = df["fatigue_score"].max()
    min_fatigue = df["fatigue_score"].min()
    fatigue_stability = df["fatigue_score"].std()

    if avg_fatigue < 30:
        fatigue_risk = "Low"
    elif avg_fatigue < 60:
        fatigue_risk = "Moderate"
    else:
        fatigue_risk = "High"

    st.subheader("Fatigue KPIs")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Average Fatigue", f"{avg_fatigue:.1f}")
    with col2:
        st.metric("Peak Fatigue", f"{peak_fatigue:.1f}")
    with col3:
        st.metric("Minimum Fatigue", f"{min_fatigue:.1f}")

    col4, col5 = st.columns(2)
    with col4:
        st.metric("Fatigue Stability (Std Dev)", f"{fatigue_stability:.1f}")
    with col5:
        st.metric("Fatigue Risk Level", fatigue_risk)

    # -----------------------------
    # FATIGUE ALERTS (AUTO-WARNINGS)
    # -----------------------------
    st.subheader("Fatigue Alerts")

    if peak_fatigue > 85:
        st.error("⚠️ Critical fatigue detected! Consider rotation or relief.")
    if avg_fatigue > 60:
        st.warning("⚠️ High average fatigue. Productivity decline likely.")
    if fatigue_stability > 20:
        st.warning("⚠️ Fatigue instability detected. Workers are fluctuating heavily.")
    if min_fatigue < 15:
        st.info("ℹ️ Fresh productivity detected early in the shift.")

    # -----------------------------
    # BREAK / LUNCH MARKERS
    # -----------------------------
    st.subheader("Break & Lunch Markers")

    if "task_type" in df.columns:
        break_times = df[df["task_type"].str.contains("break", na=False)]
        lunch_times = df[df["task_type"].str.contains("lunch", na=False)]

        st.write("Break Events:")
        st.dataframe(break_times[["timestamp", "task_type", "fatigue_score"]])

        st.write("Lunch Events:")
        st.dataframe(lunch_times[["timestamp", "task_type", "fatigue_score"]])
    else:
        st.info("ℹ️ No 'task_type' column found. Add it to track breaks and lunch.")

    # -----------------------------
    # MULTI-SHIFT FATIGUE COMPARISON
    # -----------------------------
    if "shift" in df.columns:
        st.subheader("Multi-Shift Fatigue Comparison")

        shift_fatigue = df.groupby("shift")["fatigue_score"].mean()
        st.bar_chart(shift_fatigue)

        st.write("Shift Fatigue Averages:")
        st.write(shift_fatigue)
    else:
        st.info("ℹ️ No 'shift' column found. Add a shift column to enable multi-shift comparison.")

    # -----------------------------
    # CORE DATA & FATIGUE VISUALS
    # -----------------------------
    st.subheader("Raw Dataset With Fatigue")
    st.dataframe(df, use_container_width=True)

    st.subheader("Summary Statistics")
    st.write(df.describe())

    st.subheader("Preview (first 10 rows)")
    st.write(df.head(10))

    st.subheader("Fatigue Trend Over Time")
    fatigue_chart = df[["timestamp", "fatigue_score"]].set_index("timestamp")
    st.line_chart(fatigue_chart)

    st.subheader("Daily Fatigue Averages")
    daily_fatigue = df.groupby(df["timestamp"].dt.date)["fatigue_score"].mean()
    st.bar_chart(daily_fatigue)

    st.subheader("Fatigue Zones Table")
    zone_table = df[["timestamp", "units", "cycle_time", "fatigue_score", "fatigue_zone"]]
    st.dataframe(zone_table, use_container_width=True)
