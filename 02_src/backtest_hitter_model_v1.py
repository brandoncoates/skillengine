import os
import pandas as pd

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # --- Paths ---
    data_path = os.path.join(base_dir, "../01_data/processed/hitter_model_dataset_v1.csv")
    output_path = os.path.join(base_dir, "../03_output/hitter_backtest_results_v1.csv")

    df = pd.read_csv(data_path)

    results = []

    # --- Backtest years ---
    backtest_years = [2023, 2024, 2025]

    for target_year in backtest_years:

        # --- Define training window ---
        train_df = df[df["season"] < target_year]

        # --- Keep last 3 years only ---
        train_df = train_df[train_df["season"].isin([target_year - 3, target_year - 2, target_year - 1])]

        # --- Define weights ---
        weights = {
            target_year - 1: 0.5,
            target_year - 2: 0.3,
            target_year - 3: 0.2
        }

        train_df["weight"] = train_df["season"].map(weights)

        # --- Weighted avg function ---
        def weighted_avg(group, col):
            return (group[col] * group["weight"]).sum() / group["weight"].sum()

        grouped = train_df.groupby("player_id")

        projections = grouped.apply(lambda g: pd.Series({
            "proj_home_run": weighted_avg(g, "home_run"),
            "proj_b_rbi": weighted_avg(g, "b_rbi"),
            "proj_r_run": weighted_avg(g, "r_run"),
            "proj_r_total_stolen_base": weighted_avg(g, "r_total_stolen_base"),
            "avg_SkillScore_v1": weighted_avg(g, "SkillScore_v1"),
            "avg_SkillScore_delta": weighted_avg(g, "SkillScore_delta")
        })).reset_index()

        # --- Add player name ---
        name_map = (
            train_df.sort_values("season")
            .groupby("player_id")
            .tail(1)[["player_id", "last_name, first_name"]]
        )

        projections = projections.merge(name_map, on="player_id", how="left")

        # --- Adjustments ---
        projections["proj_home_run"] += projections["avg_SkillScore_v1"] * 0.02
        projections["proj_home_run"] += projections["avg_SkillScore_delta"] * 0.1

        projections["proj_b_rbi"] += projections["avg_SkillScore_v1"] * 0.05
        projections["proj_r_run"] += projections["avg_SkillScore_v1"] * 0.05

        # --- Get actuals ---
        actuals = df[df["season"] == target_year][[
            "player_id",
            "home_run",
            "b_rbi",
            "r_run",
            "r_total_stolen_base"
        ]].rename(columns={
            "home_run": "actual_home_run",
            "b_rbi": "actual_b_rbi",
            "r_run": "actual_r_run",
            "r_total_stolen_base": "actual_sb"
        })

        merged = projections.merge(actuals, on="player_id", how="inner")

        # --- Calculate errors ---
        merged["error_home_run"] = merged["proj_home_run"] - merged["actual_home_run"]
        merged["error_b_rbi"] = merged["proj_b_rbi"] - merged["actual_b_rbi"]
        merged["error_r_run"] = merged["proj_r_run"] - merged["actual_r_run"]
        merged["error_sb"] = merged["proj_r_total_stolen_base"] - merged["actual_sb"]

        merged["target_year"] = target_year

        results.append(merged)

    # --- Combine all results ---
    final_df = pd.concat(results, ignore_index=True)

    # --- Save ---
    final_df.to_csv(output_path, index=False)

    print(f"Backtest results saved to: {output_path}")


if __name__ == "__main__":
    main()