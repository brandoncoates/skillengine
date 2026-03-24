import os
import pandas as pd

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # --- Paths ---
    data_path = os.path.join(base_dir, "../01_data/processed/hitter_model_dataset_v1.csv")
    output_path = os.path.join(base_dir, "../03_output/hitter_2026_projections_v1_1.csv")

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

    # --- Weighted average ---
    def weighted_avg(group, col):
        return (group[col] * group["weight"]).sum() / group["weight"].sum()

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

    # --- Add player name ---
    name_map = (
        df.sort_values("season")
        .groupby("player_id")
        .tail(1)[["player_id", "last_name, first_name"]]
    )

    import unicodedata

    def normalize_name(name):
        name = name.lower()
        name = name.replace(",", "")
        name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("utf-8")
        return name.strip()

    name_map["normalized_name"] = name_map["last_name, first_name"].apply(
        lambda x: normalize_name(x.split(", ")[1] + " " + x.split(", ")[0])
    )

    projections = projections.merge(name_map, on="player_id", how="left")

    # =========================================================
    # 🔥 IMPROVED ADJUSTMENTS
    # =========================================================

    # SkillScore (slightly stronger influence)
    projections["proj_home_run"] += projections["avg_SkillScore_v1"] * 0.025
    projections["proj_b_rbi"] += projections["avg_SkillScore_v1"] * 0.06
    projections["proj_r_run"] += projections["avg_SkillScore_v1"] * 0.06

    # Trend adjustment (keep modest)
    projections["proj_home_run"] += projections["avg_SkillScore_delta"] * 0.12

    # =========================================================
    # 📊 GLOBAL BIAS CORRECTION (from your evaluation)
    # =========================================================

    projections["proj_home_run"] *= 1.03
    projections["proj_b_rbi"] *= 1.08
    projections["proj_r_run"] *= 1.08
    projections["proj_r_total_stolen_base"] *= 1.05

    # =========================================================

    # --- Round counting stats ---
    projections["proj_home_run"] = projections["proj_home_run"].round(0)
    projections["proj_b_rbi"] = projections["proj_b_rbi"].round(0)
    projections["proj_r_run"] = projections["proj_r_run"].round(0)
    projections["proj_r_total_stolen_base"] = projections["proj_r_total_stolen_base"].round(0)

    # --- Prevent negative values ---
    projections["proj_home_run"] = projections["proj_home_run"].clip(lower=0)
    projections["proj_b_rbi"] = projections["proj_b_rbi"].clip(lower=0)
    projections["proj_r_run"] = projections["proj_r_run"].clip(lower=0)
    projections["proj_r_total_stolen_base"] = projections["proj_r_total_stolen_base"].clip(lower=0)

    # --- Sort by HR ---
    projections = projections.sort_values(by="proj_home_run", ascending=False)

    # --- Save ---
    projections.to_csv(output_path, index=False)

    print(f"2026 hitter projections (v1.1) saved to: {output_path}")


if __name__ == "__main__":
    main()