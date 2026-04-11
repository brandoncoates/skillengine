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
    raise ValueError("ODDS_API_KEY not set")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    today = datetime.today().strftime("%Y-%m-%d")

    output_path = os.path.join(
        base_dir,
        f"../01_data/raw/vegas/vegas_{today}.csv"
    )

    url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

    params = {
        "apiKey": API_KEY,
        "regions": "us",
        "markets": "h2h,totals,spreads",
        "bookmakers": "draftkings"
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        print("Error:", response.status_code, response.text)
        return

    data = response.json()

    game_dict = {}

    for game in data:
        home = TEAM_NAME_MAP.get(game["home_team"])
        away = TEAM_NAME_MAP.get(game["away_team"])

        if not home or not away:
            continue

        key = tuple(sorted([home, away]))  # unique matchup key

        bookmakers = game.get("bookmakers", [])
        if not bookmakers:
            continue

        markets = bookmakers[0].get("markets", [])

        total = None
        spread = {}
        moneyline = {}

        for market in markets:
            if market["key"] == "totals" and total is None:
                outcomes = market.get("outcomes", [])
                if len(outcomes) >= 2:
                    total = outcomes[0].get("point")

            elif market["key"] == "spreads":
                for o in market["outcomes"]:
                    team = TEAM_NAME_MAP.get(o["name"])
                    if team:
                        spread[team] = o["point"]

            elif market["key"] == "h2h":
                for o in market["outcomes"]:
                    team = TEAM_NAME_MAP.get(o["name"])
                    if team:
                        moneyline[team] = o["price"]

        # Skip bad totals
        if total is None or total < 6 or total > 12:
            continue

        # Keep BEST total per matchup (closest to realistic MLB range)
        if key not in game_dict:
            game_dict[key] = (total, home, away, spread, moneyline)
        else:
            existing_total = game_dict[key][0]

            # prefer totals closer to typical MLB range (~7–10)
            if abs(total - 8.5) < abs(existing_total - 8.5):
                game_dict[key] = (total, home, away, spread, moneyline)

    rows = []

    for total, home, away, spread, moneyline in game_dict.values():
        rows.append({
            "team": home,
            "opponent": away,
            "game_total": total,
            "moneyline": moneyline.get(home),
            "spread": spread.get(home)
        })

        rows.append({
            "team": away,
            "opponent": home,
            "game_total": total,
            "moneyline": moneyline.get(away),
            "spread": spread.get(away)
        })

    df = pd.DataFrame(rows)

    df["implied_team_total"] = (df["game_total"] / 2) - (df["spread"] / 2)

    df.to_csv(output_path, index=False)

    print(f"Vegas file saved: {output_path}")

if __name__ == "__main__":
    main()