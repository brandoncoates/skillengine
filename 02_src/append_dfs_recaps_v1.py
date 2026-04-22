import os
import sys
import pandas as pd


def main():
    # -----------------------------
    # DATE ARG
    # -----------------------------
    if len(sys.argv) < 2:
        print("Usage: python append_dfs_recaps_v1.py <YYYY-MM-DD>")
        return

    slate_date = sys.argv[1]

    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "../03_output")

    recap_path = os.path.join(output_dir, f"dfs_recap_{slate_date}.csv")
    master_path = os.path.join(output_dir, "dfs_recap_master.csv")

    # -----------------------------
    # LOAD TODAY RECAP
    # -----------------------------
    if not os.path.exists(recap_path):
        print(f"❌ Recap file not found: {recap_path}")
        return

    df = pd.read_csv(recap_path)

    # -----------------------------
    # ADD DATE COLUMN
    # -----------------------------
    df["slate_date"] = slate_date

    # -----------------------------
    # APPEND OR CREATE MASTER
    # -----------------------------
    if os.path.exists(master_path):
        master_df = pd.read_csv(master_path)
        combined = pd.concat([master_df, df], ignore_index=True)
    else:
        combined = df.copy()

    # -----------------------------
    # CLEAN / STANDARDIZE
    # -----------------------------
    if "player_name" in combined.columns:
        combined["player_name"] = (
            combined["player_name"]
            .astype(str)
            .str.strip()
            .str.lower()
        )

    combined["slate_date"] = pd.to_datetime(combined["slate_date"], errors="coerce")

    # force numeric on fields used in calculations
    numeric_cols = [
        "actual_fd_points",
        "projected_fd_points",
        "point_diff",
        "abs_point_diff",
        "pct_diff",
        "abs_pct_diff",
        "points_per_1000",
        "value_score",
        "Salary"
    ]

    for col in numeric_cols:
        if col in combined.columns:
            combined[col] = pd.to_numeric(combined[col], errors="coerce")

    # -----------------------------
    # REMOVE DUPLICATES
    # (same player + same slate_date)
    # -----------------------------
    combined = combined.drop_duplicates(
        subset=["player_name", "slate_date"],
        keep="last"
    )

    # -----------------------------
    # SORT BEFORE ROLLING CALCS
    # -----------------------------
    combined = combined.sort_values(
        by=["player_name", "slate_date"]
    ).reset_index(drop=True)

    # -----------------------------
    # ROLLING AVERAGES
    # Use prior games only via shift(1)
    # -----------------------------
    grouped_actual = combined.groupby("player_name")["actual_fd_points"]

    combined["last_3_avg"] = grouped_actual.transform(
        lambda x: x.shift(1).rolling(3, min_periods=1).mean()
    )

    combined["last_5_avg"] = grouped_actual.transform(
        lambda x: x.shift(1).rolling(5, min_periods=1).mean()
    )

    combined["last_10_avg"] = grouped_actual.transform(
        lambda x: x.shift(1).rolling(10, min_periods=1).mean()
    )

    # -----------------------------
    # TREND TAG
    # Compare short-term form vs longer-term form
    # -----------------------------
    combined["trend_delta"] = combined["last_3_avg"] - combined["last_10_avg"]

    def get_trend_tag(delta):
        if pd.isna(delta):
            return ""
        if delta >= 5:
            return "HOT"
        if delta >= 2:
            return "UP"
        if delta <= -5:
            return "COLD"
        if delta <= -2:
            return "DOWN"
        return "NEUTRAL"

    combined["trend_tag"] = combined["trend_delta"].apply(get_trend_tag)

    # -----------------------------
    # TREND MULTIPLIER
    # -----------------------------
    trend_multiplier_map = {
        "HOT": 1.10,
        "UP": 1.05,
        "NEUTRAL": 1.00,
        "DOWN": 0.95,
        "COLD": 0.90,
        "": 1.00
    }

    combined["trend_multiplier"] = combined["trend_tag"].map(trend_multiplier_map).fillna(1.00)

    # -----------------------------
    # ADJUSTED FANTASY POINTS
    # -----------------------------
    combined["adjusted_fantasy_points"] = (
        combined["projected_fd_points"] * combined["trend_multiplier"]
    )

    # -----------------------------
    # FINAL SORT FOR READABILITY
    # -----------------------------
    combined = combined.sort_values(
        by=["slate_date", "player_name"],
        ascending=[True, True]
    ).reset_index(drop=True)

    # -----------------------------
    # SAVE
    # -----------------------------
    combined.to_csv(master_path, index=False)

    print(f"✅ Master recap file updated: {master_path}")
    print("\nSUMMARY:")
    print("Rows:", len(combined))

    if "slate_date" in combined.columns and len(combined) > 0:
        print("Date range:", combined["slate_date"].min().date(), "to", combined["slate_date"].max().date())

    added_cols = [
        "last_3_avg",
        "last_5_avg",
        "last_10_avg",
        "trend_tag",
        "trend_multiplier",
        "adjusted_fantasy_points"
    ]
    print("Added/maintained columns:", ", ".join(added_cols))


if __name__ == "__main__":
    main()