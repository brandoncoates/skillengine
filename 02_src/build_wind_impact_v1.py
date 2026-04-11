import sys
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\brand\OneDrive\Documents\Analytics\Baseball\SkillEngine")

INPUT_DIR = PROJECT_ROOT / "01_data" / "processed" / "weather"
OUTPUT_DIR = PROJECT_ROOT / "01_data" / "processed" / "weather"


def get_slate_date():
    if len(sys.argv) < 2:
        raise ValueError("Usage: python build_wind_impact_v1.py YYYY-MM-DD")
    return sys.argv[1]


def calculate_wind_score(row):
    if row["roof_type"] == "dome":
        return 0

    speed = row["wind_speed_mph"]
    effect = row["wind_effect"]

    if effect == "out":
        if speed >= 12:
            return 2
        elif speed >= 8:
            return 1
        else:
            return 0

    elif effect == "in":
        if speed >= 12:
            return -2
        elif speed >= 8:
            return -1
        else:
            return 0

    else:
        return 0


def main():
    slate_date = get_slate_date()

    input_file = INPUT_DIR / f"wind_context_{slate_date}.csv"

    if not input_file.exists():
        raise FileNotFoundError(f"Missing file: {input_file}")

    df = pd.read_csv(input_file)

    df["wind_score"] = df.apply(calculate_wind_score, axis=1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = OUTPUT_DIR / f"wind_impact_{slate_date}.csv"

    df.to_csv(output_file, index=False)

    print(f"[OK] Wind impact saved: {output_file}")
    print(df[["team", "wind_speed_mph", "wind_effect", "wind_score"]])


if __name__ == "__main__":
    main()