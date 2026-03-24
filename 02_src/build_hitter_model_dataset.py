import os
import pandas as pd

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # --- Paths ---
    raw_path = os.path.join(base_dir, "../01_data/raw")
    skill_path = os.path.join(base_dir, "../01_data/processed/hitter_skill_history_v1.csv")
    trends_path = os.path.join(base_dir, "../03_output/hitter_trends_v1.csv")
    output_path = os.path.join(base_dir, "../01_data/processed/hitter_model_dataset_v1.csv")

    # --- Load skill + trends ---
    skill_df = pd.read_csv(skill_path)
    trends_df = pd.read_csv(trends_path)

    # --- Keep ONLY needed columns from skill ---
    skill_df = skill_df[[
        "player_id",
        "season",
        "SkillScore_v1"
    ]]

    # --- Keep ONLY needed columns from trends ---
    trends_df = trends_df[[
        "player_id",
        "season",
        "SkillScore_delta",
        "improving",
        "declining"
    ]]

    # --- Load and combine raw batting files ---
    years = [2021, 2022, 2023, 2024, 2025]
    raw_dfs = []

    for year in years:
        file_path = os.path.join(raw_path, f"{year}_batting.csv")
        df = pd.read_csv(file_path)

        # Standardize column name
        df = df.rename(columns={"year": "season"})

        raw_dfs.append(df)

    raw_df = pd.concat(raw_dfs, ignore_index=True)

    # --- Select ONLY required stat columns ---
    raw_df = raw_df[[
        "player_id",
        "last_name, first_name",
        "season",
        "batting_avg",
        "home_run",
        "b_rbi",
        "r_run",
        "r_total_stolen_base"
    ]]

    # --- Merge skill data ---
    df = pd.merge(raw_df, skill_df, on=["player_id", "season"], how="left")

    # --- Merge trend data ---
    df = pd.merge(df, trends_df, on=["player_id", "season"], how="left")

    # --- Sort for sequencing ---
    df = df.sort_values(by=["player_id", "season"])

    # --- Create target columns ---
    df["target_batting_avg"] = df.groupby("player_id")["batting_avg"].shift(-1)
    df["target_home_run"] = df.groupby("player_id")["home_run"].shift(-1)
    df["target_b_rbi"] = df.groupby("player_id")["b_rbi"].shift(-1)
    df["target_r_run"] = df.groupby("player_id")["r_run"].shift(-1)
    df["target_r_total_stolen_base"] = df.groupby("player_id")["r_total_stolen_base"].shift(-1)

    # --- Drop rows without next season ---
    df = df.dropna(subset=["target_home_run"])

    # --- Save output ---
    df.to_csv(output_path, index=False)

    print(f"Hitter model dataset saved to: {output_path}")


if __name__ == "__main__":
    main()