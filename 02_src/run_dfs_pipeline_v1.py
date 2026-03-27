import os
import sys

def run(cmd):
    print(f"\nRunning: {cmd}")
    os.system(cmd)

def main():

    if len(sys.argv) < 2:
        print("Usage: python run_dfs_pipeline_v1.py <YYYY-MM-DD>")
        return

    slate_date = sys.argv[1]

    # STEP 1: Box Scores
    run(f"python 02_src/fetch_box_scores_mlb_v1.py {slate_date}")

    # STEP 2: Actual FD Points
    run(f"python 02_src/calc_actual_fd_points_v1.py {slate_date}")

    # STEP 3: Recap
    run(f"python 02_src/build_dfs_recap_v1.py {slate_date}")

    # STEP 4: Daily Tracker
    run(f"python 02_src/update_player_tracker_v1.py {slate_date}")

    # STEP 5: Combine Tracker
    run(f"python 02_src/combine_tracker_files_v1.py {slate_date}")

    # STEP 6: Hit Rates
    run(f"python 02_src/build_player_hit_rates_v1.py {slate_date}")

    print("\nDFS Pipeline Complete.")

if __name__ == "__main__":
    main()