import os
import sys
import pandas as pd
from datetime import datetime


def normalize_team(series):
    TEAM_MAP = {
        "CWS": "CHW",
        "CHW": "CHW",
        "WSN": "WSH",
        "WSH": "WSH"
    }

    return (
        series.astype(str)
        .str.strip()
        .str.upper()
        .replace(TEAM_MAP)
    )


def normalize_name(series):
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
    )


def normalize_master_name(series):
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .apply(
            lambda x: (
                " ".join([p.strip() for p in x.split(",")[::-1]])
                if "," in x else x
            )
        )
    )


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # =========================================================
    # 📅 Get slate date
    # =========================================================
    if len(sys.argv) > 1:
        slate_date = sys.argv[1]
    else:
        slate_date = datetime.today().strftime("%Y-%m-%d")

    # =========================================================
    # 📥 INPUT FILES
    # =========================================================
    fd_path = os.path.join(
        base_dir,
        f"../01_data/raw/fanduel/FanDuel-MLB-{slate_date}.csv"
    )

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
        f"../03_output/hitter_matchups_dfs_{slate_date}.csv"
    )

    # =========================================================
    # 📊 LOAD DATA
    # =========================================================
    df = pd.read_csv(fd_path)

    # Remove players on IL
    df = df[df["Injury Indicator"] != "IL"]

    if os.path.exists(vegas_path):
        vegas_df = pd.read_csv(vegas_path)
    else:
        print(f"⚠️ Vegas file not found for {slate_date}")
        vegas_df = pd.DataFrame(columns=[
            "team", "opponent", "game_total",
            "moneyline", "spread", "implied_team_total"
        ])

    # =========================================================
    # 🔧 NORMALIZE VEGAS
    # =========================================================
    vegas_df["team"] = normalize_team(vegas_df["team"])
    vegas_df["opponent"] = normalize_team(vegas_df["opponent"])

    # =========================================================
    # 🔁 MAKE VEGAS BIDIRECTIONAL
    # =========================================================
    vegas_flip = vegas_df.rename(columns={
        "team": "opponent",
        "opponent": "team"
    }).copy()

    vegas_full = pd.concat([vegas_df, vegas_flip], ignore_index=True)
    vegas_full = vegas_full.drop_duplicates(subset=["team", "opponent"])

    # =========================================================
    # 🎯 Extract pitchers
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

    pitchers["pitcher_team"] = normalize_team(pitchers["pitcher_team"])
    pitchers["opposing_pitcher"] = normalize_name(pitchers["opposing_pitcher"])

    # =========================================================
    # 🎯 Extract hitters
    # =========================================================
    hitters = df[df["Position"] != "P"][
        [
            "Nickname",
            "Team",
            "Opponent",
            "Salary",
            "Position"
        ]
    ].copy()

    hitters = hitters.rename(columns={
        "Nickname": "player_name",
        "Team": "team",
        "Opponent": "opponent",
        "Position": "position"
    })

    hitters["player_name"] = normalize_name(hitters["player_name"])
    hitters["team"] = normalize_team(hitters["team"])
    hitters["opponent"] = normalize_team(hitters["opponent"])

    # =========================================================
    # 🔗 Attach opposing pitcher
    # =========================================================
    merged = hitters.merge(
        pitchers,
        left_on="opponent",
        right_on="pitcher_team",
        how="left"
    )

    # =========================================================
    # 🧹 Clean columns
    # =========================================================
    merged = merged[
        [
            "player_name",
            "position",
            "team",
            "opponent",
            "opposing_pitcher",
            "Salary"
        ]
    ]

    # =========================================================
    # 🔗 Merge Player Handedness
    # =========================================================
    handedness_path = os.path.join(
        base_dir,
        "../01_data/processed/player_context/player_master.csv"
    )

    hand_df = pd.read_csv(handedness_path)

    hand_df["player_name"] = normalize_master_name(hand_df["player_name"])
    merged["player_name"] = normalize_name(merged["player_name"])

    merged = merged.merge(
        hand_df[["player_name", "bat_hand"]],
        on="player_name",
        how="left"
    )

    # =========================================================
    # 🔗 Merge Pitcher Handedness
    # =========================================================
    hand_df["pitcher_name"] = hand_df["player_name"]
    merged["opposing_pitcher"] = normalize_name(merged["opposing_pitcher"])

    merged = merged.merge(
        hand_df[["pitcher_name", "throw_hand"]],
        left_on="opposing_pitcher",
        right_on="pitcher_name",
        how="left"
    )

    merged = merged.rename(columns={"throw_hand": "pitcher_hand"})
    merged = merged.drop(columns=["pitcher_name"])

    # =========================================================
    # 🔗 Merge Vegas
    # =========================================================
    merged = merged.merge(
        vegas_full,
        on=["team", "opponent"],
        how="left"
    )

    # =========================================================
    # 🧱 FORCE NO MISSING VEGAS DATA
    # =========================================================
    missing_mask = merged["game_total"].isna()

    if missing_mask.any():
        print(f"Filling missing Vegas rows: {missing_mask.sum()}")

        merged.loc[missing_mask, "game_total"] = merged["game_total"].mean()
        merged.loc[missing_mask, "moneyline"] = 0
        merged.loc[missing_mask, "spread"] = 0
        merged.loc[missing_mask, "implied_team_total"] = merged["implied_team_total"].mean()

    # =========================================================
    # 💾 SAVE
    # =========================================================
    merged.to_csv(output_path, index=False)

    print(f"✅ Matchups file saved to: {output_path}")


if __name__ == "__main__":
    main()