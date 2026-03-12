# SkillEngine Changelog

This document tracks structural, data, and logic changes to the SkillEngine project.

SkillEngine = core skill model only (no matchup context).

---

## Architecture (Current State as of 1.1)

* Storage Layer: Flat CSV files
* Compute Layer: Python (local environment using .venv)
* Data Source: Baseball Savant CSV exports
* Scope Boundary: Core skill metrics only (no matchup or contextual data)

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
