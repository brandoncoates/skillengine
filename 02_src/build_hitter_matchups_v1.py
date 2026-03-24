import os
import sys
import pandas as pd
from datetime import datetime

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # =========================================================
    # 📅 Get slate date (from CLI or default to today)
    # =========================================================
    if len(sys.argv) > 1:
        slate_date = sys.argv[1]
    else:
        slate_date = datetime.today().strftime("%Y-%m-%d")

    # =========================================================
    # 📥 INPUT FILES
    # =========================================================

    # FanDuel
    fd_path = os.path.join(
        base_dir,
        f"../01_data/raw/fanduel/FanDuel-MLB-{slate_date}.csv"
    )

    # Vegas
    vegas_path = os.path.join(
        base_dir,
        "../01_data/raw/vegas",
        f"vegas_{slate_date}.csv"
    )

    # =========================================================
    # 📤 OUTPUT
    # =========================================================

    output_path = os.path.join(
        base_dir,
        f"../03_output/hitter_matchups_{slate_date}.csv"
    )

    # =========================================================
    # 📊 LOAD DATA
    # =========================================================

    df = pd.read_csv(fd_path)

    # Load Vegas if exists
    if os.path.exists(vegas_path):
        vegas_df = pd.read_csv(vegas_path)
    else:
        print(f"⚠️ Vegas file not found for {slate_date}")
        vegas_df = pd.DataFrame(columns=[
            "team", "opponent", "game_total",
            "moneyline", "spread", "implied_team_total"
        ])

    # =========================================================
    # 🎯 STEP 1: Extract starting pitchers
    # =========================================================

    pitchers = df[
        (df["Position"] == "P") &
        (df["Probable Pitcher"] == "Yes")
    ][[
        "Team",
        "Nickname"
    ]].copy()

    pitchers = pitchers.rename(columns={
        "Team": "pitcher_team",
        "Nickname": "opposing_pitcher"
    })

    # =========================================================
    # 🎯 STEP 2: Extract hitters
    # =========================================================

    hitters = df[df["Position"] != "P"][[
        "Nickname",
        "Team",
        "Opponent",
        "Salary"
    ]].copy()

    hitters = hitters.rename(columns={
        "Nickname": "player_name",
        "Team": "team",
        "Opponent": "opponent"
    })

    # =========================================================
    # 🔗 STEP 3: Attach opposing pitcher
    # =========================================================

    merged = hitters.merge(
        pitchers,
        left_on="opponent",
        right_on="pitcher_team",
        how="left"
    )

    # =========================================================
    # 🧹 Clean base columns
    # =========================================================

    merged = merged[[
        "player_name",
        "team",
        "opponent",
        "opposing_pitcher",
        "Salary"
    ]]

    # =========================================================
    # 💰 STEP 4: Filter Vegas to slate matchups
    # =========================================================

    if not vegas_df.empty:
        valid_matchups = merged[["team", "opponent"]].drop_duplicates()

        vegas_df = vegas_df.merge(
            valid_matchups,
            on=["team", "opponent"],
            how="inner"
        )

    # =========================================================
    # 🔗 STEP 5: Merge Vegas data
    # =========================================================

    merged = merged.merge(
        vegas_df,
        on=["team", "opponent"],
        how="left"
    )

    # =========================================================
    # 💾 SAVE
    # =========================================================

    merged.to_csv(output_path, index=False)

    print(f"✅ Matchups file saved to: {output_path}")


if __name__ == "__main__":
    main()