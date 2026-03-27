import os
import sys
import pandas as pd
from datetime import datetime

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Get slate date from command line (or default to today)
    if len(sys.argv) > 1:
        slate_date = sys.argv[1]
    else:
        slate_date = datetime.today().strftime("%Y-%m-%d")

    # Input: matchup dataset (already includes Vegas context)
    input_path = os.path.join(
        base_dir,
        f"../03_output/hitter_matchups_dfs_{slate_date}.csv"
    )

    # Output: scored DFS dataset
    output_path = os.path.join(
        base_dir,
        f"../03_output/hitter_scores_dfs_{slate_date}.csv"
    )

    df = pd.read_csv(input_path)

    # Load SkillEngine output (player ability baseline)
    skill_path = os.path.join(
        base_dir,
        "../03_output/2025_hitters_scored_v1.csv"
    )

    skill_df = pd.read_csv(skill_path)[["player_name", "SkillScore_v1"]]

    # ---------------------------------------------------------
    # Normalize player names to improve matching
    # ---------------------------------------------------------

    df["player_name_clean"] = (
        df["player_name"]
        .str.lower()
        .str.strip()
    )

    skill_df["player_name_clean"] = (
        skill_df["player_name"]
        .str.lower()
        .str.strip()
    )

    # Merge using cleaned names
    df = df.merge(
        skill_df[["player_name_clean", "SkillScore_v1"]],
        on="player_name_clean",
        how="left"
    )

    # Remove any invalid salary rows
    df = df[df["Salary"] > 0]

    # ---------------------------------------------------------
    # Build projected points using Skill + Vegas context
    # ---------------------------------------------------------

    # League baseline (average runs per team per game)
    LEAGUE_AVG_RUNS = 4.3

    # Vegas factor scales scoring environment
    # >1 = high scoring game, <1 = low scoring game
    df["vegas_factor"] = df["implied_team_total"] / LEAGUE_AVG_RUNS

    # Fill missing skill with baseline (league average)
    df["SkillScore_v1"] = df["SkillScore_v1"].fillna(df["SkillScore_v1"].mean())

    # Projected points = player skill × game environment
    df["projected_points"] = df["SkillScore_v1"] * df["vegas_factor"]

    # ---------------------------------------------------------
    # Convert projections into DFS value (points per dollar)
    # ---------------------------------------------------------

    df["value_score"] = df["projected_points"] / df["Salary"]

    # ---------------------------------------------------------
    # Normalize value into a 0–10 DFS score for ranking
    # ---------------------------------------------------------

    min_score = df["value_score"].min()
    max_score = df["value_score"].max()

    if max_score != min_score:
        df["dfs_score"] = (
            (df["value_score"] - min_score) /
            (max_score - min_score)
        ) * 10
    else:
        df["dfs_score"] = 5

    # Sort players from best to worst DFS value
    df = df.sort_values(by="dfs_score", ascending=False)

    # Save results
    df.to_csv(output_path, index=False)

    print(f"DFS scores saved to: {output_path}")


if __name__ == "__main__":
    main()