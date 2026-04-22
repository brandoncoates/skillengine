import os
import pandas as pd


def normalize_name(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
    )


def safe_zscore(series: pd.Series) -> pd.Series:
    std = series.std()
    if pd.isna(std) or std == 0:
        return pd.Series(0, index=series.index)
    return (series - series.mean()) / std


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python build_hitter_projections_v1.py <YYYY-MM-DD>")
        sys.exit(1)

    slate_date = sys.argv[1]
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # =====================================================
    # INPUT FILES
    # =====================================================
    history_path = os.path.join(
        base_dir,
        "../01_data/processed/hitter_skill_history_v1.csv"
    )

    wind_path = os.path.join(
        base_dir,
        f"../01_data/processed/weather/wind_impact_{slate_date}.csv"
    )

    matchup_path = os.path.join(
        base_dir,
        f"../03_output/hitter_matchups_dfs_{slate_date}.csv"
    )

    pitcher_path = os.path.join(
        base_dir,
        "../01_data/processed/pitcher_skill_history_v1.csv"
    )

    audit_path = os.path.join(
        base_dir,
        "../03_output/hitter_projection_audit.csv"
    )

    recap_master_path = os.path.join(
        base_dir,
        "../03_output/dfs_recap_master.csv"
    )

    # =====================================================
    # LOAD DATA
    # =====================================================
    history_df = pd.read_csv(history_path)
    wind_df = pd.read_csv(wind_path)
    matchup_df = pd.read_csv(matchup_path)

    # =====================================================
    # FILTER HISTORY SEASONS
    # =====================================================
    history_df["season"] = pd.to_numeric(
        history_df["season"],
        errors="coerce"
    )

    history_df = history_df[
        history_df["season"].isin([2023, 2024, 2025])
    ].copy()

    # =====================================================
    # NORMALIZED KEYS
    # =====================================================
    history_df["player_name_key"] = normalize_name(
        history_df["player_name"]
    )

    matchup_df["player_name_key"] = normalize_name(
        matchup_df["player_name"]
    )

    matchup_df["opposing_pitcher_key"] = normalize_name(
        matchup_df["opposing_pitcher"]
    )

    # =====================================================
    # SEASON WEIGHTS
    # =====================================================
    season_weights = {
        2025: 0.65,
        2024: 0.25,
        2023: 0.10
    }

    history_df["season_weight"] = history_df["season"].map(
        season_weights
    )

    history_df["weighted_PA_component"] = (
        history_df["PA"] *
        history_df["season_weight"]
    )

    # =====================================================
    # CURRENT PA
    # =====================================================
    current_pa_df = (
        history_df[history_df["season"] == 2025]
        .groupby("player_name_key", as_index=False)["PA"]
        .sum()
        .rename(columns={"PA": "current_PA"})
    )

    weighted_pa_df = (
        history_df
        .groupby("player_name_key", as_index=False)
        .agg({
            "weighted_PA_component": "sum",
            "season_weight": "sum"
        })
    )

    weighted_pa_df["weighted_PA"] = (
        weighted_pa_df["weighted_PA_component"] /
        weighted_pa_df["season_weight"]
    )

    weighted_pa_df = weighted_pa_df[[
        "player_name_key",
        "weighted_PA"
    ]]

    df = matchup_df.merge(
        weighted_pa_df,
        on="player_name_key",
        how="left"
    )

    df = df.merge(
        current_pa_df,
        on="player_name_key",
        how="left"
    )

    df["current_PA"] = df["current_PA"].fillna(0)

    # =====================================================
    # WEATHER
    # =====================================================
    df = df.merge(
        wind_df[["team", "wind_score"]],
        on="team",
        how="left"
    )

    df["wind_score"] = df["wind_score"].fillna(0)

    df["weighted_PA"] = df["weighted_PA"].fillna(
        weighted_pa_df["weighted_PA"].mean()
    )

    # =====================================================
    # LOAD AUDIT DATA
    # =====================================================
    try:
        audit_df = pd.read_csv(audit_path)

        audit_df["player_name_key"] = normalize_name(
            audit_df["player_name"]
        )

        audit_df = audit_df[[
            "player_name_key",
            "games",
            "avg_diff",
            "trust_score",
            "bust_rate",
            "smash_rate",
            "hit_rate"
        ]]

        df = df.merge(
            audit_df,
            on="player_name_key",
            how="left"
        )

    except Exception:
        pass

    # defaults
    df["games"] = df["games"].fillna(0)
    df["avg_diff"] = df["avg_diff"].fillna(0)
    df["trust_score"] = df["trust_score"].fillna(50)
    df["bust_rate"] = df["bust_rate"].fillna(0.35)
    df["smash_rate"] = df["smash_rate"].fillna(0.15)
    df["hit_rate"] = df["hit_rate"].fillna(0.50)

    # =====================================================
    # LOAD RECAP MASTER (NEW TREND LAYER)
    # =====================================================
    try:
        recap_df = pd.read_csv(recap_master_path)

        recap_df["player_name_key"] = normalize_name(
            recap_df["player_name"]
        )

        recap_df["slate_date"] = pd.to_datetime(
            recap_df["slate_date"],
            errors="coerce"
        )

        recap_df = recap_df.sort_values(
            "slate_date"
        ).drop_duplicates(
            "player_name_key",
            keep="last"
        )

        trend_cols = [
            "player_name_key",
            "last_3_avg",
            "last_5_avg",
            "last_10_avg",
            "trend_tag",
            "trend_multiplier",
            "trend_delta"
        ]

        recap_df = recap_df[trend_cols]

        df = df.merge(
            recap_df,
            on="player_name_key",
            how="left"
        )

    except Exception:
        pass

    # trend defaults
    df["last_3_avg"] = df["last_3_avg"].fillna(df["projected_fd_points"] if "projected_fd_points" in df.columns else 8)
    df["last_5_avg"] = df["last_5_avg"].fillna(df["last_3_avg"])
    df["last_10_avg"] = df["last_10_avg"].fillna(df["last_5_avg"])
    df["trend_tag"] = df["trend_tag"].fillna("NEUTRAL")
    df["trend_multiplier"] = df["trend_multiplier"].fillna(1.00)
    df["trend_delta"] = df["trend_delta"].fillna(0)

    # =====================================================
    # OPPORTUNITY SCORE
    # =====================================================
    df["opportunity_score"] = (
        df["weighted_PA"] * 0.15 +
        df["current_PA"] * 0.55 +
        df["Salary"] * 0.10 +
        df["trust_score"] * 2.0 +
        df["implied_team_total"] * 20
    )

    # =====================================================
    # ROLE FILTER
    # =====================================================
    df = df[
        (df["current_PA"] >= 20) |
        (df["weighted_PA"] >= 300)
    ].copy()

    df["rank_within_team"] = df.groupby("team")[
        "opportunity_score"
    ].rank(
        method="first",
        ascending=False
    )

    df = df[
        df["rank_within_team"] <= 9
    ].copy()

    # =====================================================
    # TEAM SHARE
    # =====================================================
    df["team_total_PA"] = df.groupby("team")[
        "weighted_PA"
    ].transform("sum")

    df["player_PA_share"] = (
        df["weighted_PA"] /
        df["team_total_PA"]
    )

    df.loc[df["current_PA"] < 60, "player_PA_share"] *= 0.75
    df.loc[df["current_PA"] < 30, "player_PA_share"] *= 0.50
    df.loc[df["current_PA"] < 15, "player_PA_share"] *= 0.25

    df["player_PA_share"] = df["player_PA_share"].fillna(1 / 9)

    df["team_projected_PA"] = 38

    df["projected_PA"] = (
        df["team_projected_PA"] *
        df["player_PA_share"]
    )

    # =====================================================
    # BUILD EVENT RATES
    # =====================================================
    for stat in [
        "1B", "2B", "3B", "HR",
        "RBI", "R", "SB", "BB"
    ]:
        history_df[f"weighted_{stat}"] = (
            history_df[stat] *
            history_df["season_weight"]
        )

    agg_dict = {
        "weighted_PA_component": "sum"
    }

    for stat in [
        "1B", "2B", "3B", "HR",
        "RBI", "R", "SB", "BB"
    ]:
        agg_dict[f"weighted_{stat}"] = "sum"

    rates_df = (
        history_df
        .groupby("player_name_key", as_index=False)
        .agg(agg_dict)
    )

    for stat in [
        "1B", "2B", "3B", "HR",
        "RBI", "R", "SB", "BB"
    ]:
        rates_df[f"rate_{stat}"] = (
            rates_df[f"weighted_{stat}"] /
            rates_df["weighted_PA_component"]
        )

    rate_cols = ["player_name_key"] + [
        f"rate_{s}" for s in [
            "1B", "2B", "3B", "HR",
            "RBI", "R", "SB", "BB"
        ]
    ]

    rate_df = rates_df[rate_cols]

    df = df.merge(
        rate_df,
        on="player_name_key",
        how="left"
    )

    rate_columns = [
        c for c in df.columns
        if c.startswith("rate_")
    ]

    for col in rate_columns:
        df[col] = df[col].fillna(
            df[col].mean()
        )

    # =====================================================
    # MATCHUP ENGINE
    # =====================================================
    try:
        pitcher_df = pd.read_csv(pitcher_path)

        pitcher_df["season"] = pd.to_numeric(
            pitcher_df["season"],
            errors="coerce"
        )

        pitcher_df["opposing_pitcher_key"] = normalize_name(
            pitcher_df["player_name"]
        )

        pitcher_latest = (
            pitcher_df
            .sort_values("season", ascending=False)
            .drop_duplicates("opposing_pitcher_key")
        )

        pitcher_latest = pitcher_latest[[
            "opposing_pitcher_key",
            "SkillScore_v1",
            "K_pct"
        ]]

        df = df.merge(
            pitcher_latest,
            on="opposing_pitcher_key",
            how="left"
        )

        df["SkillScore_v1"] = df["SkillScore_v1"].fillna(
            df["SkillScore_v1"].mean()
        )

        df["K_pct"] = df["K_pct"].fillna(
            df["K_pct"].mean()
        )

        skill_component = safe_zscore(
            df["SkillScore_v1"]
        )

        k_component = safe_zscore(
            df["K_pct"]
        )

        df["matchup_score"] = (
            (skill_component * 0.65) +
            (k_component * 0.35)
        ).clip(-2, 2)

        df["matchup_multiplier"] = (
            1 + (df["matchup_score"] * 0.03)
        )

        for col in rate_columns:
            df[col] = (
                df[col] *
                df["matchup_multiplier"]
            )

    except Exception:
        df["matchup_multiplier"] = 1.0

    # =====================================================
    # BASE PROJECTIONS
    # =====================================================
    for stat in [
        "1B", "2B", "3B", "HR",
        "RBI", "R", "SB", "BB"
    ]:
        df[f"proj_{stat}"] = (
            df[f"rate_{stat}"] *
            df["projected_PA"]
        )

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

    # wind
    df["projected_fd_points"] *= (
        1 + (df["wind_score"] * 0.05)
    )

    df["base_projection"] = df["projected_fd_points"]

    # =====================================================
    # EXISTING FORM MULTIPLIER
    # =====================================================
    df["form_multiplier"] = 1.0

    df["form_multiplier"] += (
        (df["trust_score"] - 50) * 0.003
    )

    df["form_multiplier"] -= (
        (df["bust_rate"] - 0.35) * 0.18
    )

    df["form_multiplier"] += (
        (df["smash_rate"] - 0.15) * 0.18
    )

    df["form_multiplier"] += (
        df["avg_diff"] * 0.012
    )

    sample_blend = (
        df["games"] / 15
    ).clip(lower=0, upper=1)

    df["form_multiplier"] = (
        1 + (
            (df["form_multiplier"] - 1)
            * sample_blend
        )
    )

    df["form_multiplier"] = df["form_multiplier"].clip(
        0.78,
        1.18
    )

    df["projected_fd_points"] *= df["form_multiplier"]

    # =====================================================
    # NEW TREND ENGINE
    # =====================================================
    df["recent_form_score"] = (
        df["last_3_avg"] * 0.50 +
        df["last_5_avg"] * 0.30 +
        df["last_10_avg"] * 0.20
    )

    df["projected_fd_points"] = (
        df["projected_fd_points"] * 0.85 +
        df["recent_form_score"] * 0.15
    )

    df["projected_fd_points"] *= df["trend_multiplier"]

    # Hot / cold modifiers
    df.loc[
        (df["trend_tag"] == "HOT") &
        (df["trust_score"] >= 55),
        "projected_fd_points"
    ] *= 1.03

    df.loc[
        (df["trend_tag"] == "COLD") &
        (df["bust_rate"] >= 0.40),
        "projected_fd_points"
    ] *= 0.94

    # =====================================================
    # VALUE SCORE
    # =====================================================
    df["points_per_dollar"] = (
        df["projected_fd_points"] /
        df["Salary"]
    )

    min_ppd = df["points_per_dollar"].min()
    max_ppd = df["points_per_dollar"].max()

    if max_ppd == min_ppd:
        df["value_score"] = 5.0
    else:
        df["value_score"] = 1 + 9 * (
            (df["points_per_dollar"] - min_ppd) /
            (max_ppd - min_ppd)
        )

    df["value_score"] = df["value_score"].round(2)

    # =====================================================
    # CLEANUP
    # =====================================================
    df = df.drop(columns=[
        "player_name_key",
        "opposing_pitcher_key",
        "SkillScore_v1",
        "K_pct",
        "matchup_score",
        "matchup_multiplier"
    ], errors="ignore")

    # =====================================================
    # SAVE
    # =====================================================
    output_path = os.path.join(
        base_dir,
        "../03_output",
        f"hitter_projections_dfs_{slate_date}.csv"
    )

    df.to_csv(output_path, index=False)

    print("DONE")


if __name__ == "__main__":
    main()