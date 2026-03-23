import os
import pandas as pd

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "../01_data/processed/hitter_skill_history_v1.csv")

    df = pd.read_csv(data_path)

    df = df.sort_values(by=["player_id", "season"])

    df["prev_SkillScore_v1"] = df.groupby("player_id")["SkillScore_v1"].shift(1)

    df["SkillScore_delta"] = df["SkillScore_v1"] - df["prev_SkillScore_v1"]

    df["declining"] = df["SkillScore_delta"] < 0

    df["improving"] = df["SkillScore_delta"] > 0

    output_path = os.path.join(base_dir, "../03_output/hitter_trends_v1.csv")
    df.to_csv(output_path, index=False)

    print(f"Hitter trends saved to: {output_path}")

if __name__ == "__main__":
    main()