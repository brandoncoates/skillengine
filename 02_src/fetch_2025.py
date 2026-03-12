import os
import pybaseball

def main():
    # Create output directory if it doesn't exist
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.abspath(os.path.join(script_dir, "..", "01_data", "raw"))
    os.makedirs(output_dir, exist_ok=True)

    # Pull 2025 batting stats from FanGraphs
    print("Fetching 2025 batting stats...")
    batting = pybaseball.batting_stats(2025, qual=1)
    batting.to_csv(os.path.join(output_dir, "2025_batting.csv"), index=False)
    print(f"Batting rows pulled: {len(batting)}")
    print(f"Batting columns: {list(batting.columns)}\n")

    # Pull 2025 pitching stats from FanGraphs
    print("Fetching 2025 pitching stats...")
    pitching = pybaseball.pitching_stats(2025, qual=1)
    pitching.to_csv(os.path.join(output_dir, "2025_pitching.csv"), index=False)
    print(f"Pitching rows pulled: {len(pitching)}")
    print(f"Pitching columns: {list(pitching.columns)}")

if __name__ == "__main__":
    main()