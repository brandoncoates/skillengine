import os
import requests
import pandas as pd
from datetime import datetime

TEAM_NAME_MAP = {
    "Arizona Diamondbacks": "ARI",
    "Atlanta Braves": "ATL",
    "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS",
    "Chicago Cubs": "CHC",
    "Chicago White Sox": "CHW",
    "Cincinnati Reds": "CIN",
    "Cleveland Guardians": "CLE",
    "Colorado Rockies": "COL",
    "Detroit Tigers": "DET",
    "Houston Astros": "HOU",
    "Kansas City Royals": "KC",
    "Los Angeles Angels": "LAA",
    "Los Angeles Dodgers": "LAD",
    "Miami Marlins": "MIA",
    "Milwaukee Brewers": "MIL",
    "Minnesota Twins": "MIN",
    "New York Mets": "NYM",
    "New York Yankees": "NYY",
    "Oakland Athletics": "OAK",
    "Philadelphia Phillies": "PHI",
    "Pittsburgh Pirates": "PIT",
    "San Diego Padres": "SD",
    "San Francisco Giants": "SF",
    "Seattle Mariners": "SEA",
    "St. Louis Cardinals": "STL",
    "Tampa Bay Rays": "TB",
    "Texas Rangers": "TEX",
    "Toronto Blue Jays": "TOR",
    "Washington Nationals": "WSH"
}

API_KEY = os.getenv("ODDS_API_KEY")

if not API_KEY:
    raise ValueError("ODDS_API_KEY not set in environment variables")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # --- Output path with today's date ---
    today = datetime.today().strftime("%Y-%m-%d")
    output_path = os.path.join(
        base_dir,
        f"../01_data/raw/vegas/vegas_{today}.csv"
    )

    # --- API endpoint ---
    url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

    params = {
        "apiKey": API_KEY,
        "regions": "us",
        "markets": "h2h,totals,spreads",
        "bookmakers": "draftkings"
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        print("Error fetching data:", response.status_code, response.text)
        return

    data = response.json()

    rows = []

    for game in data:
        home_team = TEAM_NAME_MAP.get(game["home_team"])
        away_team = TEAM_NAME_MAP.get(game["away_team"])

        if home_team is None or away_team is None:
            continue

        bookmakers = game.get("bookmakers", [])
        if not bookmakers:
            continue

        markets = bookmakers[0].get("markets", [])

        moneyline = {}
        total = None
        spread = {}

        for market in markets:
            if market["key"] == "h2h":
                for outcome in market["outcomes"]:
                    team_abbr = TEAM_NAME_MAP.get(outcome["name"])
                    if team_abbr:
                        moneyline[team_abbr] = outcome["price"]

            elif market["key"] == "totals":
                total = market["outcomes"][0]["point"]

            elif market["key"] == "spreads":
                for outcome in market["outcomes"]:
                    team_abbr = TEAM_NAME_MAP.get(outcome["name"])
                    if team_abbr:
                        spread[team_abbr] = outcome["point"]

        if total is None:
            continue

        # --- Add both teams ---
        rows.append({
            "team": home_team,
            "opponent": away_team,
            "game_total": total,
            "moneyline": moneyline.get(home_team),
            "spread": spread.get(home_team)
        })

        rows.append({
            "team": away_team,
            "opponent": home_team,
            "game_total": total,
            "moneyline": moneyline.get(away_team),
            "spread": spread.get(away_team)
        })

    df = pd.DataFrame(rows)
    df["implied_team_total"] = (df["game_total"] / 2) - (df["spread"] / 2)

    # --- Save ---
    df.to_csv(output_path, index=False)

    print(f"Vegas file saved to: {output_path}")

if __name__ == "__main__":
    main()