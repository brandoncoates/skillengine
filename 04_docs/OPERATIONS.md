# SkillEngine Operations (v1.0)

This document defines how SkillEngine is updated and maintained during the season.

---

## Update Cadence

- SkillEngine baseline updates: Weekly
- Recommended update day: Monday morning (after full weekend slate is complete)

---

## Update Process (Manual v1.0)

1. Replace raw season-to-date data files.
2. Re-run full pipeline:
   - raw → master → scored → ranked → top50
3. Validate:
   - Qualification thresholds applied correctly
   - Row counts are reasonable
   - Rankings follow deterministic tie-break rules
4. Overwrite previous season-to-date outputs.

---

## Archiving Policy

- Top 50 files may be archived weekly for historical tracking.
- Master, scored, and ranked files represent current season-to-date state.

---

## Version Bump Rules

- Weight adjustments → Minor version bump (1.1, 1.2, etc.)
- Structural model changes → Major version bump (2.0)
- Bug fixes → Patch version (1.0.1)

---

## In-Season Stability Rule

SkillEngine weights should not change during the season unless evaluation metrics show consistent underperformance over multiple weeks.

---

## Baseline Model Success Criteria (v1.0)

SkillEngine (baseline only) is considered stable if:

- Top 25 ranked hitters consistently outperform league average in OPS over multi-week windows.
- Top 25 ranked pitchers consistently outperform league average in K-rate and WHIP over multi-week windows.
- Week-to-week rank volatility is reasonable (no extreme swings without major performance change).
- Top 50 group maintains higher average fantasy points than overall qualified pool.

SkillEngine is NOT designed to predict daily variance. It measures underlying skill quality.

Evaluation occurs over rolling 3–4 week periods, not single games.

---

## Update Cadence Discipline

- Baseline data refresh: Weekly (Monday morning)
- Baseline weight adjustments: Monthly at most
- Structural model changes: Offseason only
- Predictor (future DailyBoost) weight adjustments: Weekly at most
- No daily weight changes under any circumstance