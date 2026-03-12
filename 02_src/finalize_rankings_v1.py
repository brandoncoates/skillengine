import os
import sys
import pandas as pd

def rank_and_save(input_path, ranked_path, top50_path, label):
    df = pd.read_csv(input_path)
    df = df.sort_values("SkillScore_v1", ascending=False).reset_index(drop=True)
    df.insert(0, "Rank", df.index + 1)

    df.to_csv(ranked_path, index=False)
    df.head(50).to_csv(top50_path, index=False)

    print(f"\nTop 5 {label}:")
    print(df.head(5)[["player_name", "Rank", "SkillScore_v1"]].to_string(index=False))

    return df

def main():
    if len(sys.argv) < 2:
        print("Usage: python finalize_rankings_v1.py <season>")
        sys.exit(1)

    season = sys.argv[1]

    base_dir = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(base_dir, "../03_output")

    rank_and_save(
        input_path=os.path.join(out, f"{season}_hitters_scored_v1.csv"),
        ranked_path=os.path.join(out, f"{season}_hitters_ranked_v1.csv"),
        top50_path=os.path.join(out, f"{season}_hitters_top50_v1.csv"),
        label="Hitters",
    )

    rank_and_save(
        input_path=os.path.join(out, f"{season}_pitchers_scored_v1.csv"),
        ranked_path=os.path.join(out, f"{season}_pitchers_ranked_v1.csv"),
        top50_path=os.path.join(out, f"{season}_pitchers_top50_v1.csv"),
        label="Pitchers",
    )

if __name__ == "__main__":
    main()