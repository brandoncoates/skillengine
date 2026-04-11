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

    # -----------------------------
    # INPUT FILES
    # -----------------------------
    history_path = os.path.join(base_dir, "../01_data/processed/hitter_skill_history_v1.csv")
    wind_path = os.path.join(base_dir, f"../01_data/processed/weather/wind_impact_{slate_date}.csv")
    matchup_path = os.path.join(base_dir, f"../03_output/hitter_matchups_dfs_{slate_date}.csv")
    pitcher_path = os.path.join(base_dir, "../01_data/processed/pitcher_skill_history_v1.csv")
    recap_path = os.path.join(base_dir, "../03_output/dfs_recap_master.csv")

    # -----------------------------
    # LOAD DATA
    # -----------------------------
    history_df = pd.read_csv(history_path)
    wind_df = pd.read_csv(wind_path)
    matchup_df = pd.read_csv(matchup_path)

    # -----------------------------
    # FILTER SEASONS
    # -----------------------------
    history_df["season"] = pd.to_numeric(history_df["season"], errors="coerce")
    history_df = history_df[history_df["season"].isin([2023, 2024, 2025])].copy()

    # -----------------------------
    # NORMALIZED KEYS
    # -----------------------------
    history_df["player_name_key"] = normalize_name(history_df["player_name"])
    matchup_df["player_name_key"] = normalize_name(matchup_df["player_name"])
    matchup_df["opposing_pitcher_key"] = normalize_name(matchup_df["opposing_pitcher"])

    # -----------------------------
    # WEIGHTED PA
    # -----------------------------
    season_weights = {2025: 0.5, 2024: 0.3, 2023: 0.2}
    history_df["season_weight"] = history_df["season"].map(season_weights)
    history_df["weighted_PA_component"] = history_df["PA"] * history_df["season_weight"]

    # 🔥 CURRENT SEASON PA (ROLE SIGNAL)
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

    weighted_pa_df = weighted_pa_df[["player_name_key", "weighted_PA"]]

    df = matchup_df.merge(weighted_pa_df, on="player_name_key", how="left")

    df = df.merge(current_pa_df, on="player_name_key", how="left")
    df["current_PA"] = df["current_PA"].fillna(0)

    # -----------------------------
    # 🔥 RECENT PLAYING TIME (NEW)
    # -----------------------------
    try:
        recap_all = pd.read_csv(recap_path)

        recap_all["player_name_key"] = normalize_name(recap_all["player_name"])
        recap_all["slate_date"] = pd.to_datetime(recap_all["slate_date"], errors="coerce")

        recap_all = recap_all.sort_values(["player_name_key", "slate_date"], ascending=[True, False])
        recap_all["rank"] = recap_all.groupby("player_name_key").cumcount() + 1

        recent = recap_all[recap_all["rank"] <= 5].copy()

        recent_pa = (
            recent
            .groupby("player_name_key", as_index=False)["PA"]
            .mean()
            .rename(columns={"PA": "recent_avg_PA"})
        )

        df = df.merge(recent_pa, on="player_name_key", how="left")
        df["recent_avg_PA"] = df["recent_avg_PA"].fillna(0)

    except Exception as e:
        print(f"RECENT PLAYING TIME SKIPPED: {e}")
        df["recent_avg_PA"] = 0

    # -----------------------------
    # WIND
    # -----------------------------
    df = df.merge(
        wind_df[["team", "wind_score"]],
        on="team",
        how="left"
    )
    df["wind_score"] = df["wind_score"].fillna(0)

    df["weighted_PA"] = df["weighted_PA"].fillna(weighted_pa_df["weighted_PA"].mean())

    # -----------------------------
    # OPPORTUNITY (UPDATED)
    # -----------------------------
    df["opportunity_score"] = (
        df["weighted_PA"] * 0.5 +
        df["recent_avg_PA"] * 0.4 +
        df["Salary"] * 0.1
    )

    # 🔥 HARD FILTER (NEW)
    df = df[
        (df["recent_avg_PA"] >= 2.5) |
        (df["weighted_PA"] >= 300)
    ].copy()

    df["rank_within_team"] = df.groupby("team")["opportunity_score"].rank(method="first", ascending=False)

    # 🔥 KEEP TOP 9
    df = df[df["rank_within_team"] <= 9].copy()

    # -----------------------------
    # TEAM SHARE
    # -----------------------------
    df["team_total_PA"] = df.groupby("team")["weighted_PA"].transform("sum")

    # BASE SHARE
    df["player_PA_share"] = df["weighted_PA"] / df["team_total_PA"]

    # 🔥 ROLE ADJUSTMENT USING CURRENT SEASON
    df.loc[df["current_PA"] < 50, "player_PA_share"] *= 0.5
    df.loc[df["current_PA"] < 20, "player_PA_share"] *= 0.25
    df.loc[df["current_PA"] < 10, "player_PA_share"] *= 0.1

    # ROLE ADJUSTMENT
    df.loc[df["weighted_PA"] < 250, "player_PA_share"] *= 0.6
    df.loc[df["weighted_PA"] < 150, "player_PA_share"] *= 0.4

    df["player_PA_share"] = df["player_PA_share"].fillna(1 / 9)

    # -----------------------------
    # PROJECTED PA
    # -----------------------------
    df["team_projected_PA"] = 38
    df["PA_multiplier"] = 1.0

    df["projected_PA"] = (
        df["team_projected_PA"] *
        df["player_PA_share"] *
        df["PA_multiplier"]
    )

    # -----------------------------
    # FINAL FILTER
    # -----------------------------
    df = df[
        (df["weighted_PA"] >= 150) |
        (df["projected_PA"] >= 3.0)
    ].copy()

    # -----------------------------
    # RATES
    # -----------------------------
    for stat in ["1B", "2B", "3B", "HR", "RBI", "R", "SB", "BB"]:
        history_df[f"weighted_{stat}"] = history_df[stat] * history_df["season_weight"]

    agg_dict = {
        "weighted_PA_component": "sum",
    }

    for stat in ["1B", "2B", "3B", "HR", "RBI", "R", "SB", "BB"]:
        agg_dict[f"weighted_{stat}"] = "sum"

    rates_df = (
        history_df
        .groupby("player_name_key", as_index=False)
        .agg(agg_dict)
    )

    for stat in ["1B", "2B", "3B", "HR", "RBI", "R", "SB", "BB"]:
        rates_df[f"rate_{stat}"] = (
            rates_df[f"weighted_{stat}"] /
            rates_df["weighted_PA_component"]
        )

    rate_cols = ["player_name_key"] + [f"rate_{s}" for s in ["1B", "2B", "3B", "HR", "RBI", "R", "SB", "BB"]]
    rate_df = rates_df[rate_cols]

    df = df.merge(rate_df, on="player_name_key", how="left")

    rate_columns = [c for c in df.columns if c.startswith("rate_")]
    for col in rate_columns:
        df[col] = df[col].fillna(df[col].mean())

    # -----------------------------
    # MATCHUP ENGINE (UNCHANGED)
    # -----------------------------
    try:
        pitcher_df = pd.read_csv(pitcher_path)
        pitcher_df["season"] = pd.to_numeric(pitcher_df["season"], errors="coerce")
        pitcher_df["opposing_pitcher_key"] = normalize_name(pitcher_df["player_name"])

        pitcher_latest = (
            pitcher_df
            .sort_values("season", ascending=False)
            .drop_duplicates("opposing_pitcher_key")
            .copy()
        )

        pitcher_latest = pitcher_latest[["opposing_pitcher_key", "SkillScore_v1", "K_pct"]]

        df = df.merge(pitcher_latest, on="opposing_pitcher_key", how="left")

        recap = pd.read_csv(recap_path)
        recap = recap[recap["Position"] == "P"].copy()
        recap["slate_date"] = pd.to_datetime(recap["slate_date"], errors="coerce")
        recap["opposing_pitcher_key"] = normalize_name(recap["player_name"])

        recap = recap.sort_values(["opposing_pitcher_key", "slate_date"], ascending=[True, False])
        recap["rank"] = recap.groupby("opposing_pitcher_key").cumcount() + 1
        recap = recap[recap["rank"] <= 3].copy()

        recap = (
            recap
            .groupby("opposing_pitcher_key", as_index=False)["point_diff"]
            .mean()
            .rename(columns={"point_diff": "form"})
        )

        df = df.merge(recap, on="opposing_pitcher_key", how="left")

        df["SkillScore_v1"] = df["SkillScore_v1"].fillna(df["SkillScore_v1"].mean())
        df["K_pct"] = df["K_pct"].fillna(df["K_pct"].mean())
        df["form"] = df["form"].fillna(0)

        skill_component = safe_zscore(df["SkillScore_v1"])
        k_component = safe_zscore(df["K_pct"])
        form_component = safe_zscore(df["form"])

        df["matchup_score"] = (
            (skill_component * 0.6) +
            (k_component * 0.3) +
            (form_component * 0.1)
        ).clip(-2, 2)

        df["matchup_multiplier"] = 1 + (df["matchup_score"] * 0.03)

        for col in rate_columns:
            df[col] = df[col] * df["matchup_multiplier"]

    except Exception as e:
        print(f"MATCHUP ENGINE SKIPPED: {e}")

    # -----------------------------
    # PROJECTIONS
    # -----------------------------
    for stat in ["1B", "2B", "3B", "HR", "RBI", "R", "SB", "BB"]:
        df[f"proj_{stat}"] = df[f"rate_{stat}"] * df["projected_PA"]

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

    df["projected_fd_points"] = df["projected_fd_points"] * (1 + (df["wind_score"] * 0.05))

    df["points_per_dollar"] = df["projected_fd_points"] / df["Salary"]

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

    df = df.drop(columns=[
        "player_name_key",
        "opposing_pitcher_key",
        "SkillScore_v1",
        "K_pct",
        "form",
        "matchup_score",
        "matchup_multiplier"
    ], errors="ignore")

    output_path = os.path.join(base_dir, "../03_output", f"hitter_projections_dfs_{slate_date}.csv")
    df.to_csv(output_path, index=False)

    print("DONE")


if __name__ == "__main__":
    main()