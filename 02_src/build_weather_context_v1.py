import sys
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = Path(r"C:\Users\brand\OneDrive\Documents\Analytics\Baseball\SkillEngine")

STADIUM_FILE = PROJECT_ROOT / "01_data" / "static" / "mlb_stadiums.csv"
OUTPUT_DIR = PROJECT_ROOT / "01_data" / "processed" / "weather"

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


# ============================================================
# ARGUMENTS
# ============================================================

def get_slate_date() -> str:
    if len(sys.argv) < 2:
        raise ValueError("Usage: python 02_src/build_weather_context_v1.py YYYY-MM-DD")

    slate_date = sys.argv[1]

    try:
        datetime.strptime(slate_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("slate_date must be in YYYY-MM-DD format")

    return slate_date


# ============================================================
# GET GAME TIMES (MLB API)
# ============================================================

def get_game_times(slate_date: str) -> dict:
    url = "https://statsapi.mlb.com/api/v1/schedule"

    params = {
        "sportId": 1,
        "date": slate_date
    }

    response = requests.get(url, params=params)
    data = response.json()

    game_times = {}

    for date in data.get("dates", []):
        for game in date.get("games", []):
            game_time = game.get("gameDate")

            home_team = game["teams"]["home"]["team"]["name"].replace("Athletics", "Oakland Athletics")
            away_team = game["teams"]["away"]["team"]["name"].replace("Athletics", "Oakland Athletics")

            # ✅ map BOTH teams
            game_times[home_team] = game_time
            game_times[away_team] = game_time

    return game_times

# ============================================================
# VALIDATION
# ============================================================

def validate_stadium_file(df: pd.DataFrame) -> None:
    required_columns = [
        "team",
        "team_full",
        "stadium",
        "city",
        "state",
        "lat",
        "lon",
        "roof_type",
    ]

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"mlb_stadiums.csv is missing required columns: {missing}")

    if df["team"].duplicated().any():
        dupes = df.loc[df["team"].duplicated(), "team"].tolist()
        raise ValueError(f"Duplicate team values found in mlb_stadiums.csv: {dupes}")


# ============================================================
# WEATHER FETCH
# ============================================================

def fetch_weather_for_team(team_row: pd.Series, game_times: dict) -> dict:
    team = team_row["team"]
    team_full = team_row["team_full"]
    roof_type = team_row["roof_type"]
    lat = team_row["lat"]
    lon = team_row["lon"]

    base_result = {
        "team": team,
        "temp_f": None,
        "wind_speed_mph": None,
        "wind_direction_deg": None,
        "humidity": None,
        "roof_type": roof_type,
    }

    try:
        game_time_str = game_times.get(team_full)

        if not game_time_str:
            print(f"[WARN] No game time found for team={team_full}")
            return base_result

        game_time = datetime.fromisoformat(game_time_str.replace("Z", "+00:00"))

        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,wind_speed_10m,wind_direction_10m,relative_humidity_2m",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "timezone": "auto",
        }

        response = requests.get(OPEN_METEO_URL, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        hourly = data.get("hourly", {})

        times = hourly.get("time", [])

        if not times:
            print(f"[WARN] No hourly time data for team={team}")
            return base_result

        time_objects = [
            datetime.fromisoformat(t).replace(tzinfo=game_time.tzinfo)
            for t in times
        ]

        closest_index = min(
            range(len(time_objects)),
            key=lambda i: abs(time_objects[i] - game_time)
        )

        base_result["temp_f"] = hourly["temperature_2m"][closest_index]
        base_result["wind_speed_mph"] = hourly["wind_speed_10m"][closest_index]
        base_result["wind_direction_deg"] = hourly["wind_direction_10m"][closest_index]
        base_result["humidity"] = hourly["relative_humidity_2m"][closest_index]

        return base_result

    except Exception as e:
        print(f"[WARN] Weather fetch failed for team={team}: {e}")
        return base_result


# ============================================================
# MAIN
# ============================================================

def main():
    slate_date = get_slate_date()

    if not STADIUM_FILE.exists():
        raise FileNotFoundError(f"Missing stadium file: {STADIUM_FILE}")

    stadium_df = pd.read_csv(STADIUM_FILE)
    validate_stadium_file(stadium_df)

    game_times = get_game_times(slate_date)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"weather_{slate_date}.csv"

    results = []
    for _, row in stadium_df.iterrows():
        weather_row = fetch_weather_for_team(row, game_times)
        results.append(weather_row)

    weather_df = pd.DataFrame(
        results,
        columns=[
            "team",
            "temp_f",
            "wind_speed_mph",
            "wind_direction_deg",
            "humidity",
            "roof_type",
        ],
    )

    weather_df.to_csv(output_file, index=False)

    print(f"[OK] Saved weather file: {output_file}")
    print(f"[OK] Rows written: {len(weather_df)}")


if __name__ == "__main__":
    main()