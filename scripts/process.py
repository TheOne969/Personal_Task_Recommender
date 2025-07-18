""" JSON --> CSV """

from pathlib import Path
import json
import pandas as pd

# ──────────────────────────────
# CONFIG ‒ edit as you like
# ──────────────────────────────
RAW_DIR      = Path(r"C:\Codes\Personal_Task_Recommender\data\raw")       # where raw_entries_*.json live
OUT_DIR      = Path(r"C:\Codes\Personal_Task_Recommender\data\processed")   # destination for CSVs
JSON_PATTERN = "raw_entries_*.json"     # glob pattern to select files
LOCAL_TZ     = "Asia/Kolkata"          # GMT+05:30
# ──────────────────────────────

# Columns needed for analytics / goals / recommendations
KEEP_COLS = [
    "id",
    "start",
    "stop",
    "duration",
    "project_id",
    "description",
    "tags",
]


def _list_to_string(v: list | None) -> str:
    """List → 'tag1;tag2'  |  None/empty → '' """
    return ";".join(map(str, v)) if isinstance(v, list) and v else "" #using map to make sure that numerical tags get converted to string


def process_file(json_path: Path) -> Path | None:
    """Convert one raw JSON file → processed CSV file."""
    entries = json.loads(json_path.read_text())

    if not entries:
        print(f"[WARN] {json_path.name} contains 0 entries – skipped.")
        return None

    df = pd.json_normalize(entries)

    # keep only required columns (if missing, ignore)
    df = df[[c for c in KEEP_COLS if c in df.columns]]

    # ── time-zone conversion ───────────────────────────────────────
    df["start"] = pd.to_datetime(df["start"], utc=True).dt.tz_convert(LOCAL_TZ)
    df["stop"]  = pd.to_datetime(df["stop"],  utc=True).dt.tz_convert(LOCAL_TZ)

    #  derived columns ───────────────────────────
    df["duration_h"] = df["duration"] / 3600.0
    df["date"]       = df["start"].dt.date
    df["weekday"]    = df["start"].dt.day_name()

    # Monday 00:00 local time
    df["week_start"] = (
        df["start"] - pd.to_timedelta(df["start"].dt.weekday, unit="D")
    ).dt.normalize()

    df["tag_string"] = df["tags"].apply(_list_to_string)
    # ────────────────────────────────────────────────────────────────


    csv_name = json_path.name.replace("raw_entries", "toggl_entries").replace(".json", ".csv")
    csv_path = OUT_DIR / csv_name
    df.to_csv(csv_path, index=False) # index= Decides whether the first column will be index or not. 
    # Also to_csv overwrites the existing path if present. 

    print(f" {json_path.name:<35} → {csv_path.name}   ({len(df)} rows)")
    return csv_path


def main() -> None:
    json_files = list(RAW_DIR.glob(JSON_PATTERN))
    if not json_files:
        print(f"No files matching {JSON_PATTERN} found in {RAW_DIR}. Nothing to do.")
        return

    for j in json_files:
        process_file(j)


if __name__ == "__main__":
    main()