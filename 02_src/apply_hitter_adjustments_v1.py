import os
import pandas as pd
import numpy as np
import sys

# =====================================================
# APPLY HITTER ADJUSTMENTS
# Uses hitter_projection_audit.csv to tune today's hitters
# =====================================================

if len(sys.argv) < 2:
    print("Usage: python apply_hitter_adjustments_v1.py <YYYY-MM-DD>")
    sys.exit(1)

slate_date = sys.argv[1]


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    proj_path = os.path.join(
        base_dir,
        f"../03_output/hitter_projections_dfs_{slate_date}.csv"
    )

    audit_path = os.path.join(
        base_dir,
        "../03_output/hitter_projection_audit.csv"
    )

    output_path = os.path.join(
        base_dir,
        f"../03_output/hitter_projections_adjusted_{slate_date}.csv"
    )

    # -----------------------------
    # LOAD FILES
    # -----------------------------
    proj = pd.read_csv(proj_path)
    audit = pd.read_csv(audit_path)

    # -----------------------------
    # CLEAN NAMES
    # -----------------------------
    proj["player_name"] = (
        proj["player_name"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    audit["player_name"] = (
        audit["player_name"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    # -----------------------------
    # MERGE
    # -----------------------------
    df = proj.merge(
        audit[[
            "player_name",
            "trust_score",
            "avg_diff",
            "bust_rate",
            "smash_rate"
        ]],
        on="player_name",
        how="left"
    )

    # -----------------------------
    # DEFAULTS FOR NEW PLAYERS
    # -----------------------------
    df["trust_score"] = df["trust_score"].fillna(50)
    df["avg_diff"] = df["avg_diff"].fillna(0)
    df["bust_rate"] = df["bust_rate"].fillna(0.35)
    df["smash_rate"] = df["smash_rate"].fillna(0.15)

    # -----------------------------
    # ADJUSTMENT MULTIPLIER
    # -----------------------------
    multiplier = np.ones(len(df))

    # Trust score boost / penalty
    multiplier += np.where(df["trust_score"] >= 75, 0.05, 0)
    multiplier += np.where(df["trust_score"] <= 40, -0.06, 0)

    # Avg diff boost / penalty
    multiplier += np.where(df["avg_diff"] >= 1.5, 0.04, 0)
    multiplier += np.where(df["avg_diff"] <= -1.5, -0.05, 0)

    # Bust rate penalty
    multiplier += np.where(df["bust_rate"] >= 0.50, -0.06, 0)
    multiplier += np.where(df["bust_rate"] <= 0.25, 0.03, 0)

    # Smash upside small reward
    multiplier += np.where(df["smash_rate"] >= 0.30, 0.02, 0)

    # Clamp so nothing crazy happens
    multiplier = np.clip(multiplier, 0.82, 1.18)

    df["hitter_adjustment_multiplier"] = multiplier.round(3)

    # -----------------------------
    # APPLY TO PROJECTION
    # -----------------------------
    df["original_fd_points"] = df["projected_fd_points"]

    df["projected_fd_points"] = (
        df["projected_fd_points"] *
        df["hitter_adjustment_multiplier"]
    ).round(3)

    # -----------------------------
    # SORT
    # -----------------------------
    if "value_score" in df.columns:
        df["value_score"] = (
            df["projected_fd_points"] /
            (df["Salary"] / 1000)
        ).round(2)

        df = df.sort_values(
            ["value_score", "projected_fd_points"],
            ascending=[False, False]
        )
    else:
        df = df.sort_values(
            "projected_fd_points",
            ascending=False
        )

    # -----------------------------
    # SAVE
    # -----------------------------
    df.to_csv(output_path, index=False)

    print(f"\n✅ Saved adjusted hitter file:")
    print(output_path)
    print(f"Rows: {len(df)}")


if __name__ == "__main__":
    main()