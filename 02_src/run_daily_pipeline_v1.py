import os
import sys
from datetime import datetime, timedelta

def run(cmd):
    print(f"\n==============================")
    print(f"Running: {cmd}")
    print(f"==============================\n")
    os.system(cmd)

def main():

    if len(sys.argv) < 2:
        print("Usage: python run_daily_pipeline_v1.py <YYYY-MM-DD>")
        return

    today = sys.argv[1]

    # -----------------------------
    # CALCULATE YESTERDAY
    # -----------------------------
    today_dt = datetime.strptime(today, "%Y-%m-%d")
    yesterday_dt = today_dt - timedelta(days=1)
    yesterday = yesterday_dt.strftime("%Y-%m-%d")

    print(f"\nTODAY: {today}")
    print(f"YESTERDAY: {yesterday}\n")

    # ==========================================================
    # 🔴 YESTERDAY PIPELINE (POST-SLATE)
    # ==========================================================

    print("\n🔴 RUNNING YESTERDAY (EVALUATION PIPELINE)\n")

    run(f"python 02_src/fetch_box_scores_mlb_v1.py {yesterday}")
    run(f"python 02_src/calc_actual_fd_points_v1.py {yesterday}")
    run(f"python 02_src/build_dfs_recap_v1.py {yesterday}")
    run(f"python 02_src/update_player_tracker_v1.py {yesterday}")
    run(f"python 02_src/combine_tracker_files_v1.py {yesterday}")
    run(f"python 02_src/build_player_hit_rates_v1.py {yesterday}")
    run(f"python 02_src/build_dfs_tracking_v1.py {yesterday}")

    # ==========================================================
    # 🟢 TODAY PIPELINE (PRE-SLATE)
    # ==========================================================

    print("\n🟢 RUNNING TODAY (PROJECTION PIPELINE)\n")

    # STEP 0: VEGAS LINES
    run(f"python 02_src/fetch_vegas_lines_v1.py {today}")

    # STEP 1: MATCHUPS
    run(f"python 02_src/build_hitter_matchups_v1.py {today}")

    # STEP 2: HITTER PROJECTIONS
    run(f"python 02_src/build_hitter_projections_v1.py {today}")

    # STEP 3: PITCHER PROJECTIONS
    run(f"python 02_src/build_pitcher_projections_v1.py {today}")

    # STEP 4: DFS POOL
    run(f"python 02_src/build_dfs_pool_v1.py {today}")

    # STEP 5: MANUAL HELPER
    run(f"python 02_src/build_manual_dfs_helper_v1.py {today}")

    print("\n🔥 DAILY PIPELINE COMPLETE 🔥\n")

if __name__ == "__main__":
    main()