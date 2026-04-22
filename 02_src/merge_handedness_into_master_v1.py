import pandas as pd
import os

# =========================
# PATHS
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MASTER_PATH = os.path.join(BASE_DIR, "../01_data/processed/player_context/player_master.csv")
HANDEDNESS_PATH = os.path.join(BASE_DIR, "../01_data/processed/player_context/player_handedness.csv")

# =========================
# LOAD FILES
# =========================
master_df = pd.read_csv(MASTER_PATH)
hand_df = pd.read_csv(HANDEDNESS_PATH)

# =========================
# CLEAN
# =========================
hand_df = hand_df.drop_duplicates(subset=["player_id"])

# =========================
# MERGE
# =========================
merged = master_df.merge(
    hand_df[["player_id", "bat_hand", "throw_hand"]],
    on="player_id",
    how="left",
    suffixes=("", "_new")
)

# =========================
# FILL MISSING HANDEDNESS
# =========================
merged["bat_hand"] = merged["bat_hand"].fillna(merged["bat_hand_new"])
merged["throw_hand"] = merged["throw_hand"].fillna(merged["throw_hand_new"])

# =========================
# FINAL CLEAN
# =========================
final_df = merged[["player_id", "player_name", "bat_hand", "throw_hand"]]

# =========================
# SAVE
# =========================
final_df.to_csv(MASTER_PATH, index=False)

print("✅ player_master.csv updated with handedness")