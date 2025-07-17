import pandas as pd
import json
from pathlib import Path

def load_project_mappings(path=r"C:\Codes\Personal_Task_Recommender\data\project_mappings.json"):
    """Load project_id -> project_name mappings"""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {path} not found. Using project_id as project name.")
        return {}
    
def load_entries(path=None):

    if not path: 
        project_root = Path(__file__).parent.parent
        processed_dir = project_root / "data" / "processed"
        
        csv_files= list(processed_dir.glob("*.csv"))

        if not csv_files: 
            raise FileNotFoundError(f"No CSV files found in {processed_dir}")
        
        # Use the most recent file automatically
        path = max(csv_files, key=lambda f: f.stat().st_mtime)
        print(f"Loading data from: {path}")

    df = pd.read_csv(path, parse_dates=["start"]) # stop isn't needed for analysis as we already have duration

    if "duration_h" not in df.columns:
        print("!!! duration_h column missing - something's wrong")
        return df
    
    project_mappings = load_project_mappings()
    df["project_id"] = df["project_id"].astype(str) # making sure that project id is a string.
    df["project"] = df["project_id"].map(project_mappings)

    # Better fallback - use project_id if mapping fails
    df["project"] = df["project"].fillna("Project_" + df["project_id"])
    
    print(f"!!! Loaded {len(df)} entries with {df['duration_h'].sum():.1f} total hours")
    return df

def total_time(df):
    return df['duration_h'].sum()

def time_per_day(df):
    return (df.groupby(df["start"].dt.date)["duration_h"] # Here, the thing is, that it will return a df with start as date objects not date-time
              .sum()
              .reset_index()# Reset index converts series to a dataframe with index column now being original name which is here "start".
              .rename(columns= {"start":"date","duration_h":"hours"})) 

def time_by_project(df):
    return (df.groupby("project")["duration_h"]  # Now uses "project" not "project_id"
              .sum()
              .reset_index()
              .rename(columns={"duration_h": "hours"})
              .sort_values("hours", ascending=False))
