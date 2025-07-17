""" Getting data from Toggl """

import os, json, requests, datetime as dt
from dotenv import load_dotenv

load_dotenv(r"C:\Codes\personal_task_rec\configs\.env")

TODAY = dt.date.today()
SINCE = TODAY - dt.timedelta(days=7) # To get the date one week before. 
RAW_DIR= r"C:\Codes\personal_task_rec\data\raw"
PROCESSED_DIR= r"C:\Codes\personal_task_rec\data\processed"
TOKEN= os.getenv("TOGGL_API_KEY")

if not TOKEN:
    raise ValueError("TOGGL_API_KEY not found in environment variables.")



url = "https://api.track.toggl.com/api/v9/me/time_entries"
params = {
    "start_date": SINCE.isoformat(),
    "end_date": TODAY.isoformat()
}
print(f"📅 Fetching from {SINCE} to {TODAY}")

r = requests.get(url, params=params, auth=(TOKEN, "api_token"))
print(f"Status: {r.status_code}")  # Debug line

print(f"URL: {r.url}")

if r.status_code != 200:
    print(f"Error: {r.text}")

r.raise_for_status()
data = r.json()

outfile= os.path.join(RAW_DIR,f"raw_entries_{SINCE}_to_{TODAY}.json")
with open(outfile,"w", encoding="utf-8") as file: 
    file.write(json.dumps(data,indent=2))

print(f"Saved {len(data)} entries in {outfile}")



