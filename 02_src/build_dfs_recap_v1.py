import os
import sys
import pandas as pd

def main():

    # -----------------------------
    # DATE ARG (REQUIRED)
    # -----------------------------
    if len(sys.argv) < 2:
        print("Usage: python build_dfs_recap_v1.py <YYYY-MM-DD>")
        sys.exit(1)

    slate_date = sys.argv[1]

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # -----------------------------
    # LOAD HITTER PROJECTIONS
    # -----------------------------
    hitter_path = os.path.join(base_dir, f"../03_output/hitter_projections_dfs_{slate_date}.csv")
    hitters = pd.read_csv(hitter_path)

    # -----------------------------
    # LOAD PITCHER PROJECTIONS (OPTIONAL)
    # -----------------------------
    pitcher_path = os.path.join(base_dir, f"../03_output/pitcher_projections_dfs_{slate_date}.csv")

    if os.path.exists(pitcher_path):
        pitchers = pd.read_csv(pitcher_path)
        proj = pd.concat([hitters, pitchers], ignore_index=True)
        print("PROJ COLUMNS:", proj.columns.tolist())
        print(f"Loaded hitter + pitcher projections for {slate_date}")
    else:
        proj = hitters.copy()
        print(f"No pitcher projections file found for {slate_date} — using hitters only")

    # -----------------------------
    # LOAD ACTUALS
    # -----------------------------
    actual_path = os.path.join(base_dir, f"../03_output/actual_fd_points_{slate_date}.csv")
    actual = pd.read_csv(actual_path)

    # -----------------------------
    # LOAD DFS MANUAL HELPER
    # -----------------------------
    helper_path = os.path.join(base_dir, f"../03_output/dfs_manual_helper_{slate_date}.xlsx")

    pitchers_helper = pd.read_excel(helper_path, sheet_name="Pitchers")
    stacks_helper = pd.read_excel(helper_path, sheet_name="Stacks")
    top_hitters_helper = pd.read_excel(helper_path, sheet_name="Top Hitters")
    by_position_helper = pd.read_excel(helper_path, sheet_name="By Position")

    # -----------------------------
    # CLEAN NAMES
    # -----------------------------
    proj["player_name"] = proj["player_name"].str.strip().str.lower()
    actual["player_name"] = actual["player_name"].str.strip().str.lower()

    pitchers_helper["player_name"] = pitchers_helper["player_name"].str.strip().str.lower()
    stacks_helper["player_name"] = stacks_helper["player_name"].str.strip().str.lower()
    top_hitters_helper["player_name"] = top_hitters_helper["player_name"].str.strip().str.lower()
    by_position_helper["player_name"] = by_position_helper["player_name"].str.strip().str.lower()

    # -----------------------------
    # BUILD RECOMMENDATION MAP
    # -----------------------------
    recommendation_map = {}

    def add_source(df, source_tag):
        for name in df["player_name"].dropna().unique():
            if name not in recommendation_map:
                recommendation_map[name] = set()
            recommendation_map[name].add(source_tag)

    add_source(pitchers_helper, "PITCHER")
    add_source(stacks_helper, "STACK")
    add_source(top_hitters_helper, "TOP_PLAY")
    add_source(by_position_helper, "POSITION")

    # -----------------------------
    # LOAD FANDUEL SLATE
    # -----------------------------
    fanduel_path = os.path.join(base_dir, f"../01_data/raw/fanduel/FanDuel-MLB-{slate_date}.csv")
    fanduel = pd.read_csv(fanduel_path)

    fanduel["player_name"] = (
        fanduel["First Name"].str.strip().str.lower() + " " +
        fanduel["Last Name"].str.strip().str.lower()
    )

    fanduel_players = set(fanduel["player_name"])

    # -----------------------------
    # MERGE
    # -----------------------------
    merged = proj.merge(
        actual[["player_name", "actual_fd_points"]],
        on="player_name",
        how="left"
    )

    merged = merged.merge(
        fanduel[["player_name", "Position"]],
        on="player_name",
        how="left"
    )

    # -----------------------------
    # FILTER TO SLATE PLAYERS ONLY
    # -----------------------------
    merged = merged[merged["player_name"].isin(fanduel_players)].copy()

    # -----------------------------
    # CALCULATIONS
    # -----------------------------
    merged["point_diff"] = merged["actual_fd_points"] - merged["projected_fd_points"]
    merged["abs_point_diff"] = merged["point_diff"].abs()

    merged["pct_diff"] = merged["point_diff"] / merged["projected_fd_points"]
    merged["abs_pct_diff"] = merged["pct_diff"].abs()

    # -----------------------------
    # PROJECTION DIRECTION
    # -----------------------------
    def get_direction(row):
        if pd.isna(row["actual_fd_points"]):
            return "NO_DATA"
        if abs(row["point_diff"]) <= 1:
            return "ON_TARGET"
        elif row["point_diff"] > 0:
            return "UNDER_PROJECTED"
        else:
            return "OVER_PROJECTED"

    merged["projection_direction"] = merged.apply(get_direction, axis=1)

    # -----------------------------
    # PROJECTION ACCURACY BUCKET
    # -----------------------------
    def get_accuracy(row):
        if pd.isna(row["actual_fd_points"]):
            return "NO_DATA"

        diff = row["abs_point_diff"]
        pos = str(row["Position"]).upper()

        if "P" in pos:
            if diff <= 4:
                return "ELITE"
            elif diff <= 8:
                return "GOOD"
            elif diff <= 12:
                return "OK"
            elif diff <= 18:
                return "BAD"
            else:
                return "VERY_BAD"
        else:
            if diff <= 2:
                return "ELITE"
            elif diff <= 5:
                return "GOOD"
            elif diff <= 8:
                return "OK"
            elif diff <= 12:
                return "BAD"
            else:
                return "VERY_BAD"

    merged["projection_accuracy_bucket"] = merged.apply(get_accuracy, axis=1)

    # -----------------------------
    # DFS PAYOFF CALCULATIONS
    # -----------------------------
    merged["points_per_1000"] = merged["actual_fd_points"] / (merged["Salary"] / 1000)

    def get_payoff(row):
        if pd.isna(row["actual_fd_points"]):
            return "NO_DATA"

        val = row["points_per_1000"]
        pos = str(row["Position"]).upper()

        if "P" in pos:
            if val >= 3.0:
                return "SMASH"
            elif val >= 2.5:
                return "GREAT"
            elif val >= 2.0:
                return "GOOD"
            else:
                return "FAIL"
        else:
            if val >= 4.5:
                return "SMASH"
            elif val >= 3.5:
                return "GREAT"
            elif val >= 2.5:
                return "GOOD"
            else:
                return "FAIL"

    merged["payoff_tier"] = merged.apply(get_payoff, axis=1)

    merged["did_pay_off"] = (merged["payoff_tier"].isin(["GOOD", "GREAT", "SMASH"])).astype(int)

    # -----------------------------
    # RECOMMENDATION FLAGS
    # -----------------------------
    def get_sources(name):
        if name in recommendation_map:
            return "|".join(sorted(recommendation_map[name]))
        return ""

    merged["was_recommended"] = merged["player_name"].apply(
        lambda x: 1 if x in recommendation_map else 0
    )

    merged["recommendation_source"] = merged["player_name"].apply(get_sources)

    # -----------------------------
    # DECISION QUALITY (NOW CORRECTLY PLACED)
    # -----------------------------
    def decision_quality(row):

        if row["payoff_tier"] == "NO_DATA":
            return "NO_DATA"

        if row["payoff_tier"] == "GOOD":
            return "NEUTRAL_PLAY"

        if row["was_recommended"] == 1 and row["did_pay_off"] == 1:
            return "GOOD_PICK"

        if row["was_recommended"] == 1 and row["did_pay_off"] == 0:
            return "BAD_PICK"

        if row["was_recommended"] == 0 and row["did_pay_off"] == 1:
            return "MISSED_UPSIDE"

        if row["was_recommended"] == 0 and row["did_pay_off"] == 0:
            return "CORRECT_FADE"

        return "UNKNOWN"

    merged["decision_quality"] = merged.apply(decision_quality, axis=1)

    # -----------------------------
    # SAVE
    # -----------------------------
    output_path = os.path.join(base_dir, f"../03_output/dfs_recap_{slate_date}.csv")

    final_cols = [
        "player_name",
        "Position",
        "team",
        "opponent",
        "Salary",
        "projected_fd_points",
        "value_score",
        "was_recommended",
        "recommendation_source",
        "actual_fd_points",
        "point_diff",
        "abs_point_diff",
        "pct_diff",
        "abs_pct_diff",
        "projection_direction",
        "projection_accuracy_bucket",
        "points_per_1000",
        "payoff_tier",
        "did_pay_off",
        "decision_quality"
    ]

    merged = merged[final_cols]

    merged = merged.sort_values(by=["point_diff"], ascending=False)

    merged.to_csv(output_path, index=False)

    print(f"\nDFS recap saved to: {output_path}")

    print("\nSUMMARY:")
    print("Rows:", len(merged))


if __name__ == "__main__":
    main()