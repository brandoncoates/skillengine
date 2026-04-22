import os
import pandas as pd


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    box_score_dir = os.path.join(base_dir, "../03_output")

    handedness_path = os.path.join(
        base_dir,
        "../01_data/processed/player_context/player_master.csv"
    )

    hand_df = pd.read_csv(handedness_path)
    hand_df["player_name"] = hand_df["player_name"].astype(str).str.strip().str.lower()

    files = sorted([
        f for f in os.listdir(box_score_dir)
        if f.startswith("box_score_") and f.endswith(".csv")
    ])

    all_rows = []

    for file in files:
        path = os.path.join(box_score_dir, file)
        df = pd.read_csv(path)

        df["player_name"] = df["player_name"].astype(str).str.strip().str.lower()
        df["team"] = df["team"].astype(str).str.strip().str.upper()

        if "game_id" not in df.columns:
            continue

        hitters = df[(df["type"] == "hitter") & (df["AB"] > 0)].copy()
        pitchers = df[df["type"] == "pitcher"].copy()

        if hitters.empty or pitchers.empty:
            continue

        # merge handedness
        pitchers = pitchers.merge(
            hand_df[["player_name", "throw_hand"]],
            on="player_name",
            how="left"
        )

        # 🔥 FIX: KEEP ALL Ks (no dropping)
        pitchers["throw_hand"] = pitchers["throw_hand"].fillna("UNK")

        for game_id in hitters["game_id"].dropna().unique():
            game_hitters = hitters[hitters["game_id"] == game_id]
            game_pitchers = pitchers[pitchers["game_id"] == game_id]

            if game_hitters.empty or game_pitchers.empty:
                continue

            teams = sorted(game_hitters["team"].unique())
            if len(teams) != 2:
                continue

            team_a, team_b = teams[0], teams[1]

            opponent_map = {
                team_a: team_b,
                team_b: team_a
            }

            # ============================
            # TEAM PA
            # ============================
            team_pa = (
                game_hitters.groupby("team")
                .agg(total_ab=("AB", "sum"), total_bb=("BB", "sum"))
                .reset_index()
            )
            team_pa["pa"] = team_pa["total_ab"] + team_pa["total_bb"]

            # ============================
            # PITCHER K BY HAND
            # ============================
            pitcher_k = (
                game_pitchers.groupby(["team", "throw_hand"])
                .agg(total_k=("SO", "sum"))
                .reset_index()
            )

            pitcher_k["batting_team"] = pitcher_k["team"].map(opponent_map)

            for team in [team_a, team_b]:
                team_data = pitcher_k[pitcher_k["batting_team"] == team]

                pa_row = team_pa[team_pa["team"] == team]

                if team_data.empty or pa_row.empty:
                    continue

                pa = pa_row["pa"].values[0]

                for _, row in team_data.iterrows():
                    hand = row["throw_hand"]
                    k = row["total_k"]

                    all_rows.append({
                        "team": team,
                        "vs_hand": hand,
                        "total_k": k,
                        "plate_appearances": pa
                    })

    if not all_rows:
        print("No data built.")
        return

    result = pd.DataFrame(all_rows)

    result = (
        result.groupby(["team", "vs_hand"])
        .agg(
            total_k=("total_k", "sum"),
            plate_appearances=("plate_appearances", "sum")
        )
        .reset_index()
    )

    result["k_rate"] = result["total_k"] / result["plate_appearances"]

    result = result.sort_values(["team", "vs_hand"]).reset_index(drop=True)

    output_dir = os.path.join(base_dir, "../01_data/processed/team_context")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "team_k_rates_by_hand.csv")
    result.to_csv(output_path, index=False)

    print(f"✅ DONE: {output_path}")


if __name__ == "__main__":
    main()