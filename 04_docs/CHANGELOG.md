This document tracks structural, data, and logic changes to the SkillEngine project.

SkillEngine = core skill model only (no matchup context).

---

## Architecture (Current State as of 1.3)

* Storage Layer: Flat CSV files
* Compute Layer: Python (local environment using .venv)
* Data Source: Baseball Savant CSV exports + FanDuel + Vegas API
* Scope Boundary:

  * SkillEngine → core skill metrics only
  * MatchupEngine → contextual data (opponents, Vegas, slate)
  * DFS Engine → projections, value scoring, and evaluation

---

## [1.3] - 2026-03-27

### Change Type

Pipeline / Architecture / Automation

### What Changed

* Implemented full daily DFS pipeline:

  * `run_daily_pipeline_v1.py`
* Standardized all scripts to use `slate_date` (removed all hardcoded dates)
* Built DFS projection pipeline:

  * `build_hitter_projections_v1.py`
  * `build_pitcher_projections_v1.py`
  * `build_dfs_pool_v1.py`
  * `build_manual_dfs_helper_v1.py`
* Integrated Vegas pipeline into daily workflow:

  * `fetch_vegas_lines_v1.py` now runs before matchup generation
* Built post-slate evaluation pipeline:

  * `build_dfs_recap_v1.py`
  * `update_player_tracker_v1.py`
  * `combine_tracker_files_v1.py`
  * `build_player_hit_rates_v1.py`
  * `build_dfs_tracking_v1.py`
* Established separation of pipelines:

  * Pre-slate (projections + recommendations)
  * Post-slate (evaluation + tracking)

### Why It Changed

* Eliminate manual script execution and dependency errors
* Remove all hardcoded date issues causing incorrect outputs
* Create a fully automated daily workflow
* Enable consistent evaluation of model performance over time

### Validation Performed

* Verified full pipeline runs successfully with single command
* Confirmed correct file generation for:

  * matchups
  * projections
  * DFS pool
  * manual helper
  * recap
  * tracking
  * hit rates
* Confirmed Vegas data is properly integrated into matchups
* Validated no hardcoded dates remain in pipeline scripts

### Outputs Affected

* dfs_pool_<DATE>.csv
* dfs_manual_helper_<DATE>.xlsx
* dfs_recap_<DATE>.csv
* dfs_tracking_<DATE>.csv
* player_hit_rates_<DATE>.csv

---

## [1.2] - 2026-03-22

### Change Type

Feature / Analysis

### What Changed

* Implemented trend analysis layer for both hitters and pitchers.
* Created hitter trends script: `analyze_hitter_trends.py`
* Created pitcher trends script: `analyze_pitcher_trends.py`
* Added year-over-year SkillScore comparison logic.

### Why It Changed

* Establish a foundation for identifying player performance direction (improving vs declining).
* Enable future modeling and prediction based on historical skill movement.

### Validation Performed

* Verified trend calculations for multiple players across seasons.
* Confirmed correct sorting by `player_id` and `season`.
* Manually validated:

  * Previous season SkillScore (`prev_SkillScore_v1`)
  * Skill score delta (`SkillScore_delta`)
  * Trend flags (`declining`, `improving`)
* Confirmed outputs generate without errors for both hitters and pitchers.

### Outputs Affected

* 03_output/hitter_trends_v1.csv
* 03_output/pitcher_trends_v1.csv

---

## [1.1] - 2026-03-08

### Change Type

Data Source / Pipeline / Schema

### What Changed

* Migrated raw data source from FanGraphs exports to Baseball Savant.
* Updated raw ingestion process using Savant Custom Leaderboards.
* Implemented column mapping layer to standardize Savant fields into SkillEngine schema.
* Added pitcher innings conversion logic to handle Savant IP notation (.1 = 1 out, .2 = 2 outs).
* Implemented in-pipeline WHIP calculation from H, BB, and IP.
* Updated scoring scripts to support `player_name` instead of `Name`.
* Updated rate-stat handling to support `K_pct` and `BB_pct`.
* Corrected ERA mapping (`p_era → ERA`).
* Rebuilt master datasets and scoring pipeline using Savant-derived data.

### Why It Changed

* FanGraphs export functionality became restricted behind a membership requirement.
* Baseball Savant provides stable, publicly accessible data with a consistent CSV export interface.
* Establishing Savant as the raw source ensures long-term stability for the SkillEngine pipeline.

### Validation Performed

* Confirmed raw Savant CSV ingestion.
* Verified column mapping layer correctly standardizes schema.
* Confirmed innings conversion produces correct decimal IP values.
* Verified WHIP calculation accuracy.
* Confirmed scoring scripts execute without schema errors.
* Verified final ranking outputs generate successfully for both hitters and pitchers.

### Outputs Affected

* 2025_hitters_master.csv
* 2025_pitchers_master.csv
* 2025_hitters_scored_v1.csv
* 2025_pitchers_scored_v1.csv
* 2025_hitters_ranked_v1.csv
* 2025_pitchers_ranked_v1.csv
* 2025_hitters_top50_v1.csv
* 2025_pitchers_top50_v1.csv

---

## [1.0] - 2026-02-28

### Change Type

Data / Logic / Output

### What Changed

* Ingested 2025 season batting and pitching data.

* Implemented qualification filters:

  * Hitters: PA ≥ 200
  * Pitchers: IP ≥ 80

* Converted core metrics to percentiles.

* Built SkillScore_v1 weighted formulas:

  * Hitters: 0.45 OBP, 0.35 SLG, -0.20 K-rate
  * Pitchers: 0.35 K-rate, -0.20 BB-rate, -0.25 WHIP, -0.20 ERA

* Generated scored datasets.

* Generated ranked datasets.

* Exported Top 50 hitters and pitchers.

### Why It Changed

* Establish first complete, end-to-end core skill evaluation system for the 2025 season.

### Validation Performed

* Confirmed qualification filters reduced dataset correctly.
* Confirmed percentile transformation applied before weighting.
* Verified ranking outputs sorted correctly by SkillScore.
* Verified Top 50 exports reflect ranked order.

### Outputs Affected

* 2025_hitters_master.csv
* 2025_pitchers_master.csv
* 2025_hitters_scored_v1.csv
* 2025_pitchers_scored_v1.csv
* 2025_hitters_ranked_v1.csv
* 2025_pitchers_ranked_v1.csv
* 2025_hitters_top50_v1.csv
* 2025_pitchers_top50_v1.csv
