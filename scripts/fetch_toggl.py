""" Getting data from Toggl """

import os, json, requests, datetime as dt
from dotenv import load_dotenv
import requests
import json


load_dotenv()

TODAY = dt.date.today()
SINCE = TODAY - dt.timedelta(days=7) # To get the date one week before. 
DATA_DIR=r"C:\Codes\Personal_Task_Recommender\data"
RAW_DIR= os.path.join(DATA_DIR,"raw")
PROCESSED_DIR= os.path.join(DATA_DIR,"processed")

TOKEN= os.getenv("TOGGL_API_KEY")
HAS_API= bool(TOKEN)

def ensure_key_or_explain():
    """Return True if API key is available, False otherwise"""
    if not HAS_API:
        print("No TOGGL_API_KEY found - running in offline mode")
        return False
    return True

def daterange(start_date, end_date):
    """Generate all dates in range"""
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + dt.timedelta(n)

def date_2_range(dates): 
    range_list= []

    i=0 
    while i<len(dates): 
        j= i+1
        while j<len(dates): 
            if dates[j-1] + dt.timedelta(1) != dates[j]: 
                break
            j+=1
        
        if i!= j-1:
            range_list.append((dates[i],dates[j-1]))
            i=j

        else: 
            range_list.append((dates[i], dates[i] + dt.timedelta(1)))
            i+=1

    
    return range_list
        
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
    
def fetch_time_entries(api_token=TOKEN,since=SINCE,today=TODAY):


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

    return data

def fetch_all_entries_with_pagination(start_date, end_date, max_entries_per_request=1000):
    """
    Fetch all entries by automatically splitting date ranges when hitting limits
    """
    if not ensure_key_or_explain():
        return []
    

    all_entries = []

    # Filtering out the dates already present in the RAW_DIR.
    existing_dates= os.listdir(RAW_DIR)
    existing_dates= [item 
                     for x in existing_dates
                     for item in (x.split(".json")[0].split("raw_entries_")[1].split("_to_"))# split operation is from left to right. So, json will be received first. 
                    ]
    
    existing_dates= [dt.datetime.strptime(
    x, 
    '%Y-%m-%d'
).date() for x in existing_dates] 

    existing_dates_set= set(date for date in existing_dates if start_date<=date<=end_date) # The list comprehension inside is just for optimization. You could also just do set(existing_dates)
    all_dates_needed= set(daterange(start_date,end_date))
    missing_dates= all_dates_needed-existing_dates_set

    if not missing_dates:
        print("All data already exists!")
        return all_entries 

    start_date= min(missing_dates)
    end_date= max(missing_dates)
    

    current_start = start_date
      
    while current_start <= end_date:
        print(f"Fetching from {current_start} to {end_date}")
        
        
        entries = fetch_time_entries(since=current_start, today=end_date)
        
        if not entries:
            break
            
        all_entries.extend(entries)
        
        # If we got fewer than max, then we don't need multiple iterations.
        if len(entries) < max_entries_per_request:
            break
        
        # Get the last entry's date and continue from the next day
        last_entry_start = entries[-1]['start'][:10]  # Get date part
        current_start = (dt.datetime.strptime(last_entry_start, '%Y-%m-%d').date() # we doing this coz dt.date takes separate integer values.
        + dt.timedelta(days=1))
    
    missing_dates_ranges= date_2_range(sorted(missing_dates))

    for (start,end) in missing_dates_ranges: 

        data= [x for x in all_entries if start<=dt.datetime.strptime(x["start"][:10], '%Y-%m-%d').date()<=end]
        write_data(data,since=start,today=end)

def write_data(data: list,raw_dir=RAW_DIR,since=None,today=None): 

    if not since or not today: 
        since= min(dt.datetime.strptime(x["start"][:10], '%Y-%m-%d').date() for x in data)
        today= max(dt.datetime.strptime(x["start"][:10], '%Y-%m-%d').date() for x in data)
        
    outfile= os.path.join(raw_dir,f"raw_entries_{since}_to_{today}.json")

    with open(outfile,"w", encoding="utf-8") as file: 
        file.write(json.dumps(data,indent=2))

    print(f"Saved {len(data)} entries in {outfile}")


start_date = dt.date(2025, 7,18)  
end_date = dt.date(2025, 7, 21)     
fetch_all_entries_with_pagination(start_date,end_date)

