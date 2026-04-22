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

        # normalize
        df["player_name"] = df["player_name"].astype(str).str.strip().str.lower()
        df["team"] = df["team"].astype(str).str.strip().str.upper()

        if "game_id" not in df.columns:
            print(f"Skipping {file} — missing game_id")
            continue

        hitters = df[(df["type"] == "hitter") & (df["AB"] > 0)].copy()
        pitchers = df[df["type"] == "pitcher"].copy()

        if hitters.empty or pitchers.empty:
            continue

        # merge pitcher handedness
        pitchers = pitchers.merge(
            hand_df[["player_name", "throw_hand"]],
            on="player_name",
            how="left"
        )

        # =========================================================
        # PROCESS EACH GAME SEPARATELY
        # =========================================================
        for game_id in hitters["game_id"].dropna().unique():
            game_hitters = hitters[hitters["game_id"] == game_id].copy()
            game_pitchers = pitchers[pitchers["game_id"] == game_id].copy()

            if game_hitters.empty or game_pitchers.empty:
                continue

            teams = sorted(game_hitters["team"].dropna().unique())

            if len(teams) != 2:
                print(f"Skipping game_id {game_id} in {file} — expected 2 teams, found {len(teams)}")
                continue

            team_a, team_b = teams[0], teams[1]

            opponent_map = {
                team_a: team_b,
                team_b: team_a
            }

            # =========================================================
            # HITTER PA BY TEAM
            # =========================================================
            team_pa = (
                game_hitters.groupby("team")
                .agg(
                    total_ab=("AB", "sum"),
                    total_bb=("BB", "sum")
                )
                .reset_index()
            )

            team_pa["plate_appearances"] = team_pa["total_ab"] + team_pa["total_bb"]

            # =========================================================
            # PITCHER K BY PITCHING TEAM + HAND
            # assign to opponent batting team
            # =========================================================
            pitcher_k = (
                game_pitchers.groupby(["team", "throw_hand"])
                .agg(total_k=("SO", "sum"))
                .reset_index()
            )

            pitcher_k["batting_team"] = pitcher_k["team"].map(opponent_map)

            pitcher_k = pitcher_k.rename(columns={
                "throw_hand": "vs_hand",
                "batting_team": "team_faced"
            })

            merged = pitcher_k.merge(
                team_pa[["team", "plate_appearances"]],
                left_on="team_faced",
                right_on="team",
                how="left"
            )

            merged = merged.rename(columns={"team_faced": "team"})
            merged = merged.drop(columns=["team_y"], errors="ignore")
            merged = merged.rename(columns={"team_x": "pitching_team"})

            all_rows.append(merged[[
                "team",
                "vs_hand",
                "total_k",
                "plate_appearances"
            ]])

    if not all_rows:
        print("No valid data.")
        return

    result = pd.concat(all_rows, ignore_index=True)

    # drop rows with missing handedness or PA
    result = result.dropna(subset=["team", "vs_hand", "plate_appearances"])

    # =========================================================
    # FINAL AGGREGATION
    # =========================================================
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

    print(f"✅ Saved: {output_path}")


if __name__ == "__main__":
    main()