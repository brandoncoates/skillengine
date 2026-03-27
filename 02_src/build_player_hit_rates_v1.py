import os
import pandas as pd
import sys

def main():

    base_dir = os.path.dirname(os.path.abspath(__file__))

    if len(sys.argv) < 2:
        print("Usage: python build_player_hit_rates_v1.py <YYYY-MM-DD>")
        return

    slate_date = sys.argv[1]

    tracker_path = os.path.join(base_dir, f"../03_output/player_hit_tracker_master_{slate_date}.csv")

    if not os.path.exists(tracker_path):
        print("Tracker file not found.")
        return

    df = pd.read_csv(tracker_path)

    # -----------------------------
    # AGGREGATE
    # -----------------------------
    grouped = df.groupby("player_name").agg(
        total_games=("hit_flag", "count"),
        total_hits=("hit_flag", "sum")
    ).reset_index()

    # -----------------------------
    # HIT RATE
    # -----------------------------
    grouped["hit_rate"] = grouped["total_hits"] / grouped["total_games"]

    # -----------------------------
    # SORT
    # -----------------------------
    grouped = grouped.sort_values(
        by=["hit_rate", "total_games"],
        ascending=[False, False]
    )

    # -----------------------------
    # SAVE
    # -----------------------------
    if len(sys.argv) < 2:
        print("Usage: python build_player_hit_rates_v1.py <YYYY-MM-DD>")
        return

    slate_date = sys.argv[1]

    output_path = os.path.join(base_dir, f"../03_output/player_hit_rates_{slate_date}.csv")
    grouped.to_csv(output_path, index=False)

    print(f"Hit rates saved to: {output_path}")

if __name__ == "__main__":
    main()