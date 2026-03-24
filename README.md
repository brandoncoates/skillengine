# SkillEngine (v1.0)

Python analytics pipeline for evaluating MLB player skill using Statcast leaderboard data and percentile-based scoring models.

SkillEngine is a controlled baseball analytics project focused on **core player skill only**.

It produces percentile-based skill scores for qualified hitters and pitchers using **Baseball Savant leaderboard data** and exports ranked lists including Top 50 outputs.

The system is implemented as a **reproducible Python pipeline** capable of processing **multiple seasons** of data.

---

## Purpose

- Build a resume-ready analytics engineering project with clear scope boundaries, repeatable outputs, and versioned changes.
- Provide a reusable **core skill model** that can serve as the baseline layer for future matchup/context modeling.
- Establish a reproducible pipeline that can process **historical seasons and future seasons without code changes**.

---

## Tech Stack

- Python
- Pandas
- CSV data processing
- Baseball Savant leaderboard exports
- Deterministic ranking algorithms

---

## Scope Boundary (Important)

SkillEngine intentionally does **not** include:

- Home/away splits
- Weather
- Pitch-type matchups
- Ballpark factors
- DFS logic
- Betting odds

Those features will be implemented later in a separate layer called **MatchupEngine**.

SkillEngine evaluates **baseline player skill independent of matchup context**.

---

## Data Sources

SkillEngine uses **Baseball Savant Custom Leaderboard exports**.

Each season requires two raw files:

```
{season}_batting.csv
{season}_pitching.csv
```

Example:

```
2024_batting.csv
2024_pitching.csv
```

Raw files must be placed in:

```
01_data/raw/
```

The exact export process is documented in:

```
04_docs/SAVANT_EXPORT_GUIDE.md
```

This document ensures the raw data can always be reproduced consistently.

---

## Pipeline Execution

The full pipeline runs using:

```
python 02_src/run_skillengine.py {season}
```

Example:

```
python 02_src/run_skillengine.py 2024
```

Pipeline stages:

1. **build_master_dataset.py**
   - Column mapping
   - Data validation
   - Player name normalization
   - Innings conversion
   - WHIP calculation
   - Qualification filtering

2. **score_hitters_v1.py**
   - Percentile calculations
   - SkillScore generation for hitters

3. **score_pitchers_v1.py**
   - Percentile calculations
   - SkillScore generation for pitchers

4. **finalize_rankings_v1.py**
   - Deterministic ranking
   - Top 50 export generation

---

## Qualification Rules

To focus on meaningful sample sizes, the master datasets apply qualification filters.

### Hitters
```
PA ≥ 200
```

### Pitchers
```
IP ≥ 80
```

These thresholds ensure the SkillScore is calculated using players with sufficient playing time.

---

## SkillScore v1.0

All component metrics are first converted to **percentiles within the qualified player pool**, then combined using weighted formulas.

### Hitters

SkillScore =

- 0.45 × OBP percentile
- 0.35 × SLG percentile
- -0.20 × K-rate percentile

### Pitchers

SkillScore =

- 0.35 × K-rate percentile
- -0.20 × BB-rate percentile
- -0.25 × WHIP percentile
- -0.20 × ERA percentile

Interpretation:

Higher **SkillScore** indicates a stronger underlying skill profile relative to the qualified player pool.

---

## Outputs

For each processed season, the pipeline generates the following outputs.

### Master Files

```
{season}_hitters_master.csv
{season}_pitchers_master.csv
```

### Scored Files

```
{season}_hitters_scored_v1.csv
{season}_pitchers_scored_v1.csv
```

### Ranked Files

```
{season}_hitters_ranked_v1.csv
{season}_pitchers_ranked_v1.csv
```

### Top 50 Files

```
{season}_hitters_top50_v1.csv
{season}_pitchers_top50_v1.csv
```

---

## Ranking Rules (Deterministic Sorting)

To ensure rankings are reproducible, ties are resolved using deterministic tie-breakers.

### Hitters Tie-Break Order

1. Higher SkillScore
2. Higher OBP
3. Higher SLG
4. Higher PA

### Pitchers Tie-Break Order

1. Higher SkillScore
2. Higher K-rate
3. Lower WHIP
4. Higher IP

---

## How to Use This

- Use **ranked files** to evaluate the full qualified player pool.
- Use **top50 files** as a quick shortlist for draft research or high-level analysis.
- Treat SkillEngine as the **baseline skill evaluation layer**.

Future systems (MatchupEngine) will adjust these baseline ratings using matchup context.

---

## Versioning & Change Rules

SkillEngine follows semantic-style versioning.

### Major Version (2.0, 3.0, etc.)

Structural or conceptual model changes.

Examples:

- Changing percentile methodology
- Multi-year weighting
- New core architecture

### Minor Version (1.1, 1.2, etc.)

Metric additions, weight adjustments, validation improvements, or ranking refinements.

### Patch Version (1.0.1)

Bug fixes that do not alter scoring logic.

---

## Weight Adjustment Policy

Weights may only change if:

- Evaluation metrics show persistent mis-weighting.
- Changes are documented in `CHANGELOG.md`.
- Post-change validation is recorded.

No silent weight changes.

---

## Change History

See:

```
CHANGELOG.md
```

for versioned model changes, validation notes, and architectural updates.

---

## Trend Analysis (v1.2)

SkillEngine now includes trend analysis for both hitters and pitchers.

This looks at how a player’s SkillScore changes year-to-year.

Scripts:
- analyze_hitter_trends.py
- analyze_pitcher_trends.py

Outputs:
- hitter_trends_v1.csv
- pitcher_trends_v1.csv

New columns:
- prev_SkillScore_v1
- SkillScore_delta
- declining
- improving