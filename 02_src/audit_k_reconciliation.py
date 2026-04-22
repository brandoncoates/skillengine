import os
import pandas as pd


def main():
    box_dir = "03_output"
    split_path = "01_data/processed/team_context/team_k_rates_by_hand.csv"

    # ============================
    # 1. TOTAL K FROM BOX SCORES
    # ============================
    box_files = [
        f for f in os.listdir(box_dir)
        if f.startswith("box_score_") and f.endswith(".csv")
    ]

    total_k_box = 0

    for f in box_files:
        df = pd.read_csv(os.path.join(box_dir, f))

        hitters = df[
            (df["type"] == "hitter") &
            (df["AB"] > 0)
        ]

        total_k_box += hitters["K"].sum()

    print(f"\nTOTAL K FROM BOX SCORES: {total_k_box}")

    # ============================
    # 2. TOTAL K FROM SPLIT FILE
    # ============================
    split_df = pd.read_csv(split_path)

    total_k_split = split_df["total_k"].sum()

    print(f"TOTAL K FROM SPLIT FILE: {total_k_split}")

    # ============================
    # 3. CHECK DIFFERENCE
    # ============================
    diff = total_k_box - total_k_split

    print(f"\nDIFFERENCE: {diff}")

    # ============================
    # 4. TEAM-LEVEL CHECK
    # ============================
    print("\n=== TEAM LEVEL CHECK ===")

    # box totals
    team_k_box = {}

    for f in box_files:
        df = pd.read_csv(os.path.join(box_dir, f))

        hitters = df[
            (df["type"] == "hitter") &
            (df["AB"] > 0)
        ]

        team_sum = hitters.groupby("team")["K"].sum()

        for team, val in team_sum.items():
            team_k_box[team] = team_k_box.get(team, 0) + val

    box_df = pd.DataFrame(list(team_k_box.items()), columns=["team", "box_k"])

    split_team = (
        split_df.groupby("team")["total_k"]
        .sum()
        .reset_index()
        .rename(columns={"total_k": "split_k"})
    )

    merged = box_df.merge(split_team, on="team", how="left")

    merged["diff"] = merged["box_k"] - merged["split_k"]

    print(merged.sort_values("diff", ascending=False))


if __name__ == "__main__":
    main()