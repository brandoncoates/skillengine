# Baseball Savant Export Guide

This document explains how to export the raw data used by SkillEngine from Baseball Savant.

These exports are the source data for the pipeline.

Raw files must be placed in:

01_data/raw/

File naming convention:

{season}_batting.csv
{season}_pitching.csv

Example:

2024_batting.csv
2024_pitching.csv


--------------------------------------------------

HITTER EXPORT

Navigate to:

Baseball Savant
Statcast → Custom Leaderboards → Hitters

Settings:

Season: Desired season
Minimum AB: 10
Leaderboard Type: Custom
Column Set: Basic Stats

Download the CSV.

Save as:

{season}_batting.csv


--------------------------------------------------

PITCHER EXPORT

Navigate to:

Baseball Savant
Statcast → Custom Leaderboards → Pitchers

Settings:

Season: Desired season
Minimum IP: 1
Leaderboard Type: Custom
Column Set: Basic Stats

Important:

ERA must be manually selected in the column list.

Download the CSV.

Save as:

{season}_pitching.csv


--------------------------------------------------

PIPELINE EXECUTION

After exporting both files, place them in:

01_data/raw/

Then run:

python 02_src/run_skillengine.py {season}

Example:

python 02_src/run_skillengine.py 2024