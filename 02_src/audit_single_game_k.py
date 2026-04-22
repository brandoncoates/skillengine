import pandas as pd

# 🔧 CHANGE THIS TO A REAL GAME_ID FROM YOUR FILE
TARGET_GAME_ID = 823153


def main():
    path = "03_output/box_score_2026-04-13.csv"  # change date if needed
    df = pd.read_csv(path)

    if "game_id" not in df.columns:
        print("❌ No game_id column")
        return

    print("\nAvailable game_ids:")
    print(df["game_id"].dropna().unique())

    if TARGET_GAME_ID is None:
        print("\n👉 Pick one game_id above and rerun with it set.")
        return

    game_df = df[df["game_id"] == TARGET_GAME_ID].copy()

    hitters = game_df[(game_df["type"] == "hitter") & (game_df["AB"] > 0)]
    pitchers = game_df[game_df["type"] == "pitcher"]

    print("\n=== HITTER K BY TEAM ===")
    hitter_k = hitters.groupby("team")["K"].sum()
    print(hitter_k)

    print("\n=== PITCHER SO BY TEAM ===")
    pitcher_k = pitchers.groupby("team")["SO"].sum()
    print(pitcher_k)

    print("\n=== CHECK (SHOULD MATCH CROSS-TEAM) ===")

    teams = list(hitter_k.index)

    if len(teams) == 2:
        t1, t2 = teams[0], teams[1]

        print(f"\n{t1} hitters K: {hitter_k[t1]}")
        print(f"{t2} pitchers SO: {pitcher_k.get(t2, 0)}")

        print(f"\n{t2} hitters K: {hitter_k[t2]}")
        print(f"{t1} pitchers SO: {pitcher_k.get(t1, 0)}")

    else:
        print("⚠️ Not exactly 2 teams — investigate")


if __name__ == "__main__":
    main()