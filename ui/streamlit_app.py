import streamlit as st
from scripts.analytics import (
    load_entries, total_time, time_per_day, time_by_project
)
from scripts.plots import bar_hours_per_day, pie_by_project, rolling_avg_line

st.set_page_config(page_title="Time Usage", layout="wide")
st.sidebar.title("Filters")

# ---- Load & cache ----
@st.cache_data
def load():
    return load_entries()
df = load()

# ---- Sidebar filters ----
df["week"] = df["start"].dt.isocalendar().week
weeks = sorted(df["week"].unique(), reverse=True)
week_choice = st.sidebar.selectbox("Week", weeks)
df = df[df["week"] == week_choice]

projects = df["project"].dropna().unique()
proj_choice = st.sidebar.multiselect("Project(s)", projects, default=projects)
df = df[df["project"].isin(proj_choice)]

# ---- Metrics ----
st.header("Time Usage Dashboard")
st.metric("Total hours this week", f"{total_time(df)} h")

# ---- Charts ----
daily = time_per_day(df)
proj  = time_by_project(df)

col1, col2 = st.columns((2, 1))
with col1:
    st.image(bar_hours_per_day(daily))
with col2:
    st.image(pie_by_project(proj))

st.image(rolling_avg_line(daily))
st.caption("Use the sidebar to change week or project filters.")
