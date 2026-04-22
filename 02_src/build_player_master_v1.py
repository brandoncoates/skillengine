import os
import pandas as pd
import requests
import time


def fetch_player_data(player_id, retries=3):
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}"

    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except requests.exceptions.RequestException:
            pass

        time.sleep(0.5)

    return None


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    batting_path = os.path.join(base_dir, "../01_data/raw/2025_batting.csv")
    pitching_path = os.path.join(base_dir, "../01_data/raw/2025_pitching.csv")

    batting_df = pd.read_csv(batting_path)
    pitching_df = pd.read_csv(pitching_path)

    # ============================
    # STEP 1 — Collect player IDs
    # ============================
    players = pd.concat([
        batting_df[["player_id"]],
        pitching_df[["player_id"]]
    ]).drop_duplicates()

    player_ids = players["player_id"].dropna().astype(int).unique()

    print(f"Total players to process: {len(player_ids)}")

    # ============================
    # STEP 2 — Pull handedness
    # ============================
    results = []

    for i, player_id in enumerate(player_ids, start=1):
        print(f"[{i}/{len(player_ids)}] Processing player_id: {player_id}")

        data = fetch_player_data(player_id)

        if not data:
            print(f"❌ Failed: {player_id}")
            continue

        person = data.get("people", [{}])[0]

        results.append({
            "player_id": player_id,
            "player_name": person.get("fullName", "").lower(),
            "bat_hand": person.get("batSide", {}).get("code", ""),
            "throw_hand": person.get("pitchHand", {}).get("code", "")
        })

        # small delay to avoid rate limits
        time.sleep(0.05)

    master_df = pd.DataFrame(results).drop_duplicates()

    # ============================
    # STEP 3 — SAVE
    # ============================
    output_dir = os.path.join(base_dir, "../01_data/processed/player_context")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "player_master.csv")

    master_df.to_csv(output_path, index=False)

    print(f"\n✅ Player master saved to: {output_path}")
    print(f"Total successful players: {len(master_df)}")


if __name__ == "__main__":
    main()