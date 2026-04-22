import pandas as pd
import os


def normalize_name(name):
    return str(name).strip().lower()


def reverse_name(name):
    # Convert "Last, First" → "first last"
    if "," in name:
        last, first = name.split(",", 1)
        return f"{first.strip()} {last.strip()}".lower()
    return name.lower()


# =========================
# PATHS
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TRACKER_PATH = os.path.join(BASE_DIR, "../03_output/dfs_recap_master.csv")
MASTER_PATH = os.path.join(BASE_DIR, "../01_data/processed/player_context/player_master.csv")

# =========================
# LOAD FILES
# =========================
tracker_df = pd.read_csv(TRACKER_PATH)
master_df = pd.read_csv(MASTER_PATH)

# =========================
# NORMALIZE NAMES
# =========================
tracker_df["name_key"] = tracker_df["player_name"].apply(normalize_name)
master_df["name_key"] = master_df["player_name"].apply(reverse_name)

# =========================
# MERGE
# =========================
merged = tracker_df.merge(
    master_df[["player_id", "name_key"]],
    on="name_key",
    how="left"
)

# =========================
# CLEAN
# =========================
merged = merged.drop(columns=["name_key"])

# =========================
# SAVE
# =========================
merged.to_csv(TRACKER_PATH, index=False)

print("✅ player_id added to dfs_recap_master.csv")