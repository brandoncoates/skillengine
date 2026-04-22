import os
import pandas as pd


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    box_score_dir = os.path.join(base_dir, "../03_output")

    files = [
        f for f in os.listdir(box_score_dir)
        if f.startswith("box_score_") and f.endswith(".csv")
    ]

    if not files:
        print("No box score files found.")
        return

    all_dfs = []

    for file in files:
        path = os.path.join(box_score_dir, file)
        df = pd.read_csv(path)

        # ============================
        # ONLY HITTERS
        # ============================
        df = df[(df["type"] == "hitter") & (df["AB"] > 0)].copy()

        # ensure columns exist
        if "K" not in df.columns or "AB" not in df.columns:
            print(f"Skipping {file} — missing K or AB")
            continue

        df["K"] = df["K"].fillna(0)
        df["AB"] = df["AB"].fillna(0)

        all_dfs.append(df[["team", "K", "AB"]])

    if not all_dfs:
        print("No valid hitter data found.")
        return

    combined = pd.concat(all_dfs, ignore_index=True)

    # ============================
    # TEAM AGGREGATION
    # ============================
    team_stats = (
        combined
        .groupby("team")
        .agg(
            total_k=("K", "sum"),
            total_ab=("AB", "sum"),
            plate_appearances=("AB", "sum")  # temp proxy
        )
        .reset_index()
    )

    # ============================
    # K RATE
    # ============================
    team_stats["k_rate"] = team_stats["total_k"] / team_stats["plate_appearances"]
    team_stats["k_rate"] = team_stats["k_rate"].fillna(0)

    # ============================
    # SAVE
    # ============================
    output_dir = os.path.join(base_dir, "../01_data/processed/team_context")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "team_k_rates.csv")

    team_stats.to_csv(output_path, index=False)

    print(f"✅ Team K rates saved to: {output_path}")


if __name__ == "__main__":
    main()