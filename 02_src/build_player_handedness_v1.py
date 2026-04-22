import os
import pandas as pd
import requests


def normalize_name(name):
    return str(name).strip().lower()


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    fd_dir = os.path.join(base_dir, "../01_data/raw/fanduel")

    files = [
        f for f in os.listdir(fd_dir)
        if f.startswith("FanDuel-MLB-") and f.endswith(".csv")
    ]

    if not files:
        print("No FanDuel files found.")
        return

    # ============================
    # STEP 1 — Collect players
    # ============================
    all_players = []

    for file in files:
        path = os.path.join(fd_dir, file)
        df = pd.read_csv(path)

        df["player_name"] = df["Nickname"].apply(normalize_name)
        df["team"] = df["Team"]

        players = df[["player_name", "team"]].drop_duplicates()

        all_players.append(players)

    combined_players = pd.concat(all_players, ignore_index=True).drop_duplicates()

    # ============================
    # STEP 2 — Get team IDs
    # ============================
    url = "https://statsapi.mlb.com/api/v1/teams?sportId=1"
    teams_resp = requests.get(url, timeout=5).json()

    team_map = {
        t.get("abbreviation"): t.get("id")
        for t in teams_resp.get("teams", [])
    }

    # ============================
    # STEP 3 — Build roster lookup
    # ============================
    roster_data = {}

    for team in combined_players["team"].unique():
        team_id = team_map.get(team)

        if not team_id:
            continue

        roster_url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster"
        roster_resp = requests.get(roster_url, timeout=5).json()

        for player in roster_resp.get("roster", []):
            person = player.get("person", {})

            player_id = person.get("id")
            full_name = normalize_name(person.get("fullName"))

            roster_data[(full_name, team)] = player_id

    # ============================
    # STEP 4 — Pull handedness
    # ============================
    results = []

    for _, row in combined_players.iterrows():
        name = row["player_name"]
        team = row["team"]

        player_id = roster_data.get((name, team))

        if not player_id:
            continue

        try:
            detail_url = f"https://statsapi.mlb.com/api/v1/people/{player_id}"
            detail_resp = requests.get(detail_url, timeout=5).json()
        except:
            continue

        person = detail_resp.get("people", [{}])[0]

        bat_hand = person.get("batSide", {}).get("code", "")
        throw_hand = person.get("pitchHand", {}).get("code", "")

        results.append({
            "player_id": player_id,
            "player_name": name,
            "bat_hand": bat_hand,
            "throw_hand": throw_hand
        })

    # ============================
    # STEP 5 — SAVE
    # ============================
    output_dir = os.path.join(base_dir, "../01_data/processed/player_context")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "player_handedness.csv")

    df_out = pd.DataFrame(results).drop_duplicates(subset=["player_id"])
    df_out.to_csv(output_path, index=False)

    print(f"✅ Handedness file saved to: {output_path}")


if __name__ == "__main__":
    main()