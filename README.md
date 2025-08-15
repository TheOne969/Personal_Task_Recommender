# Personal Task Recommender 📈

A one-stop productivity dashboard that pulls your Toggl time-tracking data, shows you exactly where the hours go, and recommends the **next best task** to work on.

---

## Contents
1. [Features](#features)
2. [Quick Demo Data](#quick-demo-data)
3. [Install & Run](#install--run)
4. [Project Structure](#project-structure)
5. [How it Works](#how-it-works)
6. [Requirements](#requirements)
7. [Future advancements](#future-advancements)


---

## Features

| Area | What you get |
|------|--------------|
| Data ingest | Pull any date range from Toggl (`scripts/fetch_toggl.py`) and store raw JSON + processed CSV. |
| Episode engine | Groups adjacent Toggl rows into “work sessions”; labels each session **completed / not-completed**. |
| Streamlit dashboard | Four tabs – **Analytics · Goals · Task Manager · Recommendations** |
| Weekly goals | Define targets in `configs/goals.json`; progress bars update live. |
| Task manager | CRUD UI backed by `configs/tasks.json`, difficulty picker, duration estimate. |
| Recommendation engine | Rule-based scoring (performance × goal urgency × difficulty) **plus optional ML multiplier** for completion likelihood. |
| One-click retrain | “♻️ Retrain completion model” button retrains `data/completion_model.joblib` and hot-loads it in the UI. |

---

## Quick Demo Data

Don’t have Toggl yet?  
Clone the repo and grab the **sample dataset + configs**:
```
data/
├─ raw/ 
├─ processed/ # sample.csv 
└─ completion_model.joblib # tiny dummy model

configs/
├─ tasks.json
├─ goals.json
└─ category_mapping.json
└─ config.json
```

With those files in place you can open the dashboard instantly and click around
without touching the Toggl API.

---

## Install & Run

1. clone

    git clone https://github.com/TheOne969/Personal_Task_Recommender.git 

    cd Personal_Task_Recommender

2. dependencies
    
    pip install -r requirements.txt # Python ≥3.9

3. (optional) set Toggl token
    
    export TOGGL_API_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

4. Create a .env file

    If you did the above, then add it in this file. Apart from that, add the following variables and their paths accordingly. 

    ```
    TOGGL_API_KEY=
        
    DATA_DIR=C:\Codes\Personal_Task_Recommender\data
    SCRIPTS_DIR=C:\Codes\Personal_Task_Recommender\scripts
    UI_DIR=C:\Codes\Personal_Task_Recommender\ui
    CONFIGS_DIR=C:\Codes\Personal_Task_Recommender\configs

    
    CONFIG_FILE=C:\Codes\Personal_Task_Recommender\configs\config.json
    GOALS_FILE=C:\Codes\Personal_Task_Recommender\configs\goals.json
    TASKS_FILE=C:\Codes\Personal_Task_Recommender\configs\tasks.json
    CATEGORY_MAPPING_FILE=C:\Codes\Personal_Task_Recommender\configs\category_mapping.json


    ```


5. start dashboard

    streamlit run ui/streamlit_app.py 
    
    reachable on http://localhost:8501



*Pull new data at any time with the **Fetch Data** button in the sidebar.*

---

## Project Structure
```
.
├─ configs/ # editable JSON/YAML for goals, tasks, mapping
├─ data/ # raw/processed CSV + trained model
├─ scripts/
    ├─ analytics.py              # Common aggregations used by the dashboard (total time, hours/day, etc.).

    ├─ category_mapping.py       # Maps Toggl projects/descriptions → goal categories

    ├─ daily_goals.py            # (Legacy) logic for simple daily-target tracking

    ├─ feature_engineering.py    # Builds TaskEvent rows: episode inference + feature columns for the ML model.

    ├─ fetch_toggl.py            # CLI client that paginates through the Toggl API and saves raw JSON.

    ├─ ml_events.py              # Dataclass definitions (`TaskEvent`) shared by ML scripts.

    ├─ path_manager.py           # Central place for folder paths so every script agrees on `data/`, `configs/`, etc.

    ├─ plots.py                  # Small wrappers around Seaborn/Matplotlib that return figure images to Streamlit.

    ├─ process.py                # Converts raw JSON → processed CSV (adds date columns, cleans tags).

    ├─ recommendation_engine.py  # Core scorer: rule-based weights + optional completion-probability multiplier.

    ├─ task_manager.py           # CRUD helper for tasks.json; exposed in the Task-Manager tab.

    ├─ train_completion_model.py # Trains `data/completion_model.joblib`, handling temporal split & class imbalance.

    └─ weekly_goals.py           # Loads goals.json; calculates per-week progress and goal urgency.


├─ ui/ # Streamlit app
└─ README.md
```
---

## How it Works

1. **fetch**  -> `fetch_toggl.py`  
   Pulls raw entries from Toggl → `data/raw/*.json`.

2. **process**  -> `process.py`  
   Cleans & flattens the JSON → `data/processed/*.csv`.

3. **analyze** -> Daily hours, rolling averages, project breakdowns. 
    `plots.py` convert those in visual graphs. 

4. **goals** ->  Live progress vs weekly targets from `goals.json`.
    `weekly_goals.py` manages this. 

5. **Task Mgr** -> CRUD UI for tasks stored in `tasks.json`. 
    `task_manager.py` manages this and `category_mapping.py` maps the task category to tasks. 


6. **Recommendations** -> Ranked “what should I do next?” list with reasoning & one-click model retrain. 
      `feature_engineering.py` + `ml_events.py` + `recommendation_engine.py` + `train_completion_model.py` does that. 

      The method used here is basically asking a small random forest classifier, “If you start this task now, how likely are you to finish the current sitting?”
      That probability (0 – 1) multiplies the rule-based score.

      Random Forest was chosen due to it being usable with little feature engineering and being fast to train. 

---

## Requirements

All needed libraries are present in requirements.txt

---

## Future advancements

  - Right now the ML completion model still needs more fine-tuning and more data to make it more accurate and check if it's predictions are actually correct or not when applied to real life scenarios. 

  Other possible furture advancements are: 
   - include asking for user's day to day energy levels and using that as an input variable. 
   - Making it deployable such that user could use it through their phone remotely. 
   - Making category_mapping more easier by introducing AI component in that as currently it requires manual work. 

  
  
 





---

