from datetime import timedelta
import pandas as pd

from ml_events import TaskEvent
from recommendation_engine import RecommendationEngine

# ──────────────────────────────────────────────────────────────────────────────
# Heuristic parameters – tweak to taste
GAP_MIN = 5                  # break (min) that starts a new episode
COMPLETION_FACTOR = 0.90      # ≥90 % of estimated duration counts as “done”


# ──────────────────────────────────────────────────────────────────────────────
def infer_episodes(entries_df: pd.DataFrame, task_manager):
    """
    Collapse raw Toggl rows into 'episodes'.
    Each episode:
      • belongs to a single task
      • may consist of several contiguous rows separated by ≤GAP_MIN
      • is labelled completed / not-completed via COMPLETION_FACTOR

    Parameters
    ----------
    entries_df : DataFrame
        Columns required: 'start' (datetime64), 'stop' (datetime64),
                          'duration' (seconds), 'description' (task name)
    task_manager : TaskManager
        Provides metadata (category, difficulty, est. duration)

    Returns
    -------
    pd.DataFrame
        Columns: task_name, category, difficulty, start, cum_minutes,
                 est_minutes, completed
    """
    entries_df = entries_df.sort_values("start").reset_index(drop=True)
    episodes, current = [], None

    for _, row in entries_df.iterrows():
        task_name = row["description"]
        meta      = task_manager.get_task_info(task_name) or {}
        est_dur   = meta.get("estimated_duration", 0.5) * 60  # minutes

        # decide whether to start a new episode
        new_episode = (
            current is None
            or task_name != current["task_name"]
            or (row["start"] - current["last_stop"]) > timedelta(minutes=GAP_MIN)
        )

        if new_episode:
            if current:
                episodes.append(current)
            current = {
                "task_name":   task_name,
                "category":    meta.get("category", "Misc"),
                "difficulty":  int(meta.get("difficulty", 3)),
                "start":       row["start"],
                "cum_minutes": 0.0,
                "est_minutes": est_dur, # Already in minutes
                "last_stop":  row["start"] + timedelta(seconds=row["duration"]),
            }

        # accumulate time
        current["cum_minutes"] += row["duration"] / 60.0 #duration in seconds
        current["last_stop"]    = row["start"] + timedelta(seconds=row["duration"])

    if current:
        episodes.append(current)

    # label completion
    for ep in episodes:
        ep["completed"] = ep["cum_minutes"] >= COMPLETION_FACTOR * ep["est_minutes"]

    return pd.DataFrame(episodes)


# ──────────────────────────────────────────────────────────────────────────────
def toggl_df_to_events(entries_df: pd.DataFrame, task_manager, goal_tracker):
    """
    Convert Toggl entries → TaskEvent DataFrame with features for ML.

    Parameters
    ----------
    entries_df : pd.DataFrame
        Raw Toggl rows (same schema as infer_episodes()).
    task_manager : TaskManager
    goal_tracker : WeeklyGoalTracker

    Returns
    -------
    pd.DataFrame
        One row per TaskEvent with fields matching the TaskEvent dataclass.
    """
    episodes_df = infer_episodes(entries_df, task_manager).sort_values("start").reset_index(drop=True)

    # cache engine for performance-score calls (Sliding window + performance score + cached) 
    engine = RecommendationEngine(task_manager, goal_tracker)
    events = []

    for i, ep in episodes_df.iterrows():
        # historical slice up to current episode
        hist_df = episodes_df.iloc[: i + 1].copy()
        hist_df["date"]       = hist_df["start"].dt.date
        hist_df["duration_h"] = hist_df["cum_minutes"] / 60.0

        perf_score = engine.calculate_performance_score(hist_df)

        weekly_prog = goal_tracker.calculate_weekly_progress(hist_df)
        cat_info    = weekly_prog.get(
            ep["category"], {"hours": {"percentage": 0}}
        )
        cat_ratio = cat_info["hours"]["percentage"] / 100

        events.append(
            TaskEvent(
                task_name            = ep["task_name"],
                category             = ep["category"],
                difficulty           = int(ep["difficulty"]),
                started_at           = ep["start"],
                completed            = bool(ep["completed"]),
                perf_score_at_start  = perf_score,
                hour_of_day          = int(ep["start"].hour),
                category_completion  = cat_ratio,
            ).__dict__
        )

    return pd.DataFrame(events)
