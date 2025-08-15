from pathlib import Path
from path_manager import paths

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score


# ────────────────────────────────────────────────────────────
DATA_DIR  = paths.data_dir / "processed"
MODEL_OUT = paths.data_dir / "completion_model.joblib"

# ── helpers ─────────────────────────────────────────────────
def safe_predict_proba(model, X):
    """Return P(class=1). If model was trained on one class only, return zeros."""
    proba = model.predict_proba(X)
    return proba[:, 1] if proba.shape[1] == 2 else np.zeros(len(X))

def safe_auc(y_true, y_score):
    """AUC or NaN when the slice contains <2 classes."""
    return roc_auc_score(y_true, y_score) if len(set(y_true)) == 2 else float("nan")

def balance_classes(df):
    """Down-sample majority class for a balanced dataset."""
    pos = df[df.completed == 1]
    neg = df[df.completed == 0]
    if len(pos) == 0 or len(neg) == 0:
        return df
    n = min(len(pos), len(neg))
    return pd.concat(
        [pos.sample(n, random_state=42), neg.sample(n, random_state=42)],
        ignore_index=True,
    )

# ── main training routine ───────────────────────────────────
def main():
    # Importing now to avoid the API requirement at import time. 
    from feature_engineering import toggl_df_to_events
    from task_manager import TaskManager
    from weekly_goals import WeeklyGoalTracker

    # 1  Load ONLY raw Toggl exports (exclude task_events.csv)
    csv_files = [f for f in DATA_DIR.glob("*.csv") if f.name != "task_events.csv"]
    df_list   = []
    for f in csv_files:
        df = pd.read_csv(f)
        if "start" not in df.columns:
            print(f"⚠️  {f.name} skipped (no 'start' column)")
            continue
        df["start"] = pd.to_datetime(df["start"])
        df_list.append(df)

    if not df_list:
        print("No usable CSVs found — aborting.")
        return

    entries_df = pd.concat(df_list, ignore_index=True)

    # 2  Generate TaskEvents
    tm = TaskManager()
    wg = WeeklyGoalTracker()
    events = toggl_df_to_events(entries_df, tm, wg)
    events.to_csv(DATA_DIR / "task_events.csv", index=False)

    # 3  Balance classes
    events = balance_classes(events)

    # 4  Temporal split 70/15/15
    cut_train = events["started_at"].quantile(0.70)
    cut_valid = events["started_at"].quantile(0.85)
    train_df  = events[events["started_at"] <= cut_train]
    val_df    = events[(events["started_at"] > cut_train) & (events["started_at"] <= cut_valid)]
    test_df   = events[events["started_at"] > cut_valid]

    X_cols = ["perf_score_at_start", "hour_of_day", "difficulty", "category_completion"]
    X_tr, y_tr = train_df[X_cols], train_df["completed"]
    X_va, y_va = val_df[X_cols],   val_df["completed"]
    X_te, y_te = test_df[X_cols],  test_df["completed"]

    # 5  Fit model
    model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
    model.fit(X_tr, y_tr)

    print("Validation AUC:", safe_auc(y_va, safe_predict_proba(model, X_va)))

    # 6  Retrain on train+val; evaluate on test
    model.fit(pd.concat([X_tr, X_va]), pd.concat([y_tr, y_va]))
    print("Test AUC:", safe_auc(y_te, safe_predict_proba(model, X_te)))

    joblib.dump(model, MODEL_OUT)
    print("Model saved →", MODEL_OUT)

# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
