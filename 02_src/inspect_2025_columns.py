import os
import pandas as pd

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_data_path = os.path.abspath(os.path.join(script_dir, "..", "01_data", "raw"))

    files = {
        "Batting": os.path.join(base_data_path, "2025_batting.csv"),
        "Pitching": os.path.join(base_data_path, "2025_pitching.csv"),
    }

    for label, path in files.items():
        df = pd.read_csv(path)
        print(f"--- {label} ---")
        print(f"Rows: {len(df)}")
        print("Columns:")
        for col in df.columns:
            print(f"  {col}")
        print()

if __name__ == "__main__":
    main()