import os
import sys
import pandas as pd

def main():

    if len(sys.argv) < 2:
        print("Usage: python build_dfs_tracking_v1.py <YYYY-MM-DD>")
        return

    slate_date = sys.argv[1]

    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "../03_output")

    # -----------------------------
    # LOAD RECAP (TODAY)
    # -----------------------------
    recap_path = os.path.join(output_dir, f"dfs_recap_{slate_date}.csv")
    recap = pd.read_csv(recap_path)

    # -----------------------------
    # LOAD HIT RATES (HISTORY)
    # -----------------------------
    hit_rate_path = os.path.join(output_dir, f"player_hit_rates_{slate_date}.csv")
    hit_rates = pd.read_csv(hit_rate_path)

    # -----------------------------
    # MERGE
    # -----------------------------
    merged = recap.merge(
        hit_rates,
        on="player_name",
        how="left"
    )

    # -----------------------------
    # SELECT FINAL COLUMNS
    # -----------------------------
    final_cols = [
        "player_name",
        "Position",
        "team",
        "opponent",
        "Salary",
        "projected_fd_points",
        "value_score",
        "actual_fd_points",
        "point_diff",
        "abs_point_diff",
        "pct_diff",
        "abs_pct_diff",
        "projection_direction",
        "projection_accuracy_bucket",
        "total_games",
        "total_hits",
        "hit_rate"
    ]

    merged = merged[final_cols]

    # -----------------------------
    # SAVE
    # -----------------------------
    output_path = os.path.join(output_dir, f"dfs_tracking_{slate_date}.csv")
    merged.to_csv(output_path, index=False)

    print(f"\nDFS tracking file saved: {output_path}")

if __name__ == "__main__":
    main()