import streamlit as st
import pandas as pd

# -----------------------------
# COLOR PALETTE
# -----------------------------
GREEN = "#2ECC71"
LIGHT_GREEN = "#A3E4D7"
YELLOW = "#F1C40F"
ORANGE = "#E67E22"
RED = "#E74C3C"

# -----------------------------
# COLOR HELPERS
# -----------------------------
def colored_alert(message, color):
    st.markdown(
        f"""
        <div style="
            background-color:{color};
            padding:12px;
            border-radius:6px;
            color:white;
            font-weight:bold;
            margin-bottom:10px;">
            {message}
        </div>
        """,
        unsafe_allow_html=True
    )

def fatigue_badge(zone):
    color_map = {
        "Fresh (Green)": GREEN,
        "Warming Up (Light Green)": LIGHT_GREEN,
        "Noticeable Fatigue (Yellow)": YELLOW,
        "High Fatigue (Orange)": ORANGE,
        "Critical Fatigue (Red)": RED
    }
    color = color_map.get(zone, "#95A5A6")
    return f"<span style='background:{color}; padding:4px 8px; border-radius:4px; color:white;'>{zone}</span>"

def kpi_bar(label, value, color):
    st.markdown(
        f"""
        <div style="padding:10px; border-radius:6px; background:{color}; color:white; margin-bottom:10px;">
            <strong>{label}:</strong> {value}
        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------
# STREAMLIT PAGE CONFIG
# -----------------------------
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
        colored_alert("ERROR: Your CSV is missing a 'timestamp' column.", RED)
        st.stop()

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    bad_rows = df[df["timestamp"].isna()]
    if len(bad_rows) > 0:
        colored_alert(f"{len(bad_rows)} rows had invalid timestamps and were skipped.", ORANGE)

    numeric_cols = ["units", "lines", "workers", "errors", "cycle_time"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # -----------------------------
    # TIGHTENED FATIGUE ENGINE
    # -----------------------------
    df["fatigue_score"] = (
        (df["cycle_time"] / df["cycle_time"].max()) * 50 +
        (1 - (df["units"] / df["units"].max())) * 30 +
        (df["errors"] / df["errors"].max()) * 15 +
        (1 - (df["workers"] / df["workers"].max())) * 5
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
    # FATIGUE KPIs (COLORIZED)
    # -----------------------------
    avg_fatigue = df["fatigue_score"].mean()
    peak_fatigue = df["fatigue_score"].max()
    min_fatigue = df["fatigue_score"].min()
    fatigue_stability = df["fatigue_score"].std()

    if avg_fatigue < 30:
        fatigue_risk = "Low"
        risk_color = GREEN
    elif avg_fatigue < 60:
        fatigue_risk = "Moderate"
        risk_color = YELLOW
    else:
        fatigue_risk = "High"
        risk_color = RED

    st.subheader("Fatigue KPIs")

    kpi_bar("Average Fatigue", f"{avg_fatigue:.1f}", risk_color)
    kpi_bar("Peak Fatigue", f"{peak_fatigue:.1f}", RED if peak_fatigue > 85 else ORANGE)
    kpi_bar("Minimum Fatigue", f"{min_fatigue:.1f}", GREEN if min_fatigue < 20 else LIGHT_GREEN)
    kpi_bar("Fatigue Stability (Std Dev)", f"{fatigue_stability:.1f}", YELLOW if fatigue_stability > 20 else GREEN)

    # -----------------------------
    # RECOMMENDED ACTION ENGINE (COLORIZED)
    # -----------------------------
    if avg_fatigue < 30:
        action = "Shift is performing well. Maintain current workflow."
        action_color = GREEN
    elif avg_fatigue < 50:
        action = "Monitor mid-shift slowdown. Consider micro-breaks or rotation."
        action_color = LIGHT_GREEN
    elif avg_fatigue < 70:
        action = "Fatigue rising. Add relief workers or redistribute tasks."
        action_color = ORANGE
    else:
        action = "Critical fatigue. Immediate rotation or break required."
        action_color = RED

    if peak_fatigue > 85:
        action += " Peak fatigue is dangerously high — intervene now."
        action_color = RED

    if fatigue_stability > 20:
        action += " Fatigue instability detected — workers fluctuating heavily."
        action_color = ORANGE

    st.subheader("Recommended Action")
    colored_alert(action, action_color)

    # -----------------------------
    # FATIGUE ALERTS (COLORIZED)
    # -----------------------------
    st.subheader("Fatigue Alerts")

    if peak_fatigue > 85:
        colored_alert("CRITICAL FATIGUE — Immediate rotation required.", RED)

    if avg_fatigue > 60:
        colored_alert("High average fatigue — productivity decline likely.", ORANGE)

    if fatigue_stability > 20:
        colored_alert("Fatigue instability — workers fluctuating heavily.", YELLOW)

    if min_fatigue < 15:
        colored_alert("Fresh productivity detected early in shift.", GREEN)

    # -----------------------------
    # BREAK / LUNCH MARKERS (COLORIZED)
    # -----------------------------
    st.subheader("Break & Lunch Markers")

    if "task_type" in df.columns:
        df["event_color"] = df["task_type"].apply(
            lambda x: YELLOW if "lunch" in x.lower()
            else LIGHT_GREEN if "break" in x.lower()
            else "transparent"
        )

        events = df[df["event_color"] != "transparent"]

        for _, row in events.iterrows():
            colored_alert(f"{row['timestamp']} — {row['task_type']}", row["event_color"])
    else:
        colored_alert("No 'task_type' column found. Add it to track breaks and lunch.", ORANGE)

    # -----------------------------
    # MULTI-SHIFT FATIGUE COMPARISON (COLORIZED)
    # -----------------------------
    if "shift" in df.columns:
        st.subheader("Multi-Shift Fatigue Comparison")

        shift_fatigue = df.groupby("shift")["fatigue_score"].mean()

        for shift, score in shift_fatigue.items():
            color = GREEN if score < 30 else YELLOW if score < 60 else RED
            colored_alert(f"Shift {shift}: {score:.1f}", color)
    else:
        colored_alert("No 'shift' column found. Add a shift column to enable multi-shift comparison.", ORANGE)

    # -----------------------------
    # CORE DATA & VISUALS
    # -----------------------------
    st.subheader("Raw Dataset With Fatigue")
    st.dataframe(df, use_container_width=True)

    st.subheader("Fatigue Trend Over Time")
    fatigue_chart = df[["timestamp", "fatigue_score"]].set_index("timestamp")
    st.line_chart(fatigue_chart)

    st.subheader("Daily Fatigue Averages")
    daily_fatigue = df.groupby(df["timestamp"].dt.date)["fatigue_score"].mean()
    st.bar_chart(daily_fatigue)

    st.subheader("Fatigue Zones Table")
    zone_table = df[["timestamp", "units", "cycle_time", "errors", "workers", "fatigue_score", "fatigue_zone"]]
    zone_table["fatigue_zone"] = zone_table["fatigue_zone"].apply(fatigue_badge)
    st.markdown(zone_table.to_html(escape=False), unsafe_allow_html=True)
