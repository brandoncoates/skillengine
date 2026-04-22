import os
import pandas as pd
import unicodedata
import sys

if len(sys.argv) < 2:
    print("Usage: python build_pitcher_projections_v1.py <YYYY-MM-DD>")
    sys.exit(1)

slate_date = sys.argv[1]


# =====================================================
# HELPERS
# =====================================================
def normalize_name(name):
    if pd.isna(name):
        return name

    name = str(name).strip().lower()
    name = unicodedata.normalize(
        "NFKD",
        name
    ).encode(
        "ASCII",
        "ignore"
    ).decode("utf-8")

    return name


def safe_num(series):
    if series.std() == 0 or pd.isna(series.std()):
        return pd.Series(0, index=series.index)

    return (series - series.mean()) / series.std()


# =====================================================
# MAIN
# =====================================================
def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # -------------------------------------------------
    # INPUT FILES
    # -------------------------------------------------
    pitcher_path = os.path.join(
        base_dir,
        "../03_output/2025_pitchers_master.csv"
    )

    salary_path = os.path.join(
        base_dir,
        f"../01_data/raw/fanduel/FanDuel-MLB-{slate_date}.csv"
    )

    k_rates_path = os.path.join(
        base_dir,
        "../01_data/processed/team_context/team_k_rates_by_hand.csv"
    )

    hand_path = os.path.join(
        base_dir,
        "../01_data/processed/player_context/player_master.csv"
    )

    audit_path = os.path.join(
        base_dir,
        "../03_output/pitcher_projection_audit.csv"
    )

    recap_master_path = os.path.join(
        base_dir,
        "../03_output/dfs_recap_master.csv"
    )

    # -------------------------------------------------
    # LOAD DATA
    # -------------------------------------------------
    df = pd.read_csv(pitcher_path)
    salary_df = pd.read_csv(salary_path)
    k_rates = pd.read_csv(k_rates_path)
    hand_df = pd.read_csv(hand_path)

    # -------------------------------------------------
    # NORMALIZE NAMES
    # -------------------------------------------------
    df["player_name"] = df["player_name"].apply(normalize_name)
    hand_df["player_name"] = hand_df["player_name"].apply(normalize_name)

    # -------------------------------------------------
    # FILTER FD PITCHERS
    # -------------------------------------------------
    pitcher_salary_df = salary_df[
        (salary_df["Position"] == "P") &
        (salary_df["Probable Pitcher"] == "Yes")
    ].copy()

    pitcher_salary_df["player_name"] = (
        pitcher_salary_df["First Name"].str.strip() + " " +
        pitcher_salary_df["Last Name"].str.strip()
    )

    pitcher_salary_df["player_name"] = pitcher_salary_df[
        "player_name"
    ].apply(normalize_name)

    pitcher_salary_df = pitcher_salary_df[[
        "player_name",
        "Salary",
        "Team",
        "Opponent"
    ]]

    pitcher_salary_df.rename(columns={
        "Team": "team",
        "Opponent": "opponent"
    }, inplace=True)

    pitcher_salary_df["team"] = pitcher_salary_df["team"].str.upper()
    pitcher_salary_df["opponent"] = pitcher_salary_df["opponent"].str.upper()

    # -------------------------------------------------
    # MERGE FD LIST FIRST
    # -------------------------------------------------
    df = pitcher_salary_df.merge(
        df,
        on="player_name",
        how="left"
    )

    # -------------------------------------------------
    # HANDEDNESS
    # -------------------------------------------------
    df = df.merge(
        hand_df[[
            "player_name",
            "throw_hand"
        ]],
        on="player_name",
        how="left"
    )

    df["throw_hand"] = df["throw_hand"].fillna("R")

    # -------------------------------------------------
    # LOAD AUDIT FILE
    # -------------------------------------------------
    try:
        audit_df = pd.read_csv(audit_path)

        audit_df["player_name"] = audit_df[
            "player_name"
        ].apply(normalize_name)

        audit_df = audit_df[[
            "player_name",
            "games",
            "avg_diff",
            "trust_score",
            "bust_rate",
            "quality_rate",
            "smash_rate",
            "hit_rate"
        ]]

        df = df.merge(
            audit_df,
            on="player_name",
            how="left"
        )

    except Exception:
        pass

    # defaults
    df["games"] = df["games"].fillna(0)
    df["avg_diff"] = df["avg_diff"].fillna(0)
    df["trust_score"] = df["trust_score"].fillna(50)
    df["bust_rate"] = df["bust_rate"].fillna(0.35)
    df["quality_rate"] = df["quality_rate"].fillna(0.40)
    df["smash_rate"] = df["smash_rate"].fillna(0.20)
    df["hit_rate"] = df["hit_rate"].fillna(0.50)

    # -------------------------------------------------
    # LOAD TREND DATA
    # -------------------------------------------------
    try:
        recap_df = pd.read_csv(recap_master_path)

        recap_df["player_name"] = recap_df[
            "player_name"
        ].apply(normalize_name)

        recap_df["slate_date"] = pd.to_datetime(
            recap_df["slate_date"],
            errors="coerce"
        )

        recap_df = recap_df[
            recap_df["Position"].astype(str).str.upper().str.contains("P")
        ].copy()

        recap_df = recap_df.sort_values(
            "slate_date"
        ).drop_duplicates(
            "player_name",
            keep="last"
        )

        recap_df = recap_df[[
            "player_name",
            "last_3_avg",
            "last_5_avg",
            "last_10_avg",
            "trend_tag",
            "trend_multiplier",
            "trend_delta"
        ]]

        df = df.merge(
            recap_df,
            on="player_name",
            how="left"
        )

    except Exception:
        pass

    df["trend_tag"] = df["trend_tag"].fillna("NEUTRAL")
    df["trend_multiplier"] = df["trend_multiplier"].fillna(1.00)
    df["trend_delta"] = df["trend_delta"].fillna(0)

    # -------------------------------------------------
    # BASE PITCHING STATS
    # -------------------------------------------------
    df["IP_per_game"] = df["IP"] / df["p_game"]
    df["projected_IP"] = df["IP_per_game"]

    df["K_per_IP"] = df["SO"] / df["IP"]
    df["proj_SO"] = df["projected_IP"] * df["K_per_IP"]

    df["ER_per_IP"] = df["ERA"] / 9
    df["proj_ER"] = df["projected_IP"] * df["ER_per_IP"]

    # defaults for missing
    df["projected_IP"] = df["projected_IP"].fillna(5.0)
    df["proj_SO"] = df["proj_SO"].fillna(4.5)
    df["proj_ER"] = df["proj_ER"].fillna(2.5)

    # -------------------------------------------------
    # BASE FD PROJECTION
    # -------------------------------------------------
    df["projected_fd_points"] = (
        df["projected_IP"] * 3 +
        df["proj_SO"] * 3 +
        df["proj_ER"] * -3
    )

    df["base_projection"] = df["projected_fd_points"]

    # -------------------------------------------------
    # K RATE MATCHUP
    # -------------------------------------------------
    k_rates["team"] = k_rates["team"].str.upper()
    k_rates["vs_hand"] = k_rates["vs_hand"].str.upper()

    df = df.merge(
        k_rates,
        left_on=["opponent", "throw_hand"],
        right_on=["team", "vs_hand"],
        how="left"
    )

    df.rename(columns={
        "k_rate": "opp_k_rate"
    }, inplace=True)

    df["opp_k_rate"] = df["opp_k_rate"].fillna(0.22)

    BASELINE_K = k_rates["k_rate"].mean()

    df["k_diff"] = df["opp_k_rate"] - BASELINE_K

    df["k_boost"] = 1 + (df["k_diff"] * 3.0)
    df["k_boost"] = df["k_boost"].clip(0.85, 1.30)

    df["projected_fd_points"] *= df["k_boost"]

    # -------------------------------------------------
    # TRUST / FORM MULTIPLIER
    # -------------------------------------------------
    df["form_multiplier"] = 1.0

    df["form_multiplier"] += (
        (df["trust_score"] - 50) * 0.0035
    )

    df["form_multiplier"] -= (
        (df["bust_rate"] - 0.35) * 0.20
    )

    df["form_multiplier"] += (
        (df["quality_rate"] - 0.40) * 0.20
    )

    df["form_multiplier"] += (
        df["avg_diff"] * 0.010
    )

    sample_blend = (
        df["games"] / 12
    ).clip(lower=0, upper=1)

    df["form_multiplier"] = (
        1 + (
            (df["form_multiplier"] - 1) *
            sample_blend
        )
    )

    df["form_multiplier"] = df[
        "form_multiplier"
    ].clip(0.80, 1.20)

    df["projected_fd_points"] *= df["form_multiplier"]

    # -------------------------------------------------
    # TREND ENGINE
    # -------------------------------------------------
    df["last_3_avg"] = df["last_3_avg"].fillna(
        df["projected_fd_points"]
    )

    df["last_5_avg"] = df["last_5_avg"].fillna(
        df["last_3_avg"]
    )

    df["last_10_avg"] = df["last_10_avg"].fillna(
        df["last_5_avg"]
    )

    df["recent_form_score"] = (
        df["last_3_avg"] * 0.50 +
        df["last_5_avg"] * 0.30 +
        df["last_10_avg"] * 0.20
    )

    # pitchers less streaky than hitters
    df["projected_fd_points"] = (
        df["projected_fd_points"] * 0.90 +
        df["recent_form_score"] * 0.10
    )

    df["projected_fd_points"] *= df["trend_multiplier"]

    # Hot / cold tags
    df.loc[
        (df["trend_tag"] == "HOT") &
        (df["trust_score"] >= 60),
        "projected_fd_points"
    ] *= 1.03

    df.loc[
        (df["trend_tag"] == "COLD") &
        (df["bust_rate"] >= 0.35),
        "projected_fd_points"
    ] *= 0.94

    # -------------------------------------------------
    # VALUE SCORE
    # -------------------------------------------------
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

    # -------------------------------------------------
    # CLEANUP
    # -------------------------------------------------
    drop_cols = [
        "team_y",
        "vs_hand"
    ]

    df = df.drop(
        columns=drop_cols,
        errors="ignore"
    )

    # -------------------------------------------------
    # SAVE
    # -------------------------------------------------
    output_path = os.path.join(
        base_dir,
        f"../03_output/pitcher_projections_dfs_{slate_date}.csv"
    )

    df.to_csv(
        output_path,
        index=False
    )

    print(f"Pitcher file saved to: {output_path}")


if __name__ == "__main__":
    main()