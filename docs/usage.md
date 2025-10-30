# NHL Prediction Pipeline – Usage Overview

This project ingests NHL team/game data, engineers matchup-level features, and trains a logistic regression model to predict whether the home team wins.

## Directory Layout
- `data/nhl_teams.csv` – static lookup of active NHL franchises.
- `src/nhl_prediction/data_ingest.py` – fetches game-level stats from the NHL Stats REST API, aligns home/away teams, and builds one row per game.
- `src/nhl_prediction/features.py` – computes season-to-date, rolling-form, and situational features for each team prior to a game.
- `src/nhl_prediction/pipeline.py` – orchestrates ingestion + feature engineering and assembles the modelling matrix.
- `src/nhl_prediction/train.py` – Typer CLI that trains the baseline model and prints evaluation metrics.
- `src/nhl_prediction/report.py` *(added below)* – generates shareable predictions + plots.

## Quick Start
1. **Create a virtual environment & install deps**
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```
2. **Train & evaluate the baseline model**
   ```bash
   PYTHONPATH=src .venv/bin/python -m nhl_prediction.train
   ```
   - Trains on seasons `20212022` + `20222023`, evaluates on `20232024`.
   - Outputs accuracy, log loss, Brier score, ROC-AUC.

## What The Pipeline Does
1. **Fetch game logs** (`fetch_multi_season_logs`)  
   Uses `https://api.nhle.com/stats/rest/en/team/summary` to pull every regular-season game for requested seasons (one row per team per game).
2. **Engineer team features** (`engineer_team_features`)  
   - Season win %, goal differential, shot margin.  
   - Rolling 5/10 game averages (win %, special teams, faceoffs).  
   - Rest indicators (days since previous game).
3. **Assemble games** (`build_game_dataframe`)  
   - Merges home & away team rows into a single record.  
   - Computes feature differentials (home minus away) and target `home_win`.
4. **Train model** (`train.py`)  
   - Scales features, fits logistic regression.  
   - Reports metrics vs. majority-class baseline.

## Extending / Predicting Future Games
- Call `build_dataset` with additional seasons (e.g. the upcoming season) to extend training data.
- For upcoming games not yet recorded, fetch the season-to-date logs up to the day prior, engineer features, and feed the model.

## Visualization Options
See `src/nhl_prediction/report.py` (explained next) for producing CSV outputs and charts that non-technical stakeholders can review.
