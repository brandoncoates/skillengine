import os
import pandas as pd
import unicodedata
import sys

if len(sys.argv) < 2:
    print("Usage: python build_pitcher_projections_v1.py <YYYY-MM-DD>")
    sys.exit(1)

slate_date = sys.argv[1]

def normalize_name(name):
    if pd.isna(name):
        return name
    name = str(name).strip().lower()
    name = unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("utf-8")
    return name

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # -----------------------------
    # INPUT FILES
    # -----------------------------
    pitcher_path = os.path.join(base_dir, "../03_output/2025_pitchers_master.csv")
    salary_path = os.path.join(base_dir, f"../01_data/raw/fanduel/FanDuel-MLB-{slate_date}.csv")

    df = pd.read_csv(pitcher_path)
    salary_df = pd.read_csv(salary_path)

    # -----------------------------
    # FILTER PITCHERS FROM FD FILE
    # -----------------------------
    pitcher_salary_df = salary_df[
        (salary_df["Position"] == "P") &
        (salary_df["Probable Pitcher"] == "Yes")
    ].copy()

    pitcher_salary_df["player_name"] = (
        pitcher_salary_df["First Name"].str.strip() + " " +
        pitcher_salary_df["Last Name"].str.strip()
    )

    pitcher_salary_df["player_name"] = pitcher_salary_df["player_name"].apply(normalize_name)
    df["player_name"] = df["player_name"].apply(normalize_name)

    pitcher_salary_df = pitcher_salary_df[["player_name", "Salary"]]

    # -----------------------------
    # PROJECTED IP
    # -----------------------------
    df["IP_per_game"] = df["IP"] / df["p_game"]
    df["projected_IP"] = df["IP_per_game"]

    # -----------------------------
    # STRIKEOUTS + EARNED RUNS
    # -----------------------------
    df["K_per_IP"] = df["SO"] / df["IP"]
    df["proj_SO"] = df["projected_IP"] * df["K_per_IP"]

    df["ER_per_IP"] = df["ERA"] / 9
    df["proj_ER"] = df["projected_IP"] * df["ER_per_IP"]

    # -----------------------------
    # MERGE SALARY
    # -----------------------------
    df = df.merge(pitcher_salary_df, on="player_name", how="left")

    # -----------------------------
    # ADD MISSING FD PITCHERS
    # -----------------------------
    model_pitchers = set(df["player_name"])
    fd_pitchers = set(pitcher_salary_df["player_name"])

    missing_pitchers = fd_pitchers - model_pitchers

    if missing_pitchers:
        missing_rows = pitcher_salary_df[
            pitcher_salary_df["player_name"].isin(missing_pitchers)
        ].copy()

        missing_rows["projected_IP"] = 5.0
        missing_rows["proj_SO"] = 4.5
        missing_rows["proj_ER"] = 2.5

        df = pd.concat([df, missing_rows], ignore_index=True)

    # -----------------------------
    # KEEP ONLY SLATE PITCHERS
    # -----------------------------
    df = df[df["Salary"].notna()].copy()

    # -----------------------------
    # FAN DUEL POINTS
    # -----------------------------
    df["projected_fd_points"] = (
        df["projected_IP"] * 3 +
        df["proj_SO"] * 3 +
        df["proj_ER"] * -3
    )

    # -----------------------------
    # VALUE SCORE
    # -----------------------------
    df["points_per_dollar"] = df["projected_fd_points"] / df["Salary"]

    min_ppd = df["points_per_dollar"].min()
    max_ppd = df["points_per_dollar"].max()

    df["value_score"] = 1 + 9 * (
        (df["points_per_dollar"] - min_ppd) /
        (max_ppd - min_ppd)
    )

    df["value_score"] = df["value_score"].round(2)

    # -----------------------------
    # SAVE OUTPUT
    # -----------------------------
    output_path = os.path.join(base_dir, f"../03_output/pitcher_projections_dfs_{slate_date}.csv")

    df.to_csv(output_path, index=False)

    print(f"Pitcher file saved to: {output_path}")

if __name__ == "__main__":
    main()