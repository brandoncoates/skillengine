# SkillEngine Data Source

## Overview

SkillEngine uses seasonal player statistics sourced from Baseball Savant.
These datasets provide season-to-date totals for hitters and pitchers and are updated daily during the MLB season.

The data is exported manually as CSV files from the Baseball Savant Custom Leaderboard tool.

## Data Provider

Primary Source: Baseball Savant (Statcast)

https://baseballsavant.mlb.com

Baseball Savant is maintained by Major League Baseball and provides publicly available Statcast and traditional statistical data.

## Data Retrieval Process

### Hitters Dataset

Navigate to:

Statcast → Custom Leaderboards → Hitters

Settings:

Season: Current Season (example: 2026)
Minimum Plate Appearances: 1
Leaderboard Type: Custom Leaderboard

Selected Columns:

Identity

* player_id
* last_name, first_name
* year
* player_age

Playing Time

* pa
* ab

Hitting Outcomes

* hit
* single
* double
* triple
* home_run
* strikeout
* walk

Rate Statistics

* batting_avg
* on_base_percent
* slg_percent
* k_percent
* bb_percent

Statcast Metrics (optional for future models)

* woba
* xwoba
* hard_hit_percent
* barrel_batted_rate
* sweet_spot_percent

Export the dataset using:

Download CSV

Save file as:

2025_batting.csv

Place the file into:

01_data/raw/

---

### Pitchers Dataset

Navigate to:

Statcast → Custom Leaderboards → Pitchers

Settings:

Season: Current Season (example: 2026)
Minimum Innings Pitched: 1
Leaderboard Type: Custom Leaderboard

Selected Columns:

Identity

* player_id
* last_name, first_name
* year
* player_age

Playing Time

* p_formatted_ip

Pitching Outcomes

* strikeout
* walk
* hit
* home_run

Rate Statistics

* k_percent
* bb_percent
* era

Statcast Metrics (optional for future models)

* woba
* xwoba
* hard_hit_percent
* barrel_batted_rate
* whiff_percent

Export the dataset using:

Download CSV

Save file as:

2025_pitching.csv

Place the file into:

01_data/raw/

---

## Derived Metrics

Some metrics required by SkillEngine are calculated within the data pipeline.

Example:

WHIP = (walk + hit) / IP

Where:

IP = p_formatted_ip

These derived metrics ensure reproducibility and avoid dependence on externally calculated statistics.

---

## Data Update Schedule

Data is refreshed weekly.

Recommended update schedule:

Monday morning (after the full weekend slate of games).

Update workflow:

1. Export new hitter and pitcher CSV files from Baseball Savant.
2. Replace files in 01_data/raw/.
3. Run SkillEngine pipeline.

---

## Data Integrity Notes

* `player_id` is used as the primary player identifier across seasons.
* Minimum playing time filters (PA ≥ 200 for hitters, IP ≥ 80 for pitchers) are applied within the SkillEngine pipeline rather than during data export.
* Raw datasets include all players to preserve flexibility for future analysis.

---

## Future Expansion

The Savant dataset includes additional Statcast metrics such as:

* barrel_batted_rate
* hard_hit_percent
* whiff_percent
* xwoba

These metrics may be incorporated into future SkillEngine model versions.
