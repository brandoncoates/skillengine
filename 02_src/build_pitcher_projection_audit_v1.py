import os
import pandas as pd
import numpy as np

# =====================================================
# MLB DFS PITCHER PROJECTION AUDIT
# Reads dfs_recap_master.csv
# Outputs pitcher_projection_audit.csv
# =====================================================

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    input_path = os.path.join(
        base_dir,
        "../03_output/dfs_recap_master.csv"
    )

    output_path = os.path.join(
        base_dir,
        "../03_output/pitcher_projection_audit.csv"
    )

    # -----------------------------
    # LOAD DATA
    # -----------------------------
    df = pd.read_csv(input_path)

    # -----------------------------
    # CLEAN / FILTER
    # -----------------------------
    df["Position"] = df["Position"].astype(str)
    df["projected_fd_points"] = pd.to_numeric(
        df["projected_fd_points"],
        errors="coerce"
    )

    df["actual_fd_points"] = pd.to_numeric(
        df["actual_fd_points"],
        errors="coerce"
    )

    # Keep pitchers only
    pitchers = df[
        df["Position"].str.contains("P", na=False)
    ].copy()

    # Require actual scores
    pitchers = pitchers.dropna(
        subset=["actual_fd_points", "projected_fd_points"]
    )

    # -----------------------------
    # CALCULATED FIELDS
    # -----------------------------
    pitchers["diff"] = (
        pitchers["actual_fd_points"] -
        pitchers["projected_fd_points"]
    )

    pitchers["beat_projection"] = np.where(
        pitchers["actual_fd_points"] >= pitchers["projected_fd_points"],
        1,
        0
    )

    # Bust = under 25 FD
    pitchers["bust_under_25"] = np.where(
        pitchers["actual_fd_points"] < 25,
        1,
        0
    )

    # Quality = 30+
    pitchers["quality_30_plus"] = np.where(
        pitchers["actual_fd_points"] >= 30,
        1,
        0
    )

    # Smash = 45+
    pitchers["smash_45_plus"] = np.where(
        pitchers["actual_fd_points"] >= 45,
        1,
        0
    )

    # -----------------------------
    # GROUP BY PLAYER
    # -----------------------------
    grouped = pitchers.groupby("player_name").agg(
        games=("player_name", "size"),
        avg_proj=("projected_fd_points", "mean"),
        avg_actual=("actual_fd_points", "mean"),
        avg_diff=("diff", "mean"),
        hit_rate=("beat_projection", "mean"),
        bust_rate=("bust_under_25", "mean"),
        quality_rate=("quality_30_plus", "mean"),
        smash_rate=("smash_45_plus", "mean"),
        std_dev=("actual_fd_points", "std")
    ).reset_index()

    grouped["std_dev"] = grouped["std_dev"].fillna(0)

    # -----------------------------
    # SAMPLE FILTER
    # -----------------------------
    grouped = grouped[
        grouped["games"] >= 3
    ].copy()

    # -----------------------------
    # TRUST SCORE (0-100)
    # Cash oriented
    # -----------------------------
    grouped["trust_score"] = (
        (grouped["hit_rate"] * 35) +
        ((1 - grouped["bust_rate"]) * 35) +
        (grouped["quality_rate"] * 15) +
        (grouped["smash_rate"] * 5) +
        (np.minimum(grouped["games"], 12) / 12 * 10)
    )

    grouped["trust_score"] = grouped["trust_score"].round(1)

    # -----------------------------
    # ROUNDING
    # -----------------------------
    round_cols = [
        "avg_proj",
        "avg_actual",
        "avg_diff",
        "hit_rate",
        "bust_rate",
        "quality_rate",
        "smash_rate",
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

    print(f"\n✅ Saved pitcher audit file to: {output_path}")
    print(f"Rows: {len(grouped)}")


if __name__ == "__main__":
    main()