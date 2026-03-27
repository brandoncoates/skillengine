import os
import pandas as pd
import sys

if len(sys.argv) < 2:
    print("Usage: python build_manual_dfs_helper_v1.py <YYYY-MM-DD>")
    sys.exit(1)

slate_date = sys.argv[1]

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # -----------------------------
    # LOAD DFS POOL
    # -----------------------------
    pool_path = os.path.join(base_dir, f"../03_output/dfs_pool_{slate_date}.csv")
    df = pd.read_csv(pool_path)

    # -----------------------------
    # SPLIT DATA
    # -----------------------------
    pitchers = df[df["Position"] == "P"].copy()
    hitters = df[df["Position"] != "P"].copy()

    # -----------------------------
    # TOP 5 PITCHERS
    # -----------------------------
    top_pitchers = pitchers.sort_values("value_score", ascending=False).head(5)

    # -----------------------------
    # STACK TARGET TEAMS
    # -----------------------------
    # Find teams with best average value hitters
    team_scores = (
        hitters.groupby("team")["value_score"]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )

    top_teams = team_scores.head(5)["team"].tolist()

    stack_rows = []

    for team in top_teams:
        team_hitters = hitters[hitters["team"] == team].copy()

        team_hitters = team_hitters.sort_values("value_score", ascending=False).head(4)

        for _, row in team_hitters.iterrows():
            stack_rows.append({
                "team": team,
                "player_name": row["player_name"],
                "Position": row["Position"],
                "Salary": row["Salary"],
                "value_score": row["value_score"],
                "projected_fd_points": row["projected_fd_points"]
            })

    stacks_df = pd.DataFrame(stack_rows)

    # -----------------------------
    # TOP 20 VALUE HITTERS
    # -----------------------------
    top_hitters = hitters.sort_values("value_score", ascending=False).head(20)

    # -----------------------------
    # TOP 4 BY POSITION
    # -----------------------------
    positions = ["C", "1B", "2B", "3B", "SS", "OF"]

    positional_rows = []

    for pos in positions:
        pos_df = hitters[hitters["Position"].str.contains(pos, na=False)].copy()

        pos_df = pos_df.sort_values("value_score", ascending=False).head(4)

        for _, row in pos_df.iterrows():
            positional_rows.append({
                "Position": pos,
                "player_name": row["player_name"],
                "team": row["team"],
                "Salary": row["Salary"],
                "value_score": row["value_score"],
                "projected_fd_points": row["projected_fd_points"]
            })

    positional_df = pd.DataFrame(positional_rows)

    # -----------------------------
    # SAVE OUTPUTS
    # -----------------------------
    output_dir = os.path.join(base_dir, "../03_output")

    excel_path = os.path.join(output_dir, f"dfs_manual_helper_{slate_date}.xlsx")

    with pd.ExcelWriter(excel_path, engine="xlsxwriter") as writer:
        top_pitchers.to_excel(writer, sheet_name="Pitchers", index=False)
        stacks_df.to_excel(writer, sheet_name="Stacks", index=False)
        top_hitters.to_excel(writer, sheet_name="Top Hitters", index=False)
        positional_df.to_excel(writer, sheet_name="By Position", index=False)

    print(f"\nDFS Helper Excel Created: {excel_path}")


if __name__ == "__main__":
    main()