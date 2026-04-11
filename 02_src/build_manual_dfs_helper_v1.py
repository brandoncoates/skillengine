import os
import pandas as pd
import sys

if len(sys.argv) < 2:
    print("Usage: python build_manual_dfs_helper_v1.py <YYYY-MM-DD>")
    sys.exit(1)

slate_date = sys.argv[1]

def format_pitcher(row):
    return (
        f"{row['player_name'].title()} – {row['Position']} – {row['team']} vs {row['opponent']} "
        f"| ${row['Salary']} | FD: {round(row['projected_fd_points'],1)} | Value: {round(row['value_score'],2)}"
    )

def format_hitter(row):
    return (
        f"{row['Position']} – {row['player_name'].title()} – {row['team']} vs {row['opponent']} "
        f"| ${row['Salary']} | FD: {round(row['projected_fd_points'],1)} | Value: {round(row['value_score'],2)}"
    )

def format_stack(row):
    return (
        f"{row['team']} – {row['Position']} – {row['player_name'].title()} "
        f"| ${row['Salary']} | FD: {round(row['projected_fd_points'],1)} | Value: {round(row['value_score'],2)}"
    )

def format_positional(row):
    return (
        f"{row['Position']} – {row['player_name'].title()} – {row['team']} "
        f"| ${row['Salary']} | FD: {round(row['projected_fd_points'],1)} | Value: {round(row['value_score'],2)}"
    )

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    pool_path = os.path.join(base_dir, f"../03_output/dfs_pool_{slate_date}.csv")
    df = pd.read_csv(pool_path)

    pitchers = df[df["Position"] == "P"].copy()
    hitters = df[df["Position"] != "P"].copy()

    # =============================
    # PITCHERS
    # =============================
    top_pitchers = (
        pitchers
        .sort_values(["projected_fd_points", "value_score"], ascending=[False, False])
        .head(5)[[
            "player_name","Position","team","opponent","Salary","projected_fd_points","value_score"
        ]]
    )

    top_pitchers["formatted"] = top_pitchers.apply(format_pitcher, axis=1)

    # =============================
    # STACKS
    # =============================
    team_scores = (
        hitters.groupby("team")
        .agg({
            "value_score": "mean",
            "implied_team_total": "mean",
            "wind_score": "mean"
        })
        .reset_index()
    )

    team_scores["stack_score"] = (
        team_scores["implied_team_total"] +
        (team_scores["wind_score"] * 0.5)
    )

    team_scores = team_scores.sort_values("stack_score", ascending=False)
    top_teams = team_scores.head(5)["team"].tolist()

    stack_rows = []

    for team in top_teams:
        team_hitters = hitters[hitters["team"] == team].copy()
        team_hitters = team_hitters.sort_values(
            ["projected_fd_points", "value_score"],
            ascending=[False, False]
        ).head(4)

        team_stack_score = team_scores.loc[
            team_scores["team"] == team, "stack_score"
        ].values[0]

        for _, row in team_hitters.iterrows():
            stack_rows.append({
                "team": team,
                "player_name": row["player_name"],
                "Position": row["Position"],
                "Salary": row["Salary"],
                "value_score": row["value_score"],
                "projected_fd_points": row["projected_fd_points"],
                "stack_score": team_stack_score,
                "formatted": format_stack(row)
            })

    stacks_df = pd.DataFrame(stack_rows)

    # =============================
    # TOP HITTERS
    # =============================
    top_hitters = (
        hitters
        .sort_values(["projected_fd_points", "value_score"], ascending=[False, False])
        .head(20)[[
            "player_name","Position","team","opponent","Salary","projected_fd_points","value_score"
        ]]
    )

    top_hitters["formatted"] = top_hitters.apply(format_hitter, axis=1)

    # =============================
    # BY POSITION
    # =============================
    positions = ["C", "1B", "2B", "3B", "SS", "OF"]

    positional_rows = []

    for pos in positions:
        pos_df = hitters[hitters["Position"].str.contains(pos, na=False)].copy()
        pos_df = pos_df.sort_values(
            ["projected_fd_points", "value_score"],
            ascending=[False, False]
        ).head(4)

        for _, row in pos_df.iterrows():
            row_dict = {
                "Position": pos,
                "player_name": row["player_name"],
                "team": row["team"],
                "Salary": row["Salary"],
                "value_score": row["value_score"],
                "projected_fd_points": row["projected_fd_points"],
                "formatted": format_positional({
                    "Position": pos,
                    "player_name": row["player_name"],
                    "team": row["team"],
                    "Salary": row["Salary"],
                    "value_score": row["value_score"],
                    "projected_fd_points": row["projected_fd_points"]
                })
            }
            positional_rows.append(row_dict)

    positional_df = pd.DataFrame(positional_rows)

    # =============================
    # SAVE
    # =============================
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