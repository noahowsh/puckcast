# NHL Predictive Model Taxonomy

This document describes the core data entities, relationships, and feature families used to build the NHL game prediction pipeline.

## 1. Entities
- **Team (`data/nhl_teams.csv`)**  
  - `teamId`: Stable NHL identifier used across NHL APIs.  
  - `triCode`: Three-letter abbreviation (e.g., `NYR`).  
  - `fullName` / `commonName` / `placeName`: Display labels.  
  - `divisionId`: Numeric key for the NHL division. Mapping: `15`→Pacific, `16`→Central, `17`→Atlantic, `18`→Metropolitan.  
  - `conferenceId`: Not directly provided by the upstream feed; derived from division (`15`/`16`→Western, `17`/`18`→Eastern).  
  - `firstSeasonId`: ISO date representing the franchise's inaugural season.  
  - `officialSiteUrl`: Canonical marketing URL (not required for modelling, retained for completeness).
- **Game**  
  - Defined by `gamePk` (NHL schedule identifier).  
  - Attributes: date/time, home/away team IDs, scores, venue, game type (regular season, playoffs), season.
- **Team-Season Snapshot**  
  - Aggregated metrics per team per season (e.g., goal differential, power-play %, save %, shot share).  
  - Derived from NHL Stats REST endpoints (e.g., `https://api.nhle.com/stats/rest/en/team/summary`).
- **Skater/Goalie Game Logs (optional extensions)**  
  - Detailed player-level performance used for advanced features such as starting goalie strength or roster injuries.

## 2. Relationships
- `Team` ⟷ `Game`: Many-to-many through `homeTeamId` and `awayTeamId`.
- `Game` ↦ `Team-Season Snapshot`: Join on `teamId` + season to attach team form metrics.
- `Game` ↦ `Rest/Travel`: Computed by comparing each team's prior game date and venue.

## 3. Feature Families
1. **Team Strength (Season-to-Date)**
   - Win %, points %, goal differential per 60.
   - Power-play & penalty-kill percentages.
   - Shot attempt share (Corsi/Fenwick) when available.
2. **Recent Form**
   - Rolling averages over last `N` games (e.g., 5/10) for goals for/against, xG if available.
3. **Situational Factors**
   - Rest days differential.
   - Travel distance and back-to-back indicators.
   - Home/away splits (win %, goals for/against at home vs away).
4. **Special Teams Head-to-Head**
   - Matchup of home PP% vs away PK% and vice versa.
5. **Goaltending**
   - Starting goalie save % (season and recent).  
   - Fatigue indicator based on last start.
6. **Betting/Market (optional)**
   - Moneyline or implied odds when available for calibration.

## 4. Target Definition
- Binary classification: `home_team_wins` (1 if home score > away score, else 0).
- Alternative targets:
  - Regulation win indicator.
  - Puck-line cover (spread).
  - Total goals over/under (requires regression/classification adjustments).

## 5. Data Sources
- **Static**: `data/nhl_teams.csv` generated from `https://records.nhl.com/site/api/team` (filtered to `leagueId=133`, active franchises only).
- **Dynamic**:
  1. Game schedule & results: `https://api-web.nhle.com/v1/gamecenter/{gamePk}/boxscore` or schedule summary endpoints.
  2. Team statistics: `https://api.nhle.com/stats/rest/en/team/summary`, `team/goalSummary`, etc.
  3. Goalie/skater logs: `https://api.nhle.com/stats/rest/en/goalie/game/log`.

## 6. Modelling Workflow Overview
1. **Ingest** team list (this repo) and seasonal game results via NHL REST endpoints.
2. **Engineer** matchup features combining team seasonal strength, recent form, and situational variables.
3. **Split** data into train/validation/test by season or rolling date windows to avoid leakage.
4. **Train** baseline classifiers (e.g., logistic regression, gradient boosted trees).
5. **Calibrate & Evaluate** using accuracy, log loss, Brier score, ROC-AUC. Track calibration curves.
6. **Deploy** predictions for upcoming games once new schedule data is fetched.

## 7. Future Extensions
- Incorporate player-level injuries and lineup projections.
- Use expected goals (xG) feeds for richer possession metrics.
- Implement Elo or Glicko-style rolling ratings as engineered features.
- Add betting market comparison dashboard to monitor edge.
