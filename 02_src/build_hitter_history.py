import os
import pandas as pd

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "../01_data/processed")
    os.makedirs(output_dir, exist_ok=True)

    data_dir = os.path.join(base_dir, "../03_output")
    files = [f for f in os.listdir(data_dir) if f.endswith("_hitters_scored_v1.csv")]

    dataframes = []

    for file in files:
        filepath = os.path.join(data_dir, file)
        df = pd.read_csv(filepath)

        season = file.split("_")[0]
        df["season"] = season

        dataframes.append(df)

    combined_df = pd.concat(dataframes, ignore_index=True)

    output_file = os.path.join(output_dir, "hitter_skill_history_v1.csv")
    combined_df.to_csv(output_file, index=False)

    print(f"Hitter history dataset saved to: {output_file}")

if __name__ == "__main__":
    main()