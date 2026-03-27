import os
import sys
import pandas as pd

def main():

    # -----------------------------
    # DATE ARG (REQUIRED)
    # -----------------------------
    if len(sys.argv) < 2:
        print("Usage: python build_dfs_recap_v1.py <YYYY-MM-DD>")
        sys.exit(1)

    slate_date = sys.argv[1]

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # -----------------------------
    # LOAD HITTER PROJECTIONS
    # -----------------------------
    hitter_path = os.path.join(base_dir, f"../03_output/hitter_projections_dfs_{slate_date}.csv")
    hitters = pd.read_csv(hitter_path)

    # -----------------------------
    # LOAD PITCHER PROJECTIONS (OPTIONAL)
    # -----------------------------
    pitcher_path = os.path.join(base_dir, f"../03_output/pitcher_projections_dfs_{slate_date}.csv")

    if os.path.exists(pitcher_path):
        pitchers = pd.read_csv(pitcher_path)
        proj = pd.concat([hitters, pitchers], ignore_index=True)
        print("PROJ COLUMNS:", proj.columns.tolist())
        print(f"Loaded hitter + pitcher projections for {slate_date}")
    else:
        proj = hitters.copy()
        print(f"No pitcher projections file found for {slate_date} — using hitters only")

    # -----------------------------
    # LOAD ACTUALS
    # -----------------------------
    actual_path = os.path.join(base_dir, f"../03_output/actual_fd_points_{slate_date}.csv")
    actual = pd.read_csv(actual_path)

    # -----------------------------
    # CLEAN NAMES
    # -----------------------------
    proj["player_name"] = proj["player_name"].str.strip().str.lower()
    actual["player_name"] = actual["player_name"].str.strip().str.lower()

    # -----------------------------
    # LOAD FANDUEL SLATE
    # -----------------------------
    fanduel_path = os.path.join(base_dir, f"../01_data/raw/fanduel/FanDuel-MLB-{slate_date}.csv")
    fanduel = pd.read_csv(fanduel_path)

    # Normalize names
    fanduel["player_name"] = (
        fanduel["First Name"].str.strip().str.lower() + " " +
        fanduel["Last Name"].str.strip().str.lower()
    )

    # Add Position from FanDuel
    fanduel["Position"] = fanduel["Position"]

    # Keep only player names
    fanduel_players = set(fanduel["player_name"])

    # -----------------------------
    # MERGE
    # -----------------------------
    merged = proj.merge(
        actual[["player_name", "actual_fd_points"]],
        on="player_name",
        how="left"
    )

    # Merge in Position from FanDuel
    merged = merged.merge(
        fanduel[["player_name", "Position"]],
        on="player_name",
        how="left"
    )

    # -----------------------------
    # FILTER TO SLATE PLAYERS ONLY
    # -----------------------------
    merged = merged[merged["player_name"].isin(fanduel_players)].copy()

    # -----------------------------
    # CALCULATIONS
    # -----------------------------
    merged["point_diff"] = merged["actual_fd_points"] - merged["projected_fd_points"]
    merged["pct_diff"] = merged["point_diff"] / merged["projected_fd_points"]

    # -----------------------------
    # RESULT LABEL
    # -----------------------------
    def label(row):
        if pd.isna(row["actual_fd_points"]):
            return "DNP"
        elif row["actual_fd_points"] >= row["projected_fd_points"]:
            return "HIT"
        elif row["actual_fd_points"] >= row["projected_fd_points"] * 0.8:
            return "NEUTRAL"
        else:
            return "MISS"

    merged["result"] = merged.apply(label, axis=1)

    # -----------------------------
    # HIT FLAG (FOR TRACKING)
    # -----------------------------
    merged["hit_flag"] = (merged["result"] == "HIT").astype(int)

    # -----------------------------
    # SAVE
    # -----------------------------
    output_path = os.path.join(base_dir, f"../03_output/dfs_recap_{slate_date}.csv")
    
    # -----------------------------
    # RESULT RANK (FOR SORTING)
    # -----------------------------
    result_map = {
        "HIT": 1,
        "NEUTRAL": 2,
        "MISS": 3,
        "DNP": 4
    }

    merged["result_rank"] = merged["result"].map(result_map)

    # -----------------------------
    # SELECT FINAL COLUMNS (CLEAN OUTPUT)
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
        "pct_diff",
        "result",
        "result_rank",
        "hit_flag"
    ]

    merged = merged[final_cols]

    # Sort by result_rank (then best performers within each group)
    merged = merged.sort_values(
        by=["result_rank", "point_diff"],
        ascending=[True, False]
    )

    merged.to_csv(output_path, index=False)

    print(f"\nDFS recap saved to: {output_path}")

    # -----------------------------
    # SUMMARY
    # -----------------------------
    print("\nSUMMARY:")
    print(merged["result"].value_counts())

if __name__ == "__main__":
    main()