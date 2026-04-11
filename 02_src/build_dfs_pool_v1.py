import os
import pandas as pd
import sys

if len(sys.argv) < 2:
    print("Usage: python build_dfs_pool_v1.py <YYYY-MM-DD>")
    sys.exit(1)

slate_date = sys.argv[1]

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # -----------------------------
    # INPUT FILES
    # -----------------------------
    hitters_path = os.path.join(base_dir, f"../03_output/hitter_projections_dfs_{slate_date}.csv")
    pitchers_path = os.path.join(base_dir, f"../03_output/pitcher_projections_dfs_{slate_date}.csv")

    hitters = pd.read_csv(hitters_path)
    pitchers = pd.read_csv(pitchers_path)

    # Normalize names
    hitters["player_name"] = hitters["player_name"].str.strip().str.lower()
    pitchers["player_name"] = pitchers["player_name"].str.strip().str.lower()

    # -----------------------------
    # LOAD FANDUEL DATA
    # -----------------------------
    fanduel_path = os.path.join(base_dir, f"../01_data/raw/fanduel/FanDuel-MLB-{slate_date}.csv")
    fanduel = pd.read_csv(fanduel_path)

    fanduel["player_name"] = (
        fanduel["First Name"].str.strip().str.lower() + " " +
        fanduel["Last Name"].str.strip().str.lower()
    )

    fanduel_clean = fanduel[[
        "player_name",
        "Position",
        "Team",
        "Opponent"
    ]].copy()

    fanduel_clean = fanduel_clean.rename(columns={
        "Team": "team",
        "Opponent": "opponent"
    })

    # -----------------------------
    # MERGE
    # -----------------------------
    hitters = hitters.merge(fanduel_clean, on="player_name", how="left", suffixes=("", "_fd"))
    hitters["team"] = hitters["team_fd"]
    hitters["opponent"] = hitters["opponent_fd"]

    pitchers = pitchers.merge(fanduel_clean, on="player_name", how="left")

    # -----------------------------
    # SELECT COLUMNS
    # -----------------------------
    hitters_clean = hitters[[
        "player_name",
        "Position",
        "team",
        "opponent",
        "Salary",
        "projected_fd_points",
        "value_score",
        "implied_team_total",
        "wind_score"
    ]].copy()

    pitchers_clean = pitchers[[
        "player_name",
        "Position",
        "team",
        "opponent",
        "Salary",
        "projected_fd_points",
        "value_score"
    ]].copy()

    pitchers_clean["implied_team_total"] = None
    pitchers_clean["wind_score"] = None

    # =========================================================
    # 🎯 FIX: SORT EACH GROUP PROPERLY
    # =========================================================

    # Hitters → value-driven
    hitters_clean = hitters_clean.sort_values("value_score", ascending=False)

    # Pitchers → projection-driven
    pitchers_clean = pitchers_clean.sort_values(
        ["projected_fd_points", "value_score"],
        ascending=[False, False]
    )

    # -----------------------------
    # COMBINE
    # -----------------------------
    combined = pd.concat([hitters_clean, pitchers_clean], ignore_index=True)

    # 🔥 DO NOT RESORT HERE

    # -----------------------------
    # SAVE
    # -----------------------------
    output_path = os.path.join(base_dir, f"../03_output/dfs_pool_{slate_date}.csv")
    combined.to_csv(output_path, index=False)

    print(f"\nDFS pool saved to: {output_path}")


if __name__ == "__main__":
    main()