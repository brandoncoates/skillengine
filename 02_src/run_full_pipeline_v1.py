import os
import sys

def run(cmd):
    print(f"\n==============================")
    print(f"Running: {cmd}")
    print(f"==============================\n")
    os.system(cmd)

def main():

    if len(sys.argv) < 2:
        print("Usage: python run_full_pipeline_v1.py <YYYY-MM-DD>")
        return

    slate_date = sys.argv[1]

    # -----------------------------
    # STEP 1: BUILD MATCHUPS
    # -----------------------------
    run(f"python 02_src/build_hitter_matchups_v1.py {slate_date}")

    # -----------------------------
    # STEP 2: HITTER PROJECTIONS
    # -----------------------------
    run(f"python 02_src/build_hitter_projections_v1.py {slate_date}")

    # -----------------------------
    # STEP 3: PITCHER PROJECTIONS
    # -----------------------------
    run(f"python 02_src/build_pitcher_projections_v1.py {slate_date}")

    # -----------------------------
    # STEP 4: DFS POOL
    # -----------------------------
    run(f"python 02_src/build_dfs_pool_v1.py {slate_date}")

    # -----------------------------
    # STEP 5: MANUAL HELPER
    # -----------------------------
    run(f"python 02_src/build_manual_dfs_helper_v1.py {slate_date}")

    print("\n🔥 FULL DFS PIPELINE COMPLETE 🔥\n")

if __name__ == "__main__":
    main()