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
# MULTIPLIER
# =========================
def get_multiplier(tag):
    if tag == "HOT":
        return 1.10
    elif tag == "COLD":
        return 0.90
    else:
        return 1.00

df["trend_multiplier"] = df["trend_tag"].apply(get_multiplier)

# =========================
# ADJUST PROJECTION
# =========================
df["adjusted_fd_points"] = df.apply(
    lambda row: row["projected_fd_points"] * row["trend_multiplier"]
    if row["projection_direction"] != "NO_DATA"
    else None,
    axis=1
)

# =========================
# SAVE
# =========================
df.to_csv(TRACKER_PATH, index=False)

print("✅ Trend adjustment added")