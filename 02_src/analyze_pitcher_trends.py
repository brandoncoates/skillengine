import os
import pandas as pd

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Input file
    data_path = os.path.join(base_dir, "../01_data/processed/pitcher_skill_history_v1.csv")

    df = pd.read_csv(data_path)

    # Sort by player and season
    df = df.sort_values(by=["player_id", "season"])

    # Previous season skill score
    df["prev_SkillScore_v1"] = df.groupby("player_id")["SkillScore_v1"].shift(1)

    # Change in skill score
    df["SkillScore_delta"] = df["SkillScore_v1"] - df["prev_SkillScore_v1"]

    # Trend flags
    df["declining"] = df["SkillScore_delta"] < 0
    df["improving"] = df["SkillScore_delta"] > 0

    # Output file
    output_path = os.path.join(base_dir, "../03_output/pitcher_trends_v1.csv")
    df.to_csv(output_path, index=False)

    print(f"Pitcher trends saved to: {output_path}")

if __name__ == "__main__":
    main()