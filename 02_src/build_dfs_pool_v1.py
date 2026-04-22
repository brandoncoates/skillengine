import os
import pandas as pd
import sys

if len(sys.argv) < 2:
    print("Usage: python build_dfs_pool_v1.py <YYYY-MM-DD>")
    sys.exit(1)

slate_date = sys.argv[1]


def normalize_name(series):
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
    )


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # =====================================================
    # INPUT FILES
    # =====================================================
    hitters_path = os.path.join(
        base_dir,
        f"../03_output/hitter_projections_dfs_{slate_date}.csv"
    )

    pitchers_path = os.path.join(
        base_dir,
        f"../03_output/pitcher_projections_dfs_{slate_date}.csv"
    )

    hitter_audit_path = os.path.join(
        base_dir,
        "../03_output/hitter_projection_audit.csv"
    )

    pitcher_audit_path = os.path.join(
        base_dir,
        "../03_output/pitcher_projection_audit.csv"
    )

    fanduel_path = os.path.join(
        base_dir,
        f"../01_data/raw/fanduel/FanDuel-MLB-{slate_date}.csv"
    )

    # =====================================================
    # LOAD DATA
    # =====================================================
    hitters = pd.read_csv(hitters_path)
    pitchers = pd.read_csv(pitchers_path)
    hitter_audit = pd.read_csv(hitter_audit_path)
    pitcher_audit = pd.read_csv(pitcher_audit_path)
    fanduel = pd.read_csv(fanduel_path)

    # =====================================================
    # NORMALIZE PLAYER NAMES
    # =====================================================
    hitters["player_name"] = normalize_name(hitters["player_name"])
    pitchers["player_name"] = normalize_name(pitchers["player_name"])
    hitter_audit["player_name"] = normalize_name(hitter_audit["player_name"])
    pitcher_audit["player_name"] = normalize_name(pitcher_audit["player_name"])

    fanduel["player_name"] = (
        fanduel["First Name"].astype(str).str.strip().str.lower()
        + " " +
        fanduel["Last Name"].astype(str).str.strip().str.lower()
    )

    # =====================================================
    # ONLY MERGE HITTER AUDIT IF COLUMNS DO NOT ALREADY EXIST
    # Prevents trust_score_x / trust_score_y issues
    # =====================================================
    hitter_needed_cols = [
        "games",
        "avg_diff",
        "trust_score",
        "bust_rate",
        "smash_rate",
        "hit_rate"
    ]

    missing_hitter_cols = [
        col for col in hitter_needed_cols
        if col not in hitters.columns
    ]

    if missing_hitter_cols:
        hitters = hitters.merge(
            hitter_audit[["player_name"] + missing_hitter_cols],
            on="player_name",
            how="left"
        )

    # =====================================================
    # MERGE PITCHER AUDIT
    # =====================================================
    pitcher_needed_cols = [
        "games",
        "trust_score",
        "bust_rate",
        "quality_rate",
        "smash_rate",
        "hit_rate"
    ]

    missing_pitcher_cols = [
        col for col in pitcher_needed_cols
        if col not in pitchers.columns
    ]

    if missing_pitcher_cols:
        pitchers = pitchers.merge(
            pitcher_audit[["player_name"] + missing_pitcher_cols],
            on="player_name",
            how="left"
        )

    # =====================================================
    # FANDUEL TEAM / OPPONENT DATA
    # =====================================================
    fanduel_clean = fanduel[[
        "player_name",
        "Position",
        "Team",
        "Opponent"
    ]].copy()

    fanduel_clean = fanduel_clean.rename(columns={
        "Team": "fd_team",
        "Opponent": "fd_opponent"
    })

    # =====================================================
    # MERGE HITTER TEAM DATA
    # =====================================================
    hitters = hitters.merge(
        fanduel_clean,
        on="player_name",
        how="left"
    )

    hitters["team"] = hitters["fd_team"]
    hitters["opponent"] = hitters["fd_opponent"]

    # =====================================================
    # MERGE PITCHER TEAM DATA
    # =====================================================
    pitchers = pitchers.merge(
        fanduel_clean,
        on="player_name",
        how="left"
    )

    pitchers["team"] = pitchers["fd_team"]
    pitchers["opponent"] = pitchers["fd_opponent"]

    # =====================================================
    # BUILD OPPONENT IMPLIED TOTAL FOR PITCHERS
    # =====================================================
    team_totals = (
        hitters[["team", "implied_team_total"]]
        .drop_duplicates(subset=["team"])
        .rename(columns={
            "team": "opp_team",
            "implied_team_total": "opponent_implied_total"
        })
    )

    pitchers = pitchers.merge(
        team_totals,
        left_on="opponent",
        right_on="opp_team",
        how="left"
    )

    pitchers = pitchers.drop(columns=["opp_team"], errors="ignore")

    # =====================================================
    # ENSURE REQUIRED HITTER COLUMNS EXIST
    # =====================================================
    hitter_cols = [
        "games",
        "trust_score",
        "bust_rate",
        "smash_rate",
        "hit_rate"
    ]

    for col in hitter_cols:
        if col not in hitters.columns:
            hitters[col] = None

    # =====================================================
    # ENSURE REQUIRED PITCHER COLUMNS EXIST
    # =====================================================
    pitcher_cols = [
        "games",
        "trust_score",
        "bust_rate",
        "quality_rate",
        "smash_rate",
        "hit_rate"
    ]

    for col in pitcher_cols:
        if col not in pitchers.columns:
            pitchers[col] = None

    # =====================================================
    # HITTER OUTPUT
    # =====================================================
    hitters_clean = hitters[[
        "player_name",
        "Position",
        "team",
        "opponent",
        "Salary",
        "projected_fd_points",
        "value_score",
        "implied_team_total",
        "wind_score",
        "games",
        "trust_score",
        "bust_rate",
        "smash_rate",
        "hit_rate"
    ]].copy()

    # =====================================================
    # PITCHER OUTPUT
    # =====================================================
    pitchers_clean = pitchers[[
        "player_name",
        "Position",
        "team",
        "opponent",
        "Salary",
        "projected_fd_points",
        "value_score",
        "opponent_implied_total",
        "games",
        "trust_score",
        "bust_rate",
        "quality_rate",
        "smash_rate",
        "hit_rate"
    ]].copy()

    pitchers_clean["implied_team_total"] = None
    pitchers_clean["wind_score"] = None

    # =====================================================
    # SORTING
    # =====================================================
    hitters_clean = hitters_clean.sort_values(
        "value_score",
        ascending=False
    )

    pitchers_clean = pitchers_clean.sort_values(
        ["projected_fd_points", "value_score"],
        ascending=[False, False]
    )

    # =====================================================
    # COMBINE
    # =====================================================
    combined = pd.concat(
        [hitters_clean, pitchers_clean],
        ignore_index=True
    )

    # =====================================================
    # SAVE
    # =====================================================
    output_path = os.path.join(
        base_dir,
        f"../03_output/dfs_pool_{slate_date}.csv"
    )

    combined.to_csv(output_path, index=False)

    print(f"\nDFS pool saved to: {output_path}")


if __name__ == "__main__":
    main()