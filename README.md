# SkillEngine + MatchupEngine + DFS Engine

## Overview

This project is a modular sports analytics system designed to model player performance and generate data-driven DFS (Daily Fantasy Sports) insights.

It is built in three layers:

* **SkillEngine** → evaluates player skill independent of matchup
* **MatchupEngine** → adds game context (opponents, pitchers, Vegas data)
* **DFS Engine** → generates projections, value scores, and rankings

The goal is to create a scalable, automated pipeline for identifying high-value DFS plays.

---

## System Architecture

```
FanDuel Slate Data
        ↓
MatchupEngine (team, opponent, pitcher)
        ↓
Vegas Integration (totals, spreads, implied runs)
        ↓
SkillEngine (player performance metrics)
        ↓
DFS Engine (projections + value scoring + rankings)
```

---

## Current Features

### MatchupEngine v1

* Extracts hitters and starting pitchers from FanDuel slate
* Maps hitters to opposing pitchers
* Integrates Vegas betting data:

  * Game totals
  * Moneylines
  * Spreads
  * Implied team totals
* Produces a clean player-level dataset for modeling

### Vegas Data Integration

* Pulls data from The Odds API
* Normalizes team names for consistent joins
* Filters Vegas data to match DFS slate
* Handles missing data gracefully

### DFS Projection Engine

* Generates hitter projections using opportunity + rate stats
* Generates pitcher projections using IP, SO, ER modeling
* Calculates:

  * projected FanDuel points
  * points per dollar
  * value score (1–10 scale)

### DFS Pool + Helper Outputs

* Combines hitters and pitchers into a unified DFS pool
* Produces:

  * top pitchers
  * top hitters
  * team stacks
  * positional rankings
* Outputs Excel helper for lineup building

### Date-Driven Pipeline

* All scripts run using a single date parameter:

```
python <script>.py YYYY-MM-DD
```

* Eliminates hardcoding
* Enables automation and backtesting

---

## Daily Pipeline (v1)

Run once each morning:

```
python 02_src/run_daily_pipeline_v1.py YYYY-MM-DD
```

Example:

```
python 02_src/run_daily_pipeline_v1.py 2026-03-27
```

---

### 🔴 Yesterday (Post-Slate Evaluation)

* Fetch box scores
* Calculate actual FanDuel points
* Build DFS recap
* Update player tracker
* Combine tracking history
* Calculate hit rates
* Build DFS tracking file

---

### 🟢 Today (Pre-Slate Projections)

* Fetch Vegas lines
* Build hitter matchups
* Generate hitter projections
* Generate pitcher projections
* Build DFS player pool
* Generate DFS manual helper (Excel)

---

## Example Output

### MatchupEngine Output

```
player_name | team | opponent | opposing_pitcher | Salary | game_total | moneyline | spread | implied_team_total
```

---

### DFS Pool Output

```
player_name | Position | team | opponent | Salary | projected_fd_points | value_score
```

---

### DFS Recap Output

```
player_name | projected_fd_points | actual_fd_points | point_diff | pct_diff | result
```

---

## Project Structure

```
01_data/
    raw/
        fanduel/
        vegas/
    processed/

02_src/
    run_daily_pipeline_v1.py
    build_hitter_matchups_v1.py
    build_hitter_projections_v1.py
    build_pitcher_projections_v1.py
    build_dfs_pool_v1.py
    build_manual_dfs_helper_v1.py
    fetch_vegas_lines_v1.py

03_output/
    dfs_pool_YYYY-MM-DD.csv
    dfs_manual_helper_YYYY-MM-DD.xlsx
    dfs_recap_YYYY-MM-DD.csv
    dfs_tracking_YYYY-MM-DD.csv
    player_hit_rates_YYYY-MM-DD.csv

04_docs/
    MATCHUP_ENGINE.md
    CHANGELOG.md
```

---

## How to Run

Run the full daily pipeline:

```
python 02_src/run_daily_pipeline_v1.py YYYY-MM-DD
```

---

## Roadmap

* Model accuracy tracking (prediction vs outcome)
* DFS decision grading (good pick / bad pick / miss)
* Projection calibration (over/under analysis)
* Player trend analysis (rolling performance)
* Stack performance tracking
* Weather and ballpark factors
* Multi-sportsbook Vegas aggregation
* Automated scheduling (cron / GitHub Actions)

---

## Why This Project Matters

Most DFS analysis is manual and subjective.

This system:

* standardizes data inputs
* aligns multiple data sources
* creates a repeatable modeling pipeline
* enables continuous model improvement

The goal is to move from intuition → data-driven decision making.

---

## Author

Brandon Coates
Systems Engineer → Sports Analytics
Building data-driven DFS models and automation pipelines
