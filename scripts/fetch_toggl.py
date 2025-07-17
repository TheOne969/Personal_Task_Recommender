""" Getting data from Toggl """

import os, json, requests, datetime as dt
from dotenv import load_dotenv

load_dotenv(r"C:\Codes\Personal_Task_Recommender\configs\.env")

TODAY = dt.date.today()
SINCE = TODAY - dt.timedelta(days=7) # To get the date one week before. 
DATA_DIR=r"C:\Codes\Personal_Task_Recommender\data"
RAW_DIR= os.path.join(DATA_DIR,"raw")
PROCESSED_DIR= os.path.join(DATA_DIR,"processed")
TOKEN= os.getenv("TOGGL_API_KEY")

if not TOKEN:
    raise ValueError("TOGGL_API_KEY not found in environment variables.")


# In your Phase 1 script (e.g., scripts/fetch_toggl.py)
import requests
import json

def fetch_project_mappings(api_token=TOKEN,dir=DATA_DIR):
    """Fetch project_id -> project_name mappings from Toggl"""
    url = "https://api.track.toggl.com/api/v9/me/projects"
    
    response = requests.get(url, auth=(api_token, "api_token"))
    response.raise_for_status()
    
    projects = response.json()
    
    # Create mapping dict
    mapping = {proj["id"]: proj["name"] for proj in projects}
    
    # Save to file
    with open(os.path.join(dir,"project_mappings.json"), "w") as f:
        json.dump(mapping, f, indent=2)
    

def fetch_time_entries(api_token=TOKEN,since=SINCE,today=TODAY,raw_dir=RAW_DIR):


    url = "https://api.track.toggl.com/api/v9/me/time_entries"
    params = {
        "start_date": since.isoformat(),
        "end_date": today.isoformat()
    }
    print(f"📅 Fetching from {since} to {today}")

    r = requests.get(url, params=params, auth=(api_token, "api_token"))
    print(f"Status: {r.status_code}")  # Debug line

    print(f"URL: {r.url}")

    if r.status_code != 200:
        print(f"Error: {r.text}")

    r.raise_for_status()
    data = r.json()

    outfile= os.path.join(raw_dir,f"raw_entries_{since}_to_{today}.json")

    with open(outfile,"w", encoding="utf-8") as file: 
        file.write(json.dumps(data,indent=2))

    print(f"Saved {len(data)} entries in {outfile}")

fetch_project_mappings()

