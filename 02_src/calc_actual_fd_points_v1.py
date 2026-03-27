import os
import pandas as pd
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python calc_actual_fd_points_v1.py <YYYY-MM-DD>")
        sys.exit(1)

    slate_date = sys.argv[1]
    
    base_dir = os.path.dirname(os.path.abspath(__file__))

    box_path = os.path.join(base_dir, f"../03_output/box_score_{slate_date}.csv")
    df = pd.read_csv(box_path)

    # -----------------------------
    # HITTER SCORING
    # -----------------------------
    hitters = df[df["type"] == "hitter"].copy()

    hitters["actual_fd_points"] = (
        hitters["1B"] * 3 +
        hitters["2B"] * 6 +
        hitters["3B"] * 9 +
        hitters["HR"] * 12 +
        hitters["RBI"] * 3.5 +
        hitters["R"] * 3.2 +
        hitters["BB"] * 3 +
        hitters["SB"] * 6
    )

    # -----------------------------
    # PITCHER SCORING
    # -----------------------------
    pitchers = df[df["type"] == "pitcher"].copy()

    pitchers["actual_fd_points"] = (
        pitchers["IP"] * 3 +
        pitchers["SO"] * 3 -
        pitchers["ER"] * 3
    )

    # -----------------------------
    # COMBINE
    # -----------------------------
    combined = pd.concat([hitters, pitchers], ignore_index=True)

    # -----------------------------
    # SAVE
    # -----------------------------
    output_path = os.path.join(base_dir, f"../03_output/actual_fd_points_{slate_date}.csv")
    combined.to_csv(output_path, index=False)

    print(f"\nActual FD points saved to: {output_path}")

if __name__ == "__main__":
    main()