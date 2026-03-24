import os
import pandas as pd

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # --- Paths ---
    data_path = os.path.join(base_dir, "../01_data/processed/hitter_model_dataset_v1.csv")
    output_path = os.path.join(base_dir, "../03_output/hitter_2026_projections_v1.csv")

    df = pd.read_csv(data_path)

    # --- Keep only last 3 seasons ---
    df = df[df["season"].isin([2023, 2024, 2025])]

    # --- Define weights ---
    weights = {
        2025: 0.5,
        2024: 0.3,
        2023: 0.2
    }

    df["weight"] = df["season"].map(weights)

    # --- Weighted average function ---
    def weighted_avg(group, col):
        return (group[col] * group["weight"]).sum() / group["weight"].sum()

    # --- Group by player ---
    grouped = df.groupby("player_id")

    projections = grouped.apply(lambda g: pd.Series({
        "proj_batting_avg": weighted_avg(g, "batting_avg"),
        "proj_home_run": weighted_avg(g, "home_run"),
        "proj_b_rbi": weighted_avg(g, "b_rbi"),
        "proj_r_run": weighted_avg(g, "r_run"),
        "proj_r_total_stolen_base": weighted_avg(g, "r_total_stolen_base"),
        "avg_SkillScore_v1": weighted_avg(g, "SkillScore_v1"),
        "avg_SkillScore_delta": weighted_avg(g, "SkillScore_delta")
    })).reset_index()

    # --- Add player name (latest season) ---
    name_map = (
        df.sort_values("season")
        .groupby("player_id")
        .tail(1)[["player_id", "last_name, first_name"]]
    )

    projections = projections.merge(name_map, on="player_id", how="left")

    # =========================================================
    # 🔥 FIXED ADJUSTMENTS (SAFE + CONTROLLED)
    # =========================================================

    # SkillScore adjustment (small additive)
    projections["proj_home_run"] += projections["avg_SkillScore_v1"] * 0.02

    # Trend adjustment (small additive)
    projections["proj_home_run"] += projections["avg_SkillScore_delta"] * 0.1

    # Apply similar adjustments to RBI and Runs
    projections["proj_b_rbi"] += projections["avg_SkillScore_v1"] * 0.05
    projections["proj_r_run"] += projections["avg_SkillScore_v1"] * 0.05

    # =========================================================

    # --- Round counting stats ---
    projections["proj_home_run"] = projections["proj_home_run"].round(0)
    projections["proj_b_rbi"] = projections["proj_b_rbi"].round(0)
    projections["proj_r_run"] = projections["proj_r_run"].round(0)
    projections["proj_r_total_stolen_base"] = projections["proj_r_total_stolen_base"].round(0)

    # --- Sort by HR ---
    projections = projections.sort_values(by="proj_home_run", ascending=False)

    # --- Save output ---
    projections.to_csv(output_path, index=False)

    print(f"2026 hitter projections saved to: {output_path}")


if __name__ == "__main__":
    main()