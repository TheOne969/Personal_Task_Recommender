# streamlit_app.py
import sys, os, subprocess
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd

# ─── add project root ─────────────────────────────────────────────────────────
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

# ─── third-party & local imports ──────────────────────────────────────────────
from scripts.analytics import load_entries, total_time, time_per_day, time_by_project
from scripts.plots     import bar_hours_per_day, pie_by_project, rolling_avg_line
from scripts.fetch_toggl import fetch_all_entries_with_pagination
from scripts.process      import process_file

from scripts.weekly_goals       import WeeklyGoalTracker
from scripts.task_manager       import TaskManager
from scripts.category_mapping   import CategoryMapper
from scripts.recommendation_engine import RecommendationEngine
from scripts.path_manager       import paths

MODEL_PATH = paths.data_dir / "completion_model.joblib"   # ← NEW

st.set_page_config(page_title="Time Usage Dashboard", layout="wide")

# ──────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def init_goal_system():
    try:
        return WeeklyGoalTracker(), TaskManager(), CategoryMapper()
    except Exception as e:
        st.error(f"Goal system not configured: {e}")
        return None, None, None

@st.cache_data
def load():
    return load_entries()

# ──────────────────────────────────────────────────────────────────────────────
def main():
    # Load your existing data
    df = load()
    
    # Initialize goal system
    goal_tracker, task_manager, category_mapper = init_goal_system()

    # Every time you change a filter:

    # 1. Script reruns  
    # 2. CSV data retrieved from memory cache (fast!)
    # 3. Data gets processed again
    # 4. Charts get regenerated

    # ----------------  GLOBAL FILTERS  -----------------
    with st.sidebar:

        st.header("Fetch Data")

        # Add date input widgets
        col1, col2 = st.columns(2)
        
        with col1:
            date1 = st.date_input(
                "Start Date",
                value=datetime.now().date() - timedelta(days=7),  # Default: 1 week ago
                key="start_date"
            )
        
        with col2:
            date2 = st.date_input(
                "End Date", 
                value=datetime.now().date(),  # Default: today
                key="end_date"
            )
    
        # Add a fetch button to control when data is fetched as we don't want it to call that function every time apps refreshes(i.e, when interacts with user)
        if st.button("🔄 Fetch Data"):
            if date1 <= date2:
                with st.spinner("Fetching data..."):
                    fetch_all_entries_with_pagination(date1, date2)
                
                # Process any new files
                source_dir = Path(paths.data_dir) / "raw"
                dest_dir = Path(paths.data_dir) / "processed"
                
                source_files = list(source_dir.iterdir())
                dest_files = list(dest_dir.iterdir())
                dest_file_names = {f.name for f in dest_files}
                
                processed_count = 0
                for path in source_files:
                    out = path.name.replace("raw_entries", "toggl_entries").replace(".json", ".csv")
                    
                    if out not in dest_file_names:
                        process_file(path)
                        processed_count += 1
                
                # Clear the cache to force reload of data
                load.clear()  # Clear only the load() function's cache
                
                st.success(f"Data fetched from {date1} to {date2}")
                if processed_count > 0:
                    st.info(f"Processed {processed_count} new files")
                
                # Force app rerun to reload data with fresh cache
                st.rerun()
                
            else:
                st.error("Start date must be before or equal to end date!")
        
        
        


        st.header("Filters")

        # make sure start is datetime
        df['start'] = pd.to_datetime(df['start'], errors='coerce')
        df['date']  = df['start'].dt.date          # keep the pure-date column

        # Build the ISO week number once
        df['iso_week'] = df['start'].dt.isocalendar().week

        # Unique week numbers in descending order
        weeks = sorted(df['iso_week'].unique(), reverse=True)

        # ONE selector for the whole app
        week_choice = st.selectbox("Week number", weeks, key="week_choice") # week_choice is being accessed through st.session_state.get("week_choice"), so indirectly.


    
     # ---------- PAGE TABS ----------
    
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Analytics", "🎯 Goals & Progress", "📋 Task Manager", "🤖 Recommendations"]
    )

    with tab1: show_analytics_tab(df)
    with tab2:
        if goal_tracker: show_goals_tab(df, goal_tracker, category_mapper)
        else: st.warning("Goals system not configured.")
    with tab3:
        if task_manager: show_tasks_tab(task_manager, category_mapper)
        else: st.warning("Task manager not configured.")
    with tab4:
        if goal_tracker and task_manager:
            show_recommendations_tab(df, goal_tracker, task_manager, category_mapper)
        else:
            st.warning("Recommendations need goals & tasks configured.")

def show_analytics_tab(df):
    """ First Tab """
    st.header("📊 Time Usage Analytics")
    
    # Existing sidebar filters
    with st.sidebar:
        # Not creating a filter as I want this to go directly under existing Filter header. 
        
        # Week filter
         # Read the value that Streamlit automatically stored
        week_num = st.session_state.get("week_choice")
    
        if week_num is None:
            st.warning("Pick a week in the sidebar to see goal progress.")
            return
        
        df_filtered  = df[df['iso_week'] == week_num]

        
        # Project filter
        projects = df_filtered["project"].dropna().unique()
        proj_choice = st.multiselect("Project(s)", projects, default=projects)
        df_filtered = df_filtered[df_filtered["project"].isin(proj_choice)]
    
    # Your existing metrics
    st.metric("Total hours this week", f"{total_time(df_filtered):.1f} h")
    
    # Your existing charts
    daily = time_per_day(df_filtered)
    proj = time_by_project(df_filtered)
    
    col1, col2 = st.columns((2, 1))
    with col1:
        st.image(bar_hours_per_day(daily))
    with col2:
        st.image(pie_by_project(proj))
    
    st.image(rolling_avg_line(daily))
    st.caption("Use the sidebar to change week or project filters.")

def show_goals_tab(df, goal_tracker, category_mapper):
    """Tab: Weekly Goals & Progress"""
    st.header("🎯 Weekly Goals & Progress")

    # ----------------------------------------------------------------
    # 1.  Prepare dataframe (date + iso_week + category columns)
    # ----------------------------------------------------------------
    df_week = df.copy()

    # ensure date column is pure date objects
    if df_week["date"].dtype == "object":
        df_week["date"] = pd.to_datetime(df_week["date"]).dt.date

    # iso week number (add once if it isn’t already there)
    if "iso_week" not in df_week.columns:
        df_week["iso_week"] = pd.to_datetime(df_week["date"]).dt.isocalendar().week

    # add goal-category column
    if "category" not in df_week.columns:
        df_week["category"] = df_week.apply(
            lambda row: category_mapper.map_entry_to_category(
                project=row.get("project", ""),
                description=row.get("description", "")
            ),
            axis=1
        )

    # ----------------------------------------------------------------
    # 2.  Filter to the week the user picked in the sidebar
    # ----------------------------------------------------------------
    week_num = st.session_state.get("week_choice")
    if week_num is None:
        st.warning("Pick a week in the sidebar to see goal progress.")
        return

    week_df = df_week[df_week["iso_week"] == week_num]

    if week_df.empty:
        st.info(f"No data found for ISO-week {week_num}.")
        return

    # ----------------------------------------------------------------
    # 3.  Build progress dictionary (hours, % complete, status)
    # ----------------------------------------------------------------
    progress = {}
    for category, goal_info in goal_tracker.weekly_goals.items():
        hours_done = week_df[week_df["category"] == category]["duration_h"].sum()
        target     = goal_info["target_hours"]
        pct        = min(100, (hours_done / target) * 100) if target else 0

        progress[category] = {
            "hours": {
                "completed": round(hours_done, 2),
                "target":    target,
                "percentage": pct
            },
            "priority": goal_info["priority"],
            "status":   goal_tracker.get_goal_status(hours_done, target)
        }

    # ----------------------------------------------------------------
    # 4.  Display progress cards
    # ----------------------------------------------------------------
    st.subheader(f"📈 Progress for ISO-week {week_num}")
    cols = st.columns(max(1, len(progress)))

    for idx, (cat, data) in enumerate(progress.items()):
        with cols[idx]:
            comp = data["hours"]["completed"]
            targ = data["hours"]["target"]
            pct  = data["hours"]["percentage"]
            stat = data["status"]

            st.metric(
                label=f"{cat} {stat}",
                value=f"{comp:.1f} h",
                delta=f"{targ - comp:.1f} h remaining"
            )
            st.progress(min(pct / 100, 1.0))
            st.caption(f"{pct:.0f}% of {targ} h goal")

    # ----------------------------------------------------------------
    # 5.  Category-distribution chart + text summary
    # ----------------------------------------------------------------
    st.subheader("📊 Category Time Distribution")
    cat_hours = (
        week_df.groupby("category")["duration_h"]
               .sum()
               .sort_values(ascending=False)
    )

    if cat_hours.empty:
        st.info("No tracked hours this week.")
    else:
        st.bar_chart(cat_hours, use_container_width=True)

        for cat, hrs in cat_hours.items():
            targ = goal_tracker.weekly_goals.get(cat, {}).get("target_hours", 0)
            if targ:
                st.write(f"• **{cat}**  {hrs:.1f} h / {targ} h "
                         f"({(hrs/targ)*100:.0f} %)")
            else:
                st.write(f"• **{cat}**  {hrs:.1f} h (no goal set)")

def show_tasks_tab(task_manager,category_mapper):
    """Tab 3"""
    st.header("📋 Task Manager")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Available Tasks")
        tasks = task_manager.get_all_tasks()
        
        if tasks:
            for task_name, task_info in tasks.items():
                with st.expander(f"📝 {task_name}"):
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        st.write(f"**Category:** {task_info['category']}")
                    with col_b:
                        difficulty_desc = task_manager.get_difficulty_description(task_info['difficulty'])
                        st.write(f"**Difficulty:** {difficulty_desc}")
                    with col_c:
                        duration = task_info.get('estimated_duration', 'Not set')
                        st.write(f"**Duration:** {duration}h")
                    
                    if st.button(f"🗑️ Remove {task_name}", key=f"del_{task_name}"):
                        task_manager.remove_task(task_name)
                        task_manager.save_tasks()
                        st.rerun()
        else:
            st.info("No tasks configured. Add some below!")
    
    with col2:
        st.subheader("➕ Add Task")
        with st.form("new_task"):
            task_name = st.text_input("Task Name")
            task_category = st.selectbox("Category", 
                category_mapper.get_all_categories())
            task_difficulty = st.slider("Difficulty", 1, 5, 3)
            task_duration = st.number_input("Duration (hours)", 0.5, 8.0, 1.0)
            
            if st.form_submit_button("Add Task"):
                if task_name:
                    task_manager.add_task(task_name, task_category, task_difficulty, task_duration)
                    task_manager.save_tasks()
                    st.success(f"Added: {task_name}")
                    st.rerun()

def human_time(epoch: float) -> str:
    return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M")

def show_recommendations_tab(df, goal_tracker, task_manager, category_mapper):
    """Tab 4 — now includes model status & retrain button"""
    st.header("🤖 Task Recommendations")

    # 1️⃣  load / cache engine
    if "rec_engine" not in st.session_state:
        st.session_state.rec_engine = RecommendationEngine(task_manager, goal_tracker)
    rec_engine = st.session_state.rec_engine

    # 2️⃣  model status + retrain button
    model_exists = MODEL_PATH.exists()
    last_trained = human_time(MODEL_PATH.stat().st_mtime) if model_exists else "never"
    st.caption(f"ML model file: {'✅' if model_exists else '❌'}  (last trained: {last_trained})")

    if st.button("♻️ Retrain completion model"):
        with st.spinner("Training… this takes a few seconds"):
            subprocess.run(["python", "scripts/train_completion_model.py"], check=True)
        st.success("Retrain finished — reloading model")
        # refresh engine so new .joblib is picked up
        st.session_state.rec_engine = RecommendationEngine(task_manager, goal_tracker)
        st.rerun()

    # 3️⃣  sidebar settings specific to this tab
    with st.sidebar:
        st.subheader("🎛️ Recommendation Settings")
        perf_w = st.slider("Performance Weight", 0.0, 1.0, 0.4, 0.1)
        goal_w = st.slider("Goal Progress Weight", 0.0, 1.0, 0.6, 0.1)
        rec_engine.update_weights(perf_w, goal_w)
        target  = st.number_input("Daily Target Hours", 1.0, 12.0, 6.0, 0.5)
        rec_engine.set_daily_target(target)

    # 4️⃣  add categories to dataframe
    df_cat = df.copy()
    df_cat["category"] = df_cat.apply(
        lambda r: category_mapper.map_entry_to_category(
            project=r.get("project", ""), description=r.get("description", "")
        ),
        axis=1,
    )

    # 5️⃣  get & display recommendations
    recs = rec_engine.get_top_recommendations(df_cat, limit=5)
    if not recs:
        st.warning("No tasks to recommend. Add tasks in the Task Manager tab.")
        return

    st.subheader("🎯 Recommended Next Task")
    top = recs[0]
    col1, col2 = st.columns([2, 1])
    with col1:
        st.success(f"**{top.task_name}**")
        st.write(f"📂 Category: {top.category}")
        st.write(f"⭐ Priority Score: {top.priority_score:.2f}")
        st.write(f"💡 Why: {top.reasoning}")
    with col2:
        st.metric("Difficulty", task_manager.get_difficulty_description(top.difficulty))
        st.metric("Est. Duration", f"{top.estimated_duration} h")

    st.subheader("📋 All Recommendations")
    for i, rec in enumerate(recs):
        with st.expander(f"{i+1}. {rec.task_name}  (Score {rec.priority_score:.2f})"):
            st.write(f"**Category:** {rec.category}")
            st.write(f"**Difficulty:** {task_manager.get_difficulty_description(rec.difficulty)}")
            st.write(f"**Duration:** {rec.estimated_duration} h")
            st.write(f"**Reasoning:** {rec.reasoning}")

# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
