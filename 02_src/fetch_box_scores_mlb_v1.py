import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import sys


def fetch_box_score(date):
    print(f"📅 Processing: {date}")

    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}&hydrate=team,linescore,boxscore"
    response = requests.get(url).json()

    rows = []

    for date_data in response.get("dates", []):
        for game in date_data.get("games", []):
            game_id = game["gamePk"]

            box_url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/boxscore"
            box = requests.get(box_url).json()

            for team_side in ["home", "away"]:
                team = box["teams"][team_side]

                for player_id, player in team["players"].items():
                    person = player["person"]["fullName"].lower()
                    team_abbr = team["team"]["abbreviation"]

                    batting = player.get("stats", {}).get("batting", {})
                    if batting:
                        rows.append({
                            "game_id": game_id,
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
                            "SB": batting.get("stolenBases", 0),
                            "K": batting.get("strikeOuts", 0)
                        })

                    pitching = player.get("stats", {}).get("pitching", {})
                    if pitching:
                        rows.append({
                            "game_id": game_id,
                            "player_name": person,
                            "team": team_abbr,
                            "type": "pitcher",
                            "IP": pitching.get("inningsPitched", "0.0"),
                            "ER": pitching.get("earnedRuns", 0),
                            "SO": pitching.get("strikeOuts", 0),
                            "BB_allowed": pitching.get("baseOnBalls", 0),
                            "H_allowed": pitching.get("hits", 0)
                        })

    if not rows:
        print(f"⚠️ No data for {date}")
        return

    df = pd.DataFrame(rows)

    def convert_ip(ip):
        if isinstance(ip, str) and "." in ip:
            whole, frac = ip.split(".")
            return int(whole) + int(frac) / 3
        return float(ip)

    if "IP" in df.columns:
        df["IP"] = df["IP"].apply(convert_ip)

    if "H" in df.columns:
        df["1B"] = df["H"] - df.get("2B", 0) - df.get("3B", 0) - df.get("HR", 0)

    output_path = f"03_output/box_score_{date}.csv"
    df.to_csv(output_path, index=False)

    print(f"✅ Saved: {output_path}")


def main():

    # ✅ SUPPORT SINGLE DATE (PIPELINE)
    if len(sys.argv) == 2:
        date = sys.argv[1]
        fetch_box_score(date)
        return

    # ✅ SUPPORT DATE RANGE (MANUAL USE)
    if len(sys.argv) == 3:
        start_date = datetime.strptime(sys.argv[1], "%Y-%m-%d")
        end_date = datetime.strptime(sys.argv[2], "%Y-%m-%d")

        current = start_date
        while current <= end_date:
            fetch_box_score(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)
        return

    print("Usage:")
    print("Single date: python fetch_box_scores_mlb_v1.py 2026-04-14")
    print("Range: python fetch_box_scores_mlb_v1.py 2026-03-25 2026-04-14")


if __name__ == "__main__":
    main()