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
# CALCULATE TREND
# =========================
def get_trend(row):
    avg = row["last_5_avg"]
    actual = row["actual_fd_points"]

    if pd.isna(avg):
        return None

    if actual >= avg * 1.25:
        return "HOT"
    elif actual <= avg * 0.75:
        return "COLD"
    else:
        return "NEUTRAL"

df["trend_tag"] = df.apply(get_trend, axis=1)

# =========================
# SAVE
# =========================
df.to_csv(TRACKER_PATH, index=False)

print("✅ Trend tags added")