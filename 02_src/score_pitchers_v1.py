import os
import sys
import pandas as pd

def main():
    if len(sys.argv) < 2:
        print("Usage: python score_pitchers_v1.py <season>")
        sys.exit(1)

    season = sys.argv[1]

    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(base_dir, f"../03_output/{season}_pitchers_master.csv")
    output_path = os.path.join(base_dir, f"../03_output/{season}_pitchers_scored_v1.csv")

    df = pd.read_csv(input_path)
    print(f"Rows loaded: {len(df)}")

    cols = df.columns.tolist()

    # --- K-rate (required) ---
    if "K_pct" in df.columns:
        df["K_rate"] = df["K_pct"]
    elif "K%" in df.columns:
        df["K_rate"] = df["K%"]
    elif "SO" in df.columns and "TBF" in df.columns:
        df["K_rate"] = (df["SO"] / df["TBF"]) * 100
    else:
        print("ERROR: Cannot compute K-rate. Need 'K_pct', 'K%', or both 'SO' and 'TBF'.")
        return

    # --- ERA (required) ---
    if "ERA" not in cols:
        sys.exit("ERROR: Cannot compute SkillScore_v1. 'ERA' column is missing.")

    # --- BB-rate (required for v1 unless unavailable) ---
    use_bb = True
    if "BB_pct" in df.columns:
        df["BB_rate"] = df["BB_pct"]
    elif "BB%" in df.columns:
        df["BB_rate"] = df["BB%"]
    elif "BB" in df.columns and "TBF" in df.columns:
        df["BB_rate"] = (df["BB"] / df["TBF"]) * 100
    else:
        print("WARNING: BB-rate not available. Skipping BB component.")
        use_bb = False

    # --- WHIP (required for v1 unless unavailable) ---
    use_whip = True
    if "WHIP" in cols:
        df["whip_val"] = df["WHIP"]
    elif {"H", "BB", "IP"}.issubset(cols):
        df["whip_val"] = (df["H"] + df["BB"]) / df["IP"].replace(0, float("nan"))
    else:
        print("WARNING: WHIP not available. Skipping WHIP component.")
        use_whip = False

    # --- Percentile ranks (0–100) ---
    # Higher K-rate = better
    df["pct_krate"] = df["K_rate"].rank(pct=True) * 100

    # Lower ERA / BB-rate / WHIP = better, so invert ranking
    df["pct_era"] = df["ERA"].rank(pct=True, ascending=False) * 100

    if use_bb:
        df["pct_bbrate"] = df["BB_rate"].rank(pct=True, ascending=False) * 100

    if use_whip:
        df["pct_whip"] = df["whip_val"].rank(pct=True, ascending=False) * 100

    # --- Combine into SkillScore_v1 ---
    # Official v1 weights:
    # 0.35 K-rate percentile
    # 0.20 BB-rate percentile (inverted)
    # 0.25 WHIP percentile (inverted)
    # 0.20 ERA percentile (inverted)
    #
    # If a component is missing, redistribute weights proportionally.

    if use_bb and use_whip:
        df["SkillScore_v1"] = (
            0.35 * df["pct_krate"] +
            0.20 * df["pct_bbrate"] +
            0.25 * df["pct_whip"] +
            0.20 * df["pct_era"]
        )
    elif use_bb and not use_whip:
        df["SkillScore_v1"] = (
            0.35 / 0.75 * df["pct_krate"] +
            0.20 / 0.75 * df["pct_bbrate"] +
            0.20 / 0.75 * df["pct_era"]
        )
    elif use_whip and not use_bb:
        df["SkillScore_v1"] = (
            0.35 / 0.80 * df["pct_krate"] +
            0.25 / 0.80 * df["pct_whip"] +
            0.20 / 0.80 * df["pct_era"]
        )
    else:
        df["SkillScore_v1"] = (
            0.35 / 0.55 * df["pct_krate"] +
            0.20 / 0.55 * df["pct_era"]
        )

    # --- Drop helper columns ---
    helper_cols = [
        "K_rate", "BB_rate", "whip_val",
        "pct_krate", "pct_era", "pct_bbrate", "pct_whip"
    ]
    df = df.drop(columns=[c for c in helper_cols if c in df.columns])

    df.to_csv(output_path, index=False)
    print(f"Rows saved: {len(df)}")

    # --- Display top 10 ---
    display_cols = ["player_name", "IP", "ERA", "SkillScore_v1"]
    top10 = df.nlargest(10, "SkillScore_v1")[display_cols]

    print("\nTop 10 Pitchers by SkillScore_v1:")
    print(top10.to_string(index=False))

if __name__ == "__main__":
    main()