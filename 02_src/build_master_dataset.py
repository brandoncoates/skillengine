import os
import sys
import pandas as pd

HITTER_RENAME = {
    "pa": "PA",
    "ab": "AB",
    "hit": "H",
    "double": "2B",
    "triple": "3B",
    "home_run": "HR",
    "walk": "BB",
    "strikeout": "SO",
    "on_base_percent": "OBP",
    "slg_percent": "SLG",
    "k_percent": "K_pct",
    "bb_percent": "BB_pct",
}

PITCHER_RENAME = {
    "p_formatted_ip": "IP",
    "strikeout": "SO",
    "walk": "BB",
    "hit": "H",
    "home_run": "HR",
    "k_percent": "K_pct",
    "bb_percent": "BB_pct",
    "p_era": "ERA",
}

REQUIRED_HITTER_COLS = [
    "player_id",
    "last_name, first_name",
    "pa",
    "ab",
    "hit",
    "double",
    "triple",
    "home_run",
    "walk",
    "strikeout",
    "on_base_percent",
    "slg_percent",
    "k_percent",
]

REQUIRED_PITCHER_COLS = [
    "player_id",
    "last_name, first_name",
    "p_formatted_ip",
    "hit",
    "walk",
    "strikeout",
    "home_run",
    "k_percent",
    "bb_percent",
    "p_era",
]

def validate_required_columns(df, required_cols, dataset_name):
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing {dataset_name} columns: {missing_cols}")

def combine_name(df):
    df["player_name"] = df["last_name, first_name"].apply(
        lambda x: " ".join(reversed([part.strip() for part in str(x).split(",", 1)]))
        if "," in str(x) else str(x).strip()
    )
    return df

def convert_ip(ip_series):
    """
    Convert Baseball Savant innings-pitched notation to decimal.
    e.g. 187.1 -> 187.333...   187.2 -> 187.667...   187.0 -> 187.0
    """
    def _convert(val):
        try:
            whole = int(float(val))
            decimal = round(float(val) - whole, 1)
            if abs(decimal - 0.1) < 0.01:
                return whole + 1 / 3
            elif abs(decimal - 0.2) < 0.01:
                return whole + 2 / 3
            else:
                return float(whole)
        except (ValueError, TypeError):
            return float("nan")

    return ip_series.apply(_convert)

def main():
    if len(sys.argv) < 2:
        print("Usage: python build_master_dataset.py <season>")
        sys.exit(1)

    season = sys.argv[1]

    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(base_dir, "../01_data/raw")
    out_dir = os.path.join(base_dir, "../03_output")
    os.makedirs(out_dir, exist_ok=True)

    # ------------------------------------------------------------------ #
    # HITTERS
    # ------------------------------------------------------------------ #
    batting = pd.read_csv(os.path.join(raw_dir, f"{season}_batting.csv"))
    validate_required_columns(batting, REQUIRED_HITTER_COLS, "hitter raw data")

    batting = combine_name(batting)
    batting = batting.rename(columns=HITTER_RENAME)

    hitters = batting[batting["PA"] >= 200].copy()
    hitters.to_csv(os.path.join(out_dir, f"{season}_hitters_master.csv"), index=False)
    print(f"Hitters after filter (PA >= 200): {len(hitters)}")

    # ------------------------------------------------------------------ #
    # PITCHERS
    # ------------------------------------------------------------------ #
    pitching = pd.read_csv(os.path.join(raw_dir, f"{season}_pitching.csv"))
    validate_required_columns(pitching, REQUIRED_PITCHER_COLS, "pitcher raw data")

    pitching = combine_name(pitching)
    pitching = pitching.rename(columns=PITCHER_RENAME)

    pitching["IP"] = convert_ip(pitching["IP"])
    pitching["WHIP"] = (pitching["BB"] + pitching["H"]) / pitching["IP"]

    pitchers = pitching[pitching["IP"] >= 80].copy()
    pitchers.to_csv(os.path.join(out_dir, f"{season}_pitchers_master.csv"), index=False)
    print(f"Pitchers after filter (IP >= 80): {len(pitchers)}")

if __name__ == "__main__":
    main()