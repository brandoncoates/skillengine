import requests
import pandas as pd
from datetime import datetime, timedelta

def get_yesterday():
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

def main():
    date = get_yesterday()

    # MLB schedule endpoint
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}&hydrate=team,linescore,boxscore"

    response = requests.get(url).json()

    rows = []

    for date_data in response.get("dates", []):
        for game in date_data.get("games", []):
            game_id = game["gamePk"]

            # Boxscore endpoint
            box_url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/boxscore"
            box = requests.get(box_url).json()

            for team_side in ["home", "away"]:
                team = box["teams"][team_side]

                for player_id, player in team["players"].items():
                    person = player["person"]["fullName"].lower()
                    team_abbr = team["team"]["abbreviation"]

                    # -----------------------------
                    # HITTERS
                    # -----------------------------
                    batting = player.get("stats", {}).get("batting", {})

                    if batting:
                        rows.append({
                            "player_name": person,
                            "team": team_abbr,
                            "type": "hitter",
                            "AB": batting.get("atBats", 0),
                            "H": batting.get("hits", 0),
                            "2B": batting.get("doubles", 0),
                            "3B": batting.get("triples", 0),
                            "HR": batting.get("homeRuns", 0),
                            "RBI": batting.get("rbi", 0),
                            "R": batting.get("runs", 0),
                            "BB": batting.get("baseOnBalls", 0),
                            "SB": batting.get("stolenBases", 0)
                        })

                    # -----------------------------
                    # PITCHERS
                    # -----------------------------
                    pitching = player.get("stats", {}).get("pitching", {})

                    if pitching:
                        rows.append({
                            "player_name": person,
                            "team": team_abbr,
                            "type": "pitcher",
                            "IP": pitching.get("inningsPitched", "0.0"),
                            "ER": pitching.get("earnedRuns", 0),
                            "SO": pitching.get("strikeOuts", 0),
                            "BB_allowed": pitching.get("baseOnBalls", 0),
                            "H_allowed": pitching.get("hits", 0)
                        })


    df = pd.DataFrame(rows)

    # Convert IP to float (e.g. "5.2" → 5.6667)
    def convert_ip(ip):
        if isinstance(ip, str) and "." in ip:
            whole, frac = ip.split(".")
            return int(whole) + int(frac) / 3
        return float(ip)

    if "IP" in df.columns:
        df["IP"] = df["IP"].apply(convert_ip)

    # Derive singles for hitters
    if "H" in df.columns:
        df["1B"] = df["H"] - df.get("2B", 0) - df.get("3B", 0) - df.get("HR", 0)

    # derive singles
    df["1B"] = df["H"] - df["2B"] - df["3B"] - df["HR"]

    output_path = f"03_output/box_score_{date}.csv"
    df.to_csv(output_path, index=False)

    print(f"Box score saved to: {output_path}")

if __name__ == "__main__":
    main()