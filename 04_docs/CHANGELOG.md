# CHANGELOG

This document tracks structural, data, and logic changes to the SkillEngine project.

SkillEngine = core skill model only (no matchup context).

---

## Architecture (Current State as of 1.4)

* Storage Layer: Flat CSV files
* Compute Layer: Python (local environment using .venv)
* Data Sources:

  * Baseball Savant CSV exports
  * FanDuel salary/slate files
  * Vegas API
  * Weather / wind files
  * Historical DFS recap master

* Scope Boundary:

  * SkillEngine → core player skill metrics only
  * MatchupEngine → opponents, handedness, weather, Vegas, slate context
  * DFS Engine → projections, rankings, value scoring, trust/trend adjustments, evaluation
  * Content Engine → article exports, helper sheets, publishing outputs

---

## [1.4] - 2026-04-23

### Change Type

Projection Logic / Evaluation / Publishing / Model Intelligence

### What Changed

### DFS Projection Engine Upgrades

* Added historical trust / reliability layer to hitter and pitcher projections.

New variables integrated:

* `trust_score`
* `bust_rate`
* `smash_rate`
* `quality_rate`
* `avg_diff`
* `games`

* Added recap master trend engine to projections.

New trend variables integrated:

* `last_3_avg`
* `last_5_avg`
* `last_10_avg`
* `trend_tag`
* `trend_multiplier`
* `trend_delta`

### Hitter Projection Enhancements

* Added weighted recent form score:

  * 50% last_3_avg
  * 30% last_5_avg
  * 20% last_10_avg

* Added trend-adjusted final hitter projection.
* Added hot-player bonuses.
* Added cold-player penalties.
* Added regression controls for small sample sizes.

### Pitcher Projection Enhancements

* Added recent form weighting (lighter than hitters).
* Added trust / bust / quality adjustments.
* Added hot/cold pitcher modifiers.
* Added safer weighting to prevent overreaction to streaks.

### Matchup / Data Fixes

* Corrected hitter handedness and opposing pitcher handedness merge issues caused by inconsistent name formats.
* Restored platoon split accuracy in matchup generation.

### Evaluation Engine Upgrades

* Rebuilt `dfs_recap_master.csv` historical engine.
* Restored rolling historical metrics:

  * last_3_avg
  * last_5_avg
  * last_10_avg

* Restored trend classification system.
* Restored adjusted projection fields.

### Manual Helper / Publishing Upgrades

* Added automated article export file:

  * `goatland_article_<DATE>.txt`

* Added HTML-ready copy/paste sections for:

  * Top Pitchers
  * Top Hitters
  * Top Stacks
  * By Position

* Improved daily content publishing workflow for WordPress.

### Why It Changed

* Reduce stale recommendations driven only by season-long averages.
* Improve identification of hot players and slumping players.
* Reduce lineup zeroes and volatile cash-game plays.
* Improve projection realism using recent DFS outcomes.
* Speed up daily publishing workflow.

### Validation Performed

* Confirmed hitter and pitcher projection files populate trend fields.
* Verified recap master rolling averages updating correctly.
* Confirmed trend multipliers applying to projections.
* Confirmed helper file exports clean HTML article sections.
* Confirmed historical metrics populate after 4/13 issue fix.
* Manual spot-checks showed stronger rankings for in-form players.

### Outputs Affected

* hitter_projections_dfs_<DATE>.csv
* pitcher_projections_dfs_<DATE>.csv
* dfs_pool_<DATE>.csv
* dfs_manual_helper_<DATE>.xlsx
* goatland_article_<DATE>.txt
* dfs_recap_master.csv

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

  * `fetch_vegas_lines_v1.py`

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

* Eliminate manual script execution and dependency errors.
* Remove hardcoded date failures.
* Create fully automated daily workflow.
* Enable consistent long-term model evaluation.

### Validation Performed

* Verified full pipeline runs successfully.
* Confirmed correct file generation across all steps.
* Validated Vegas integration.
* Confirmed no hardcoded dates remain.

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

* Implemented trend analysis layer for hitters and pitchers.
* Added:

  * `analyze_hitter_trends.py`
  * `analyze_pitcher_trends.py`

* Added year-over-year SkillScore comparisons.

### Why It Changed

* Identify improving vs declining players.
* Build future prediction signals.

### Validation Performed

* Verified trend calculations across seasons.
* Confirmed proper sorting and deltas.

### Outputs Affected

* hitter_trends_v1.csv
* pitcher_trends_v1.csv

---

## [1.1] - 2026-03-08

### Change Type

Data Source / Pipeline / Schema

### What Changed

* Migrated from FanGraphs exports to Baseball Savant.
* Added mapping layer.
* Added IP conversion logic.
* Added WHIP calculations.
* Updated schema compatibility.

### Why It Changed

* FanGraphs access restrictions.
* Savant offered stable public source.

### Validation Performed

* Verified ingestion and mapping.
* Confirmed scoring outputs.

### Outputs Affected

* 2025_hitters_master.csv
* 2025_pitchers_master.csv
* ranked/scored outputs

---

## [1.0] - 2026-02-28

### Change Type

Data / Logic / Output

### What Changed

* Built first complete 2025 skill model.
* Qualification filters.
* Percentile scoring.
* SkillScore formulas for hitters and pitchers.
* Rankings + Top 50 exports.

### Why It Changed

* Establish first complete end-to-end SkillEngine.

### Validation Performed

* Confirmed rankings and outputs.

### Outputs Affected

* 2025_hitters_master.csv
* 2025_pitchers_master.csv
* ranked/scored outputs