import os
import subprocess
import sys

def run_step(command):
    print(f"\nRunning {command[1]}...")
    result = subprocess.run(command, check=True)
    if result.returncode == 0:
        print(f"Completed {command[1]}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_skillengine.py <season>")
        sys.exit(1)

    season = sys.argv[1]

    base_dir = os.path.dirname(os.path.abspath(__file__))

    scripts = [
        "build_master_dataset.py",
        "score_hitters_v1.py",
        "score_pitchers_v1.py",
        "finalize_rankings_v1.py",
    ]

    for script in scripts:
        run_step([sys.executable, os.path.join(base_dir, script), season])

    print("\nSkillEngine pipeline completed successfully.")

if __name__ == "__main__":
    main()