import streamlit as st
import pandas as pd
import altair as alt

# -----------------------------
# COLOR PALETTE
# -----------------------------
GREEN = "#2ECC71"
LIGHT_GREEN = "#A3E4D7"
YELLOW = "#F1C40F"
ORANGE = "#E67E22"
RED = "#E74C3C"
GREY = "#95A5A6"

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
    color = color_map.get(zone, GREY)
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
    # COMBINED PERFORMANCE & FATIGUE KPIs
    # -----------------------------
    st.subheader("Combined Performance & Fatigue KPIs")

    avg_units = df["units"].mean() if "units" in df.columns else 0
    avg_lines = df["lines"].mean() if "lines" in df.columns else 0
    avg_errors = df["errors"].mean() if "errors" in df.columns else 0
    avg_workers = df["workers"].mean() if "workers" in df.columns else 0

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

    col_perf1, col_perf2, col_perf3, col_perf4 = st.columns(4)
    with col_perf1:
        kpi_bar("Avg Units", f"{avg_units:.1f}", GREEN if avg_units > 0 else GREY)
    with col_perf2:
        kpi_bar("Avg Lines", f"{avg_lines:.1f}", LIGHT_GREEN if avg_lines > 0 else GREY)
    with col_perf3:
        kpi_bar("Avg Errors", f"{avg_errors:.1f}", RED if avg_errors > 0 else GREEN)
    with col_perf4:
        kpi_bar("Avg Workers", f"{avg_workers:.1f}", LIGHT_GREEN if avg_workers > 0 else GREY)

    kpi_bar("Average Fatigue", f"{avg_fatigue:.1f}", risk_color)
    kpi_bar("Peak Fatigue", f"{peak_fatigue:.1f}", RED if peak_fatigue > 85 else ORANGE)
    kpi_bar("Minimum Fatigue", f"{min_fatigue:.1f}", GREEN if min_fatigue < 20 else LIGHT_GREEN)
    kpi_bar("Fatigue Stability (Std Dev)", f"{fatigue_stability:.1f}", YELLOW if fatigue_stability > 20 else GREEN)
    kpi_bar("Fatigue Risk Level", fatigue_risk, risk_color)

    # -----------------------------
    # RECOMMENDED ACTION ENGINE
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
    # FATIGUE ALERTS
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
    # BREAK / LUNCH MARKERS
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
    # MULTI-SHIFT FATIGUE COMPARISON + HEATMAP
    # -----------------------------
    st.subheader("Multi-Shift Fatigue Comparison")

    if "shift" in df.columns:
        shift_fatigue = df.groupby("shift")["fatigue_score"].mean()

        for shift, score in shift_fatigue.items():
            color = GREEN if score < 30 else YELLOW if score < 60 else RED
            colored_alert(f"Shift {shift}: {score:.1f}", color)

        # Heatmap: shift vs date
        df["date"] = df["timestamp"].dt.date
        heat_data = df.groupby(["shift", "date"])["fatigue_score"].mean().reset_index()

        heatmap = alt.Chart(heat_data).mark_rect().encode(
            x=alt.X("date:N", title="Date"),
            y=alt.Y("shift:N", title="Shift"),
            color=alt.Color("fatigue_score:Q", scale=alt.Scale(scheme="redyellowgreen"), title="Fatigue"),
            tooltip=["shift", "date", "fatigue_score"]
        ).properties(
            width=600,
            height=300,
            title="Shift Fatigue Heatmap"
        )

        st.altair_chart(heatmap, use_container_width=True)
    else:
        colored_alert("No 'shift' column found. Add a shift column to enable multi-shift comparison and heatmap.", ORANGE)

    # -----------------------------
    # COLORED FATIGUE LINE CHART ZONES
    # -----------------------------
    st.subheader("Fatigue Trend Over Time (Colored Zones)")

    line_data = df[["timestamp", "fatigue_score", "fatigue_zone"]].dropna()

    line_chart = alt.Chart(line_data).mark_line().encode(
        x=alt.X("timestamp:T", title="Time"),
        y=alt.Y("fatigue_score:Q", title="Fatigue Score"),
        color=alt.Color("fatigue_zone:N",
                        scale=alt.Scale(
                            domain=[
                                "Fresh (Green)",
                                "Warming Up (Light Green)",
                                "Noticeable Fatigue (Yellow)",
                                "High Fatigue (Orange)",
                                "Critical Fatigue (Red)"
                            ],
                            range=[GREEN, LIGHT_GREEN, YELLOW, ORANGE, RED]
                        ),
                        title="Fatigue Zone"),
        tooltip=["timestamp", "fatigue_score", "fatigue_zone"]
    ).properties(
        width=800,
        height=300
    )

    st.altair_chart(line_chart, use_container_width=True)

    # -----------------------------
    # DAILY FATIGUE AVERAGES
    # -----------------------------
    st.subheader("Daily Fatigue Averages")
    daily_fatigue = df.groupby(df["timestamp"].dt.date)["fatigue_score"].mean().reset_index()
    daily_fatigue.columns = ["date", "avg_fatigue"]

    daily_chart = alt.Chart(daily_fatigue).mark_bar(color=ORANGE).encode(
        x=alt.X("date:N", title="Date"),
        y=alt.Y("avg_fatigue:Q", title="Average Fatigue"),
        tooltip=["date", "avg_fatigue"]
    ).properties(
        width=800,
        height=300
    )

    st.altair_chart(daily_chart, use_container_width=True)

    # -----------------------------
    # SUPERVISOR INTERPRETATION PANEL
    # -----------------------------
    st.subheader("Supervisor Interpretation Panel")

    interpretation_text = """
### How to Read This Dashboard

**Fatigue Score (0–100)**  
- 0–20: Fresh (Green)  
- 21–40: Warming Up (Light Green)  
- 41–60: Noticeable Fatigue (Yellow)  
- 61–80: High Fatigue (Orange)  
- 81–100: Critical (Red)  

**What Supervisors Should Watch For:**  
- Yellow → Orange → Red transitions  
- Afternoon fatigue waves  
- Pre‑lunch slump  
- No recovery after breaks  
- High fatigue + high errors = safety risk  
- High fatigue + low units = productivity decline  
"""

    colored_alert("Supervisor Guide Loaded — Scroll down to read full interpretation.", LIGHT_GREEN)
    st.markdown(interpretation_text)

    # -----------------------------
    # SAFETY RISK SCORING SYSTEM
    # -----------------------------
    st.subheader("Safety Risk Score")

    df["safety_risk"] = (
        (df["fatigue_score"] / 100) * 60 +
        (df["errors"] / df["errors"].max()) * 30 +
        (df["cycle_time"] / df["cycle_time"].max()) * 10
    )

    avg_risk = df["safety_risk"].mean()

    if avg_risk < 25:
        risk_label = "Low Risk"
        risk_color = GREEN
    elif avg_risk < 50:
        risk_label = "Moderate Risk"
        risk_color = YELLOW
    elif avg_risk < 75:
        risk_label = "High Risk"
        risk_color = ORANGE
    else:
        risk_label = "Critical Risk"
        risk_color = RED

    kpi_bar("Safety Risk Score", f"{avg_risk:.1f}", risk_color)
    colored_alert(f"Safety Status: {risk_label}", risk_color)

    # -----------------------------
    # PRODUCTIVITY VS FATIGUE CORRELATION
    # -----------------------------
    st.subheader("Productivity vs Fatigue Correlation")

    corr_data = df[["units", "fatigue_score"]].dropna()

    corr_chart = alt.Chart(corr_data).mark_circle(size=80).encode(
        x=alt.X("fatigue_score:Q", title="Fatigue Score"),
        y=alt.Y("units:Q", title="Units Output"),
        color=alt.Color("fatigue_score:Q", scale=alt.Scale(scheme="redyellowgreen")),
        tooltip=["units", "fatigue_score"]
    ).properties(
        width=700,
        height=350,
        title="Correlation Between Fatigue and Productivity"
    )

    st.altair_chart(corr_chart, use_container_width=True)

    # -----------------------------
    # RAW DATA + FATIGUE ZONES TABLE
    # -----------------------------
    st.subheader("Raw Dataset With Fatigue")
    st.dataframe(df, use_container_width=True)

    st.subheader("Fatigue Zones Table")
    zone_table = df[["timestamp", "units", "cycle_time", "errors", "workers", "fatigue_score", "fatigue_zone"]]
    zone_table["fatigue_zone"] = zone_table["fatigue_zone"].apply(fatigue_badge)
    st.markdown(zone_table.to_html(escape=False), unsafe_allow_html=True)
