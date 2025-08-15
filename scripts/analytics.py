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
        
        csv_files = [f for f in processed_dir.glob("*.csv") if f.name != "task_events.csv"]
   

        if not csv_files: 
            raise FileNotFoundError(f"No CSV files found in {processed_dir}")
        
        

    df_list   = [pd.read_csv(f, parse_dates=["start"],index_col=False,na_values=[],na_filter=False) for f in csv_files] # stop isn't needed for analysis as we already have duration.
    # parse_dates is important because it's converting the string object into datetime.

    df=  pd.concat(df_list, ignore_index=True) # We are using concat coz multiple dataframes coz different files collectively put together. Another way to do is to first gather all the entires in one file and read it once. 
    df.drop_duplicates(subset="id", inplace=True) 
    df.sort_values("start", inplace=True) # if we don't add inplace, then df will remain unchanged, as the new sorted object isn't being assigned to any variable, hence not manipulated. 

    if "duration_h" not in df.columns:
        print("!!! duration_h column missing - something's wrong")
        return df
    
    project_mappings = load_project_mappings()

     # Fix: Remove .0 suffix from project_ids. This happened when pandas read NaN values and makes the whole column float.  
    df["project_id"] = df["project_id"].astype(str).str.replace('.0', '', regex=False)
    # making sure that project id is a string.
    
    df["project"] = df["project_id"].map(project_mappings)

    # Better fallback - use project_id if mapping fails
    df["project"] = df["project"].fillna("Project_" + df["project_id"])
    
    print(f"!!! Loaded {len(df)} entries with {df['duration_h'].sum():.1f} total hours")
    return df

def total_time(df):
    return df['duration_h'].sum()

def time_per_day(df):
    """ returns a dataframe with two columns: date and time. """

    return (df.groupby(df["date"])["duration_h"]
              .sum()
              .reset_index()# Reset index converts series to a dataframe with index column now being original name which is here "date".
              .rename(columns= {"duration_h":"hours"})) 

def time_by_project(df):
    return (df.groupby("project")["duration_h"]  
              .sum()
              .reset_index()
              .rename(columns={"duration_h": "hours"})
              .sort_values("hours", ascending=False))
