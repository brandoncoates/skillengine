import os
import pandas as pd

def main():

    import sys

    if len(sys.argv) < 2:
        print("Usage: python build_hitter_projections_v1.py <YYYY-MM-DD>")
        sys.exit(1)

    slate_date = sys.argv[1]
    
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # -----------------------------
    # INPUT FILES
    # -----------------------------
    history_path = os.path.join(base_dir, "../01_data/processed/hitter_skill_history_v1.csv")

    # TODO: Replace with today's date dynamically later
    matchup_path = os.path.join(base_dir, f"../03_output/hitter_matchups_dfs_{slate_date}.csv")

    # -----------------------------
    # LOAD DATA
    # -----------------------------
    history_df = pd.read_csv(history_path)
    matchup_df = pd.read_csv(matchup_path)

    print(f"History rows: {len(history_df)}")
    print(f"Matchup rows: {len(matchup_df)}")

    # -----------------------------
    # KEEP ONLY 2023–2025 FOR WEIGHTED MODEL
    # -----------------------------
    history_df["season"] = pd.to_numeric(history_df["season"], errors="coerce")
    history_df = history_df[history_df["season"].isin([2023, 2024, 2025])].copy()

    print(f"History rows after 2023-2025 filter: {len(history_df)}")

    print("\nHistory columns:")
    print(history_df.columns.tolist())

    print("\nMatchup columns:")
    print(matchup_df.columns.tolist())

    # -----------------------------
    # WEIGHTED PA CALCULATION
    # -----------------------------
    season_weights = {
        2025: 0.5,
        2024: 0.3,
        2023: 0.2
    }

    # Map weights
    history_df["season_weight"] = history_df["season"].map(season_weights)

    # Compute weighted PA contribution
    history_df["weighted_PA_component"] = history_df["PA"] * history_df["season_weight"]

    # Aggregate to player level
    weighted_pa_df = (
        history_df
        .groupby("player_name", as_index=False)
        .agg({
            "weighted_PA_component": "sum",
            "season_weight": "sum"
        })
    )

    # Re-normalize weights (handles missing seasons)
    weighted_pa_df["weighted_PA"] = (
        weighted_pa_df["weighted_PA_component"] /
        weighted_pa_df["season_weight"]
    )

    # Keep only needed column
    weighted_pa_df = weighted_pa_df[["player_name", "weighted_PA"]]

    print("\nWeighted PA sample:")
    print(weighted_pa_df.head(10))

    # -----------------------------
    # MERGE WEIGHTED PA INTO MATCHUP
    # -----------------------------
    df = matchup_df.merge(weighted_pa_df, on="player_name", how="left")

    print("\nAfter merge (sample):")
    print(df[["player_name", "team", "Salary", "weighted_PA"]].head(10))

    print("\nMissing weighted_PA count:")
    print(df["weighted_PA"].isna().sum())

    # -----------------------------
    # HANDLE MISSING weighted_PA (ROOKIES / NEW PLAYERS)
    # -----------------------------
    avg_weighted_PA = weighted_pa_df["weighted_PA"].mean()

    df["weighted_PA"] = df["weighted_PA"].fillna(avg_weighted_PA)

    print("\nFilled missing weighted_PA with league average:")
    print(avg_weighted_PA)

    # -----------------------------
    # TEAM TOTAL PA + PLAYER SHARE
    # -----------------------------

    # -----------------------------
    # LIMIT TO TOP 9 HITTERS PER TEAM
    # -----------------------------
    
    # -----------------------------
    # COMBINED OPPORTUNITY SCORE
    # -----------------------------
    df["opportunity_score"] = (
        df["weighted_PA"] * 0.7 +
        df["Salary"] * 0.3
    )

    df["rank_within_team"] = df.groupby("team")["opportunity_score"].rank(method="first", ascending=False)

    # KEEP ONLY LIKELY STARTERS
    df = df[df["rank_within_team"] <= 9].copy()

    top_hitters_df = df[df["rank_within_team"] <= 9].copy()

    # Recalculate team totals using only top hitters
    top_hitters_df["team_total_PA"] = top_hitters_df.groupby("team")["weighted_PA"].transform("sum")

    # Merge back team_total_PA
    df = df.merge(
        top_hitters_df[["player_name", "team_total_PA"]],
        on="player_name",
        how="left"
    )

    # Player share of team PA
    df["player_PA_share"] = df["weighted_PA"] / df["team_total_PA"]

    # -----------------------------
    # HANDLE MISSING PA SHARE (EDGE CASE)
    # -----------------------------
    avg_pa_share = 1 / 9

    df["player_PA_share"] = df["player_PA_share"].fillna(avg_pa_share)

    print("\nPA share sample:")
    print(df[["player_name", "team", "weighted_PA", "team_total_PA", "player_PA_share"]].head(10))

    # -----------------------------
    # PROJECTED PA (VEGAS + BENCH ADJUSTMENT)
    # -----------------------------

    # Step 1 - Use fixed team PA baseline (more accurate than using runs)
    df["team_projected_PA"] = 38

    # Step 2 — bench vs starter multiplier
    bench_threshold = 250

    df["PA_multiplier"] = df["weighted_PA"].apply(
        lambda x: 1.0 if x >= bench_threshold else 0.3
    )

    # Step 3 — final projected PA
    df["projected_PA"] = (
        df["team_projected_PA"]
        * df["player_PA_share"]
        * df["PA_multiplier"]
    )

    # -----------------------------
    # STAT RATES (SIMPLE VERSION)
    # -----------------------------

    # Use most recent season available (fast + stable for now)
    latest_season_df = (
        history_df
        .sort_values("season", ascending=False)
        .drop_duplicates(subset=["player_name"])
    )

    # Calculate rates
    for stat in ["1B", "2B", "3B", "HR", "RBI", "R", "SB", "BB"]:
        latest_season_df[f"rate_{stat}"] = latest_season_df[stat] / latest_season_df["PA"]

    rate_cols = ["player_name"] + [f"rate_{stat}" for stat in ["1B", "2B", "3B", "HR", "RBI", "R", "SB", "BB"]]

    rate_df = latest_season_df[rate_cols]

    # Merge into main df
    df = df.merge(rate_df, on="player_name", how="left")

    print("\nRate sample:")
    print(df[[
        "player_name",
        "rate_1B",
        "rate_HR",
        "rate_RBI",
        "rate_R",
        "rate_SB",
        "rate_BB"
    ]].head(10))

    # -----------------------------
    # PROJECTED STATS
    # -----------------------------
    for stat in ["1B", "2B", "3B", "HR", "RBI", "R", "SB", "BB"]:
        df[f"proj_{stat}"] = df[f"rate_{stat}"] * df["projected_PA"]

    print("\nProjected stats sample:")
    print(df[[
        "player_name",
        "proj_1B",
        "proj_HR",
        "proj_RBI",
        "proj_R",
        "proj_SB",
        "proj_BB"
    ]].head(10))


    # -----------------------------
    # FAN DUEL POINTS
    # -----------------------------
    df["projected_fd_points"] = (
        df["proj_1B"] * 3 +
        df["proj_2B"] * 6 +
        df["proj_3B"] * 9 +
        df["proj_HR"] * 12 +
        df["proj_RBI"] * 3.5 +
        df["proj_R"] * 3.2 +
        df["proj_BB"] * 3 +
        df["proj_SB"] * 6
    )

    # Points per dollar
    df["points_per_dollar"] = df["projected_fd_points"] / df["Salary"]

    # -----------------------------
    # NORMALIZED VALUE SCORE (1–10)
    # -----------------------------
    min_ppd = df["points_per_dollar"].min()
    max_ppd = df["points_per_dollar"].max()

    df["value_score"] = 1 + 9 * (
        (df["points_per_dollar"] - min_ppd) /
        (max_ppd - min_ppd)
    )

    # Round for readability
    df["value_score"] = df["value_score"].round(2)

    print("\nValue score sample:")
    print(df[[
        "player_name",
        "Salary",
        "projected_fd_points",
        "points_per_dollar",
        "value_score"
    ]].sort_values("value_score", ascending=False).head(10))

    print("\nFD projection sample:")
    print(df[[
        "player_name",
        "Salary",
        "projected_fd_points",
        "points_per_dollar"
    ]].sort_values("projected_fd_points", ascending=False).head(10))

    print("\nProjected PA sample:")
    print(df[[
        "player_name",
        "team",
        "implied_team_total",
        "player_PA_share",
        "PA_multiplier",
        "projected_PA"
    ]].head(10))

    # -----------------------------
    # SAVE OUTPUT
    # -----------------------------
    output_path = os.path.join(base_dir, "../03_output", f"hitter_projections_dfs_{slate_date}.csv")

    df.to_csv(output_path, index=False)

    print(f"\nProjection file saved to: {output_path}")

if __name__ == "__main__":
    main()