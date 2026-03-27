import os
import pandas as pd
import itertools

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    pool_path = os.path.join(base_dir, "../03_output/dfs_pool_2026-03-26.csv")
    df = pd.read_csv(pool_path)

    SALARY_CAP = 35000

    # -----------------------------
    # SPLIT POSITIONS
    # -----------------------------
    pitchers = df[df["Position"] == "P"]

    c1b = df[df["Position"].str.contains("C|1B", na=False)]
    second = df[df["Position"].str.contains("2B", na=False)]
    third = df[df["Position"].str.contains("3B", na=False)]
    short = df[df["Position"].str.contains("SS", na=False)]
    outfield = df[df["Position"].str.contains("OF", na=False)]

    hitters = df[df["Position"] != "P"]

    # -----------------------------
    # REDUCE SEARCH SPACE
    # -----------------------------
    pitchers = pitchers.sort_values("value_score", ascending=False).head(8)

    c1b = c1b.sort_values("value_score", ascending=False).head(6)
    second = second.sort_values("value_score", ascending=False).head(6)
    third = third.sort_values("value_score", ascending=False).head(6)
    short = short.sort_values("value_score", ascending=False).head(6)
    outfield = outfield.sort_values("value_score", ascending=False).head(10)
    hitters = hitters.sort_values("value_score", ascending=False).head(20)

    best_lineups = []

    player_exposure = {}
    MAX_EXPOSURE = 3

    # -----------------------------
    # BUILD ONE LINEUP PER PITCHER
    # -----------------------------
    for p in pitchers.sort_values("value_score", ascending=False).itertuples():

        candidates_for_pitcher = []

        for c in c1b.itertuples():
            for b2 in second.itertuples():
                for b3 in third.itertuples():
                    for ss in short.itertuples():
                        for of_combo in itertools.combinations(outfield.itertuples(), 3):

                            used_names = {
                                p.player_name,
                                c.player_name,
                                b2.player_name,
                                b3.player_name,
                                ss.player_name,
                                of_combo[0].player_name,
                                of_combo[1].player_name,
                                of_combo[2].player_name
                            }

                            # UTIL
                            remaining_hitters = hitters[~hitters["player_name"].isin(used_names)]
                            if remaining_hitters.empty:
                                continue

                            util = remaining_hitters.sort_values("value_score", ascending=False).iloc[0]

                            lineup = [p, c, b2, b3, ss, *of_combo, util]

                            # -----------------------------
                            # STACKING (MIN 2 SAME TEAM)
                            # -----------------------------
                            hitter_teams = [player.team for player in lineup if player.Position != "P"]
                            team_counts = pd.Series(hitter_teams).value_counts()

                            # Relax stacking slightly
                            if team_counts.max() < 2:
                                # allow non-stack ONLY if needed to fill lineups
                                pass

                            salary = sum(player.Salary for player in lineup)
                            if salary > SALARY_CAP:
                                continue

                            points = sum(player.projected_fd_points for player in lineup)

                            candidates_for_pitcher.append({
                                "lineup": lineup,
                                "salary": salary,
                                "points": points
                            })

        if candidates_for_pitcher:

            # sort best → worst
            candidates_for_pitcher = sorted(candidates_for_pitcher, key=lambda x: x["points"], reverse=True)

            chosen = None

            for candidate in candidates_for_pitcher:
                can_use = True

                for player in candidate["lineup"]:
                    name = player.player_name
                    if player_exposure.get(name, 0) >= MAX_EXPOSURE:
                        can_use = False
                        break

                if can_use:
                    chosen = candidate
                    break

            if chosen:
                best_lineups.append(chosen)

                for player in chosen["lineup"]:
                    name = player.player_name
                    player_exposure[name] = player_exposure.get(name, 0) + 1

        # Stop after 5 pitchers
        if len(best_lineups) >= 5:
            break

    # -----------------------------
    # SORT + OUTPUT
    # -----------------------------
    best_lineups = sorted(best_lineups, key=lambda x: x["points"], reverse=True)

    for i, l in enumerate(best_lineups, 1):
        print(f"\nLINEUP {i}")
        print(f"Salary: {l['salary']} | Points: {round(l['points'],2)}")

        for player in l["lineup"]:
            print(f"{player.Position} - {player.player_name} ({player.team} vs {player.opponent}) | ${player.Salary}")

if __name__ == "__main__":
    main()