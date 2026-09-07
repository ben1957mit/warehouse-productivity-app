import streamlit as st
import pandas as pd

st.title("First-Shift Productivity Drop-Off Analysis")

# 1. Upload data
st.subheader("Upload first-shift dataset")
file = st.file_uploader("Upload CSV with timestamp, units, lines, workers, errors, cycle_time, task_type", type=["csv"])

if file is not None:
    df = pd.read_csv(file)

    # 2. Normalize timestamp and create 30-min intervals
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["time"] = df["timestamp"].dt.time
    df["interval_start"] = df["timestamp"].dt.floor("30min")

    # 3. Aggregate by interval
    agg = df.groupby("interval_start").agg({
        "units": "sum",
        "lines": "sum",
        "workers": "sum",
        "errors": "sum",
        "cycle_time": "mean"
    }).reset_index()

    # 4. Calculate productivity metrics
    agg["units_per_labor_hour"] = agg["units"] / agg["workers"].replace(0, pd.NA)
    agg["lines_per_labor_hour"] = agg["lines"] / agg["workers"].replace(0, pd.NA)
    agg["error_rate"] = agg["errors"] / agg["lines"].replace(0, pd.NA)

    # 5. Sort by time within shift
    agg = agg.sort_values("interval_start")

    st.subheader("Interval Productivity Metrics")
    st.dataframe(agg[[
        "interval_start",
        "units_per_labor_hour",
        "lines_per_labor_hour",
        "error_rate",
        "cycle_time"
    ]])

    # 6. Plot productivity over time
    st.subheader("Units per Labor Hour by Interval (First Shift)")
    st.line_chart(
        agg.set_index("interval_start")[["units_per_labor_hour"]]
    )

    # 7. Moving average (3-interval)
    window = 3
    agg["uplh_ma"] = agg["units_per_labor_hour"].rolling(window=window, min_periods=1).mean()

    st.subheader(f"Smoothed Productivity (Moving Average, window={window})")
    st.line_chart(
        agg.set_index("interval_start")[["units_per_labor_hour", "uplh_ma"]]
    )

    # 8. Identify potential drop-off intervals
    st.subheader("Potential Drop-Off Detection")

    # Compare each interval to previous
    agg["uplh_change_pct"] = agg["units_per_labor_hour"].pct_change() * 100

    threshold = st.slider("Drop-off threshold (% decline)", 5, 30, 10)
    drops = agg[agg["uplh_change_pct"] <= -threshold]

    st.write(f"Intervals with ≥ {threshold}% decline vs previous:")
    st.dataframe(drops[[
        "interval_start",
        "units_per_labor_hour",
        "uplh_ma",
        "uplh_change_pct"
    ]])

    # 9. Summary text
    if not drops.empty:
        first_drop = drops.iloc[0]
        st.markdown(
            f"**First significant drop-off detected at** `{first_drop['interval_start']}` "
            f"with a {first_drop['uplh_change_pct']:.1f}% decline in units per labor hour."
        )
    else:
        st.markdown("No intervals meet the current drop-off threshold.")

else:
    st.info("Upload a CSV file to begin the analysis.")

