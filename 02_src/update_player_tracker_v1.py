import os
import sys
import pandas as pd

def main():

    if len(sys.argv) < 2:
        print("Usage: python update_player_tracker_v1.py <YYYY-MM-DD>")
        sys.exit(1)

    slate_date = sys.argv[1]

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # -----------------------------
    # LOAD RECAP FILE
    # -----------------------------
    recap_path = os.path.join(base_dir, f"../03_output/dfs_recap_{slate_date}.csv")

    if not os.path.exists(recap_path):
        print(f"Recap file not found: {recap_path}")
        sys.exit(1)

    recap = pd.read_csv(recap_path)

    # -----------------------------
    # SELECT TRACKING FIELDS
    # -----------------------------
    tracker_df = recap[[
        "player_name",
        "Position",
        "team",
        "hit_flag"
    ]].copy()

    tracker_df["date"] = slate_date

    # -----------------------------
    # TRACKER FILE PATH
    # -----------------------------
    tracker_path = os.path.join(base_dir, f"../03_output/player_hit_tracker_{slate_date}.csv")

    # -----------------------------
    # OVERWRITE DAILY TRACKER FILE
    # -----------------------------
    combined = tracker_df.copy()
    
    # -----------------------------
    # SAVE
    # -----------------------------
    combined.to_csv(tracker_path, index=False)

    print(f"Tracker updated: {tracker_path}")

if __name__ == "__main__":
    main()