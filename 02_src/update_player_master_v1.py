import pandas as pd
import os
import glob

# =========================
# PATHS
# =========================
RAW_PATH = r"01_data/raw"
MASTER_PATH = r"01_data/processed/player_context/player_master.csv"

# =========================
# GET FILES
# =========================
batting_files = sorted(glob.glob(os.path.join(RAW_PATH, "*_batting.csv")))
pitching_files = sorted(glob.glob(os.path.join(RAW_PATH, "*_pitch*.csv")))

all_files = batting_files + pitching_files

print("=== FILES BEING LOADED ===")
for f in all_files:
    print(f)

# =========================
# LOAD DATA
# =========================
dfs = []

for file in all_files:
    df = pd.read_csv(file)

    if "player_id" not in df.columns or "last_name, first_name" not in df.columns:
        print(f"❌ Skipping (missing columns): {file}")
        continue

    temp = df[["player_id", "last_name, first_name"]].copy()
    temp = temp.rename(columns={"last_name, first_name": "player_name"})

    dfs.append(temp)

# =========================
# COMBINE
# =========================
players_df = pd.concat(dfs, ignore_index=True)

print(f"\nTotal rows before dedupe: {len(players_df)}")

# IMPORTANT: dedupe AFTER everything is loaded
players_df = players_df.drop_duplicates(subset=["player_id"])

print(f"Total unique players: {len(players_df)}")

# =========================
# LOAD EXISTING MASTER
# =========================
master_df = pd.read_csv(MASTER_PATH)

# =========================
# MERGE
# =========================
merged_df = players_df.merge(
    master_df,
    on="player_id",
    how="left",
    suffixes=("", "_existing")
)

# Keep existing names if needed
merged_df["player_name"] = merged_df["player_name"].fillna(merged_df["player_name_existing"])

# Preserve handedness
merged_df["bat_hand"] = merged_df["bat_hand"]
merged_df["throw_hand"] = merged_df["throw_hand"]

# =========================
# FINAL
# =========================
final_df = merged_df[["player_id", "player_name", "bat_hand", "throw_hand"]]
final_df = final_df.sort_values("player_id")

final_df.to_csv(MASTER_PATH, index=False)

print("\n✅ player_master.csv rebuilt successfully")