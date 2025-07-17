import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st

from scripts.analytics import (
    load_entries, total_time, time_per_day, time_by_project
)
from scripts.plots import bar_hours_per_day, pie_by_project, rolling_avg_line

# The above imports will fail 'coz scripts is not in the current directory. For
# it to work, those above lines of code were added. 

st.set_page_config(page_title="Time Usage", layout="wide")
st.sidebar.title("Filters")

# Every time you change a filter:
# 1. Script reruns  
# 2. CSV data retrieved from memory cache (fast!)
# 3. Data gets processed again
# 4. Charts get regenerated

# ---- Load & cache ----
@st.cache_data # Caches the data so it doesn't reload on every interaction
def load():
    return load_entries()
df = load()

# ---- Sidebar filters ----
df["week"] = df["start"].dt.isocalendar().week # Extracts week number
weeks = sorted(df["week"].unique(), reverse=True)
week_choice = st.sidebar.selectbox("Week", weeks)
df = df[df["week"] == week_choice]

projects = df["project"].dropna().unique()
proj_choice = st.sidebar.multiselect("Project(s)", projects, default=projects)
df = df[df["project"].isin(proj_choice)]

# ---- Metrics ----
st.header("Time Usage Dashboard")
st.metric("Total hours this week", f"{total_time(df):.1f} h")

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


