# SkillEngine Data Validation

This document defines the validation checks that must pass before the SkillEngine pipeline proceeds.

These checks ensure that upstream data changes do not silently break the model.

---

# Raw Dataset Validation

The following checks should be applied to raw datasets exported from Baseball Savant.

Files:

01_data/raw/2025_batting.csv
01_data/raw/2025_pitching.csv

Required columns must exist before ingestion.

---

## Required Hitter Columns

player_id
last_name, first_name
pa
ab
hit
double
triple
home_run
walk
strikeout
on_base_percent
slg_percent
k_percent

---

## Required Pitcher Columns

player_id
last_name, first_name
p_formatted_ip
hit
walk
strikeout
home_run
k_percent
bb_percent
p_era

---

# Schema Mapping Validation

After ingestion in `build_2025_master.py`, the following columns must exist.

---

## Hitter Master Dataset

Required columns:

player_id
player_name
PA
OBP
SLG
K_pct

---

## Pitcher Master Dataset

Required columns:

player_id
player_name
IP
ERA
WHIP
K_pct
BB_pct

---

# Data Type Validation

The following fields must be numeric.

Hitters:

PA
OBP
SLG
K_pct

Pitchers:

IP
ERA
WHIP
K_pct
BB_pct

---

# Derived Metric Validation

WHIP must be successfully computed using:

WHIP = (H + BB) / IP

Checks:

* IP must not equal zero
* WHIP must not contain null values

---

# Qualification Filter Validation

The qualification filters must reduce the dataset correctly.

Hitters:

PA ≥ 200

Pitchers:

IP ≥ 80

These filters ensure the model evaluates only meaningful sample sizes.

---

# Ranking Validation

After scoring:

* SkillScore_v1 must exist
* Rankings must be sorted descending
* No duplicate ranks should exist
* Output row counts must match input row counts

---

# Purpose

These validation checks protect the SkillEngine pipeline from:

* schema changes
* missing statistics
* incorrect derived metrics
* corrupted ranking outputs

---

# Known Issues

### Character Encoding (Statcast Exports)

Some Statcast CSV exports occasionally produce UTF-8 encoding artifacts
for player names containing accented characters.

Examples:

* "JosÃ© Abreu" instead of "José Abreu"
* "MartÃ­n Maldonado" instead of "Martín Maldonado"
* "AcuÃ±a Jr." instead of "Acuña Jr."

This issue does **not affect model accuracy or data integrity** because
SkillEngine uses `player_id` as the unique identifier for all joins
and historical tracking.

Name normalization and encoding cleanup will be handled later during
the **final modeling dataset preparation stage**.