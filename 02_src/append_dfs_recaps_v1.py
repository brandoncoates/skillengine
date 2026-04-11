import os
import sys
import pandas as pd

def main():

    # -----------------------------
    # DATE ARG
    # -----------------------------
    if len(sys.argv) < 2:
        print("Usage: python append_dfs_recaps_v1.py <YYYY-MM-DD>")
        return

    slate_date = sys.argv[1]

    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "../03_output")

    recap_path = os.path.join(output_dir, f"dfs_recap_{slate_date}.csv")
    master_path = os.path.join(output_dir, "dfs_recap_master.csv")

    # -----------------------------
    # LOAD TODAY RECAP
    # -----------------------------
    if not os.path.exists(recap_path):
        print(f"❌ Recap file not found: {recap_path}")
        return

    df = pd.read_csv(recap_path)

    # -----------------------------
    # ADD DATE COLUMN
    # -----------------------------
    df["slate_date"] = slate_date

    # -----------------------------
    # APPEND OR CREATE MASTER
    # -----------------------------
    if os.path.exists(master_path):
        master_df = pd.read_csv(master_path)

        combined = pd.concat([master_df, df], ignore_index=True)

        # -----------------------------
        # REMOVE DUPLICATES
        # (same player + same slate_date)
        # -----------------------------
        combined = combined.drop_duplicates(
            subset=["player_name", "slate_date"],
            keep="last"
        )

        combined.to_csv(master_path, index=False)

        print(f"✅ Appended to master file: {master_path}")

    else:
        df.to_csv(master_path, index=False)
        print(f"✅ Created master file: {master_path}")


if __name__ == "__main__":
    main()