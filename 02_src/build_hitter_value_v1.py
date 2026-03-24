import os
import pandas as pd
import unicodedata

def normalize_name(name):
    name = name.lower()
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("utf-8")
    return name.strip()

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # --- Paths ---
    proj_path = os.path.join(base_dir, "../03_output/hitter_2026_projections_v1_1.csv")
    fd_path = os.path.join(base_dir, "../01_data/raw/fanduel_hitters.csv")
    output_path = os.path.join(base_dir, "../03_output/hitter_value_v1.csv")

    proj = pd.read_csv(proj_path)
    fd = pd.read_csv(fd_path)

    # =========================================================
    # 🔧 NORMALIZE NAMES
    # =========================================================

    # Convert "Last, First" → "First Last"
    proj["normalized_name"] = proj["last_name, first_name"].apply(
        lambda x: normalize_name(x.split(", ")[1] + " " + x.split(", ")[0])
    )

    fd["normalized_name"] = (fd["First Name"] + " " + fd["Last Name"]).apply(normalize_name)

    # =========================================================
    # 🔗 MERGE
    # =========================================================

    merged = proj.merge(fd, on="normalized_name", how="inner")

    # =========================================================
    # 🧠 ESTIMATE FANTASY POINTS
    # =========================================================

    merged["proj_fpts"] = (
        merged["proj_home_run"] * 12
        + merged["proj_b_rbi"] * 3.5
        + merged["proj_r_run"] * 3.2
        + merged["proj_r_total_stolen_base"] * 6
    )

    # =========================================================
    # 💰 VALUE
    # =========================================================

    merged["value"] = merged["proj_fpts"] / merged["Salary"]

    # =========================================================
    # SORT
    # =========================================================

    merged = merged.sort_values(by="value", ascending=False)

    # =========================================================
    # SAVE
    # =========================================================

    merged.to_csv(output_path, index=False)

    print(f"Value file saved to: {output_path}")

if __name__ == "__main__":
    main()