import pandas as pd
import os

# =========================
# PATH
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRACKER_PATH = os.path.join(BASE_DIR, "../03_output/dfs_recap_master.csv")

# =========================
# LOAD
# =========================
df = pd.read_csv(TRACKER_PATH)

# =========================
# CLEAN DATE
# =========================
df["slate_date"] = pd.to_datetime(df["slate_date"])

# =========================
# SORT (GLOBAL)
# =========================
df = df.sort_values(["player_id", "slate_date"])

# =========================
# CALCULATE ROLLING STATS
# =========================
def add_rolling(group):
    group = group.sort_values("slate_date").reset_index(drop=True)

    group["last_3_avg"] = (
        group["actual_fd_points"]
        .shift(1)
        .rolling(window=3, min_periods=1)
        .mean()
    )

    group["last_5_avg"] = (
        group["actual_fd_points"]
        .shift(1)
        .rolling(window=5, min_periods=1)
        .mean()
    )

    group["last_10_avg"] = (
        group["actual_fd_points"]
        .shift(1)
        .rolling(window=10, min_periods=1)
        .mean()
    )

    return group

df = df.groupby("player_id", group_keys=False).apply(add_rolling)

# =========================
# SAVE
# =========================
df.to_csv(TRACKER_PATH, index=False)

print("✅ Rolling performance columns fixed")