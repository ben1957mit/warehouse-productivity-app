import streamlit as st

st.set_page_config(page_title="Employee Productivity Calculator", layout="centered")

st.title("Employee Productivity Calculator")

st.write("Enter the employee's work details below to calculate productivity.")

# Input fields
hours_worked = st.number_input("Hours Worked", min_value=0.0, step=0.5)
units_completed = st.number_input("Units Completed", min_value=0, step=1)
target_units = st.number_input("Target Units (Goal)", min_value=1, step=1)

# Calculate productivity
if target_units > 0 and hours_worked > 0:
    productivity = (units_completed / target_units) * 100
    units_per_hour = units_completed / hours_worked
else:
    productivity = 0
    units_per_hour = 0

# Display results
st.subheader("Results")
st.write(f"**Productivity:** {productivity:.2f}%")
st.write(f"**Units per Hour:** {units_per_hour:.2f}")

# Rating
st.subheader("Performance Rating")

if productivity >= 120:
    st.success("Outstanding Performance")
elif productivity >= 100:
    st.success("Meets Expectations")
elif productivity >= 80:
    st.warning("Needs Improvement")
else:
    st.error("Unsatisfactory Performance")
