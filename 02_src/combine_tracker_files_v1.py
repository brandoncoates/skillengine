import os
import pandas as pd
import sys

def main():

    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "../03_output")

    # -----------------------------
    # FIND TRACKER FILES
    # -----------------------------

    files = [
        f for f in os.listdir(output_dir)
        if f.startswith("player_hit_tracker_")
        and f.endswith(".csv")
        and "master" not in f
    ]

    if not files:
        print("No tracker files found.")
        return

    # -----------------------------
    # LOAD + COMBINE
    # -----------------------------
    all_dfs = []

    for file in files:
        path = os.path.join(output_dir, file)
        df = pd.read_csv(path)
        all_dfs.append(df)

    combined = pd.concat(all_dfs, ignore_index=True)

    # -----------------------------
    # SAVE MASTER FILE
    # -----------------------------

    if len(sys.argv) < 2:
        print("Usage: python combine_tracker_files_v1.py <YYYY-MM-DD>")
        return

    slate_date = sys.argv[1]

    output_path = os.path.join(output_dir, f"player_hit_tracker_master_{slate_date}.csv")

    combined.to_csv(output_path, index=False)

    print(f"Master tracker saved: {output_path}")

if __name__ == "__main__":
    main()
