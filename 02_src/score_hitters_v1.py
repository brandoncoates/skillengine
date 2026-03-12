import os
import sys
import pandas as pd

def main():
    if len(sys.argv) < 2:
        print("Usage: python score_hitters_v1.py <season>")
        sys.exit(1)

    season = sys.argv[1]

    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(base_dir, f"../03_output/{season}_hitters_master.csv")
    output_path = os.path.join(base_dir, f"../03_output/{season}_hitters_scored_v1.csv")

    df = pd.read_csv(input_path)
    print(f"Rows loaded: {len(df)}")

    # Determine strikeout rate column
    if "K%" in df.columns:
        df["k_rate"] = df["K%"]
    else:
        df["k_rate"] = df["SO"] / df["PA"]

    # Compute percentiles (0–100)
    df["pct_OBP"] = df["OBP"].rank(pct=True) * 100
    df["pct_SLG"] = df["SLG"].rank(pct=True) * 100
    df["pct_Krate"] = df["k_rate"].rank(pct=True) * 100  # higher K% = worse, so weight is negative

    # Combine into SkillScore_v1
    df["SkillScore_v1"] = (
        0.45 * df["pct_OBP"] +
        0.35 * df["pct_SLG"] +
        -0.20 * df["pct_Krate"]
    )

    # Drop helper columns
    df = df.drop(columns=["k_rate", "pct_OBP", "pct_SLG", "pct_Krate"])

    df.to_csv(output_path, index=False)
    print(f"Rows saved: {len(df)}")

    top10 = df.nlargest(10, "SkillScore_v1")[["player_name", "PA", "SkillScore_v1"]]
    print("\nTop 10 Hitters by SkillScore_v1:")
    print(top10.to_string(index=False))

if __name__ == "__main__":
    main()