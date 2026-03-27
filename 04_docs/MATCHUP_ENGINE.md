# MatchupEngine v1

## Overview

MatchupEngine is responsible for generating a structured, player-level dataset for daily MLB DFS analysis.

It combines:
- FanDuel slate data (players, teams, salaries)
- Opposing pitcher identification
- Vegas betting data (totals, spreads, implied runs)

This dataset serves as the foundation for the DFS scoring model.

---

## Inputs

### 1. FanDuel Slate File
Location:
01_data/raw/fanduel/FanDuel-MLB-YYYY-MM-DD.csv

Contains:
- Player names
- Team
- Opponent
- Salary
- Position
- Probable pitcher flag

---

### 2. Vegas Data File
Location:
01_data/raw/vegas/vegas_YYYY-MM-DD.csv

Contains:
- Team
- Opponent
- Game total
- Moneyline
- Spread
- Implied team total

---

## Output

Location:
03_output/hitter_matchups_YYYY-MM-DD.csv

Columns:

- player_name
- team
- opponent
- opposing_pitcher
- Salary
- game_total
- moneyline
- spread
- implied_team_total

---

## Data Flow

1. Load FanDuel slate
2. Extract starting pitchers
3. Extract hitters
4. Map hitters → opposing pitchers
5. Build player-level matchup dataset
6. Load Vegas data (if available)
7. Filter Vegas data to match slate games
8. Merge Vegas data into matchup dataset
9. Save final output

---

## Key Logic

### Opposing Pitcher Mapping

Pitchers are filtered using:
- Position == "P"
- Probable Pitcher == "Yes"

Hitters are matched to pitchers using:
hitters.opponent == pitchers.pitcher_team

---

### Vegas Integration

Vegas data is merged using:
team + opponent

Only games present in the FanDuel slate are retained.

---

### Implied Team Total

Calculated as:
implied_team_total = (game_total / 2) - (spread / 2)

- Negative spread → favorite → higher implied total  
- Positive spread → underdog → lower implied total  

---

## How to Run

Run for a specific slate:

python 02_src/build_hitter_matchups_v1.py YYYY-MM-DD

Example:

python 02_src/build_hitter_matchups_v1.py 2026-03-25

If no date is provided, the script defaults to today's date.

---

## Known Limitations

- Vegas data may not be available early in the day  
- Missing Vegas data results in NULL values  
- Only one sportsbook (DraftKings) is currently used  
- No park factors, weather, or recent form included yet  

---

## Next Steps

- Add DFS scoring model  
- Integrate player skill metrics (SkillEngine)  
- Add weather and park factors  
- Expand to multiple sportsbooks  