import pandas as pd

def load_entries(path=r"C:\Codes\personal_task_rec\data\processed\toggl_entries_2025-07-09_to_2025-07-16.csv"):
    df = pd.read_csv(path, parse_dates=["start", "end"])
    return df

def total_time(df):
    return round(df["duration_h"].sum(), 2)

def time_per_day(df):
    return (df.groupby(df["start"].dt.date)["duration_h"]
              .sum()
              .reset_index(name="hours"))

def time_by_project(df):
    return (df.groupby("project_id")["duration_h"]
              .sum()
              .reset_index(name="hours")
              .sort_values("hours", ascending=False))
