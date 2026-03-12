# SkillEngine Column Mapping

## Overview

SkillEngine uses Baseball Savant as the raw data source.
However, Savant column names differ from the standardized column names used internally by the SkillEngine pipeline.

This document defines the mapping between:

* Raw Savant dataset columns
* Internal SkillEngine column names

The pipeline performs this mapping during the data loading step.

---

# Hitters Column Mapping

| Savant Column         | SkillEngine Column | Notes                     |
| --------------------- | ------------------ | ------------------------- |
| player_id             | player_id          | Primary player identifier |
| last_name, first_name | player_name        | Combined name field       |
| year                  | season             | Season identifier         |
| player_age            | age                | Player age during season  |
| pa                    | PA                 | Plate appearances         |
| ab                    | AB                 | At-bats                   |
| hit                   | H                  | Hits                      |
| single                | 1B                 | Singles                   |
| double                | 2B                 | Doubles                   |
| triple                | 3B                 | Triples                   |
| home_run              | HR                 | Home runs                 |
| walk                  | BB                 | Walks                     |
| strikeout             | SO                 | Strikeouts                |
| batting_avg           | AVG                | Batting average           |
| on_base_percent       | OBP                | On-base percentage        |
| slg_percent           | SLG                | Slugging percentage       |
| k_percent             | K_pct              | Strikeout rate            |
| bb_percent            | BB_pct             | Walk rate                 |

---

# Pitchers Column Mapping

| Savant Column         | SkillEngine Column | Notes                     |
| --------------------- | ------------------ | ------------------------- |
| player_id             | player_id          | Primary player identifier |
| last_name, first_name | player_name        | Combined name field       |
| year                  | season             | Season identifier         |
| player_age            | age                | Player age during season  |
| p_formatted_ip        | IP                 | Innings pitched           |
| strikeout             | SO                 | Strikeouts                |
| walk                  | BB                 | Walks                     |
| hit                   | H                  | Hits allowed              |
| home_run              | HR                 | Home runs allowed         |
| k_percent             | K_pct              | Strikeout rate            |
| bb_percent            | BB_pct             | Walk rate                 |
| p_era                   | ERA                | Earned run average        |

---

# Derived Metrics

Some statistics are calculated during the SkillEngine pipeline rather than coming directly from the dataset.

Example:

WHIP

WHIP = (BB + H) / IP

This ensures the model uses a transparent and reproducible calculation.

---

# Purpose of Mapping Layer

This mapping layer provides several benefits:

* Decouples the model from the raw data source
* Allows future dataset changes without breaking the pipeline
* Improves code readability
* Supports potential future data providers
