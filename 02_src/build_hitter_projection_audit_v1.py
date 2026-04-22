import os
import pandas as pd
import numpy as np

# =====================================================
# MLB DFS HITTER PROJECTION AUDIT
# Reads dfs_recap_master.csv
# Outputs hitter_projection_audit.csv
# =====================================================

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    input_path = os.path.join(base_dir, "../03_output/dfs_recap_master.csv")
    output_path = os.path.join(base_dir, "../03_output/hitter_projection_audit.csv")

    # -----------------------------
    # LOAD DATA
    # -----------------------------
    df = pd.read_csv(input_path)

    # -----------------------------
    # CLEAN / FILTER
    # -----------------------------
    df["Position"] = df["Position"].astype(str)
    df["projected_fd_points"] = pd.to_numeric(df["projected_fd_points"], errors="coerce")
    df["actual_fd_points"] = pd.to_numeric(df["actual_fd_points"], errors="coerce")

    # Remove pitchers
    hitters = df[~df["Position"].str.contains("P", na=False)].copy()

    # Require actual scores
    hitters = hitters.dropna(subset=["actual_fd_points", "projected_fd_points"])

    # -----------------------------
    # CALCULATED FIELDS
    # -----------------------------
    hitters["diff"] = hitters["actual_fd_points"] - hitters["projected_fd_points"]

    hitters["beat_projection"] = np.where(
        hitters["actual_fd_points"] >= hitters["projected_fd_points"], 1, 0
    )

    hitters["bust_under_6"] = np.where(
        hitters["actual_fd_points"] < 6, 1, 0
    )

    hitters["smash_15_plus"] = np.where(
        hitters["actual_fd_points"] >= 15, 1, 0
    )

    # -----------------------------
    # GROUP BY PLAYER
    # -----------------------------
    grouped = hitters.groupby("player_name").agg(
        games=("player_name", "size"),
        avg_proj=("projected_fd_points", "mean"),
        avg_actual=("actual_fd_points", "mean"),
        avg_diff=("diff", "mean"),
        hit_rate=("beat_projection", "mean"),
        bust_rate=("bust_under_6", "mean"),
        smash_rate=("smash_15_plus", "mean"),
        std_dev=("actual_fd_points", "std")
    ).reset_index()

    grouped["std_dev"] = grouped["std_dev"].fillna(0)

    # -----------------------------
    # SAMPLE FILTER
    # -----------------------------
    grouped = grouped[grouped["games"] >= 5].copy()

    # -----------------------------
    # TRUST SCORE (0-100)
    # -----------------------------
    grouped["trust_score"] = (
        (grouped["hit_rate"] * 40) +
        ((1 - grouped["bust_rate"]) * 30) +
        (grouped["smash_rate"] * 15) +
        (np.minimum(grouped["games"], 15) / 15 * 15)
    )

    grouped["trust_score"] = grouped["trust_score"].round(1)

    # -----------------------------
    # ROUNDING
    # -----------------------------
    round_cols = [
        "avg_proj", "avg_actual", "avg_diff",
        "hit_rate", "bust_rate", "smash_rate",
        "std_dev"
    ]

    for col in round_cols:
        grouped[col] = grouped[col].round(3)

    # -----------------------------
    # SORT
    # -----------------------------
    grouped = grouped.sort_values(
        ["trust_score", "avg_actual"],
        ascending=[False, False]
    )

    # -----------------------------
    # SAVE
    # -----------------------------
    grouped.to_csv(output_path, index=False)

    print(f"\n✅ Saved hitter audit file to: {output_path}")
    print(f"Rows: {len(grouped)}")


if __name__ == "__main__":
    main()