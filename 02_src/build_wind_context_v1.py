import sys
import pandas as pd
from pathlib import Path

# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = Path(r"C:\Users\brand\OneDrive\Documents\Analytics\Baseball\SkillEngine")

WEATHER_DIR = PROJECT_ROOT / "01_data" / "processed" / "weather"
ORIENTATION_FILE = PROJECT_ROOT / "01_data" / "static" / "mlb_stadium_orientations.csv"
OUTPUT_DIR = PROJECT_ROOT / "01_data" / "processed" / "weather"


# ============================================================
# ARGUMENTS
# ============================================================

def get_slate_date():
    if len(sys.argv) < 2:
        raise ValueError("Usage: python build_wind_context_v1.py YYYY-MM-DD")
    return sys.argv[1]


# ============================================================
# WIND CLASSIFICATION
# ============================================================

def classify_wind(wind_deg, cf_deg):
    if pd.isna(wind_deg) or pd.isna(cf_deg):
        return "unknown"

    diff = abs(wind_deg - cf_deg)

    if diff > 180:
        diff = 360 - diff

    if diff <= 45:
        return "out"
    elif diff >= 135:
        return "in"
    else:
        return "cross"


# ============================================================
# MAIN
# ============================================================

def main():
    slate_date = get_slate_date()

    weather_file = WEATHER_DIR / f"weather_{slate_date}.csv"

    if not weather_file.exists():
        raise FileNotFoundError(f"Missing weather file: {weather_file}")

    weather_df = pd.read_csv(weather_file)
    orient_df = pd.read_csv(ORIENTATION_FILE)

    df = weather_df.merge(orient_df, on="team", how="left")

    df["wind_effect"] = df.apply(
        lambda row: classify_wind(row["wind_direction_deg"], row["cf_direction_deg"]),
        axis=1
    )

    output_file = OUTPUT_DIR / f"wind_context_{slate_date}.csv"

    df.to_csv(output_file, index=False)

    print(f"[OK] Wind context saved: {output_file}")
    print(df[["team", "wind_speed_mph", "wind_direction_deg", "cf_direction_deg", "wind_effect"]])


if __name__ == "__main__":
    main()