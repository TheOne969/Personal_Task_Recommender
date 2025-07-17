from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns


sns.set_theme(style="darkgrid")          # global look-and-feel for all plots.

# --- Generic helper to return a PNG buffer Streamlit can display ---
def _to_png(fig):
    buf = BytesIO() # creates a buffer. 
    fig.tight_layout()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf

# 1. Bar chart – hours per day
def bar_hours_per_day(daily_df):
    fig, ax = plt.subplots(figsize=(8, 3.5))
    sns.barplot(data=daily_df, x="start", y="hours", color="steelblue", ax=ax)
    ax.set_title("Hours per Day")
    ax.set_xlabel("Date")
    ax.set_ylabel("Hours")
    ax.tick_params(axis="x", rotation=45)
    return _to_png(fig)

# 2. Pie chart – distribution by project
def pie_by_project(proj_df):
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(
        proj_df["hours"],
        labels=proj_df["project"],
        autopct="%1.1f%%",
        startangle=140,
        colors=sns.color_palette("pastel", len(proj_df)),
    )
    ax.set_title("Time Distribution by Project")
    return _to_png(fig)

# 3. Line chart – 7-day rolling average
def rolling_avg_line(daily_df):
    d = daily_df.sort_values("start").copy()
    d["rolling"] = d["hours"].rolling(7, min_periods=1).mean()
    fig, ax = plt.subplots(figsize=(8, 3.5))
    sns.lineplot(data=d, x="start", y="rolling", marker="o", ax=ax)
    ax.set_title("7-Day Rolling Avg of Hours")
    ax.set_xlabel("Date")
    ax.set_ylabel("Hours (rolling avg)")
    ax.tick_params(axis="x", rotation=45)
    return _to_png(fig)
