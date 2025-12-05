# NHL Prediction Model - Usage Guide

This guide explains how to use the prediction pipeline, understand the data flow, and extend the model.

---

## Pipeline Overview

The prediction system follows this flow:

```
MoneyPuck Data (CSV)
    ↓
load_moneypuck_data() - Filter to team-level, regular season
    ↓
fetch_multi_season_logs() - Extract requested seasons
    ↓
engineer_team_features() - Create rolling stats, lagged features
    ↓
build_game_dataframe() - Pair home/away teams into matchups
    ↓
add_elo_features() - Compute pre-game Elo ratings
    ↓
build_dataset() - Create feature matrix + target
    ↓
Model Training & Evaluation
```

---

## Data Source: MoneyPuck

### What is MoneyPuck?

**MoneyPuck** (https://moneypuck.com/) is a leading hockey analytics platform that provides:
- Game-by-game statistics for all NHL teams since 2008
- **Expected Goals (xG)**: Shot quality metrics based on location, type, and game situation
- **Shot danger classifications**: High/medium/low danger shot breakdowns
- **Corsi & Fenwick**: Possession metrics (all shot attempts)
- **Score-adjusted statistics**: Context-aware metrics that account for score effects

This data is **professionally maintained** and used by NHL analysts, media, and researchers.

### Data File Location

**`data/moneypuck_all_games.csv`** (115MB)
- Contains ~220,000 team-game records from 2008-2024
- One row per team per game
- Updated periodically by MoneyPuck

### Updating MoneyPuck Data

To get the latest data:

```bash
cd data
curl -O "https://moneypuck.com/moneypuck/playerData/careers/gameByGame/all_teams.csv"
mv all_teams.csv moneypuck_all_games.csv
```

For current season predictions, re-download monthly or weekly.

---

## Using the Pipeline

### 1. Load and Prepare Data

```python
from nhl_prediction.pipeline import build_dataset

# Specify seasons to include
seasons = ['20212022', '20222023', '20232024']
dataset = build_dataset(seasons)

# Inspect
print(f"Games: {len(dataset.games)}")
print(f"Features: {dataset.features.shape}")
print(f"Target: {dataset.target.sum()} home wins of {len(dataset.target)} games")
```

**Season ID Format:** Use 8-digit format like `20232024` for the 2023-24 season.

### 2. Access Components

```python
# Full game dataframe (includes all columns)
games_df = dataset.games

# Feature matrix (engineered features only)
X = dataset.features

# Target variable (1 = home win, 0 = away win)
y = dataset.target
```

### 3. Train Models

**Command-line:**
```bash
python -m nhl_prediction.train \
    --train-seasons 20212022 \
    --train-seasons 20222023 \
    --test-season 20232024
```

**Python code:**
```python
from nhl_prediction.train import compare_models

comparison = compare_models(dataset, 
                           train_ids=['20212022', '20222023'],
                           test_id='20232024')

best_model = comparison['best_result']['model']
test_metrics = comparison['best_result']['test_metrics']

print(f"Best model: {comparison['best_result']['name']}")
print(f"Test accuracy: {test_metrics['accuracy']:.3f}")
print(f"Test ROC-AUC: {test_metrics['roc_auc']:.3f}")
```

### 4. Make Predictions

```python
from nhl_prediction.model import predict_probabilities

# Get probabilities for test games
test_mask = dataset.games['seasonId'] == '20232024'
probs = predict_probabilities(best_model, dataset.features, test_mask)

# probs = array of home win probabilities
print(f"Sample predictions: {probs[:5]}")
```

### 5. Launch Dashboard

```bash
streamlit run streamlit_app.py
```

Dashboard allows:
- Interactive season selection
- Model comparison
- Game-level prediction exploration
- Feature importance visualization
- CSV export

---

## Data Flow Details

### Step 1: Load MoneyPuck CSV

**File:** `src/nhl_prediction/data_ingest.py`

```python
def load_moneypuck_data():
    df = pd.read_csv('data/moneypuck_all_games.csv')
    
    # Filter to:
    # - Team Level (not player stats)
    # - "all" situation (full game, not just 5v5)
    # - Regular season only (playoffGame == 0)
    df = df[
        (df['position'] == 'Team Level') & 
        (df['situation'] == 'all') &
        (df['playoffGame'] == 0)
    ]
    return df
```

### Step 2: Standardize Columns

Maps MoneyPuck column names to expected format:

| MoneyPuck Column | Our Column | Description |
|------------------|------------|-------------|
| `playerTeam` | `teamAbbrev` | Team abbreviation (e.g., "NYR") |
| `opposingTeam` | `opponentTeamAbbrev` | Opponent abbreviation |
| `home_or_away` | `homeRoad` | "H" or "A" |
| `goalsFor` | `goalsFor` | Goals scored |
| `xGoalsFor` | `xGoalsFor` | Expected goals (shot quality) |
| `corsiPercentage` | `corsiPercentage` | Shot attempt % |
| `highDangerShotsFor` | `highDangerShotsFor` | High-danger shots |

### Step 3: Engineer Features

**File:** `src/nhl_prediction/features.py`

Creates lagged, rolling, and derived features:

```python
def engineer_team_features(logs):
    # Sort chronologically
    logs = logs.sort_values(['teamId', 'seasonId', 'gameDate'])
    
    # Group by team-season
    group = logs.groupby(['teamId', 'seasonId'])
    
    # Lagged cumulative stats
    logs['season_win_pct'] = group['win'].cumsum().shift(1) / group.cumcount()
    
    # Rolling windows (3, 5, 10 games)
    for window in [3, 5, 10]:
        logs[f'rolling_win_pct_{window}'] = group['win'].transform(
            lambda s: s.shift(1).rolling(window).mean()
        )
    
    return logs
```

**Key principle:** `.shift(1)` ensures no data leakage - we only use games *before* the current one.

### Step 4: Build Game Matchups

Converts two rows (home team, away team) into one row per game:

```python
def build_game_dataframe(logs):
    home = logs[logs['homeRoad'] == 'H'].rename(columns=lambda c: f"{c}_home")
    away = logs[logs['homeRoad'] == 'A'].rename(columns=lambda c: f"{c}_away")
    
    games = pd.merge(home, away, on=['gameId', 'gameDate', 'seasonId'])
    games['home_win'] = (games['home_score'] > games['away_score']).astype(int)
    
    return games
```

### Step 5: Compute Elo Ratings

**File:** `src/nhl_prediction/pipeline.py`

```python
def _add_elo_features(games):
    # Initialize each team at 1500 per season
    # Update after each game based on outcome and margin
    # Add home ice advantage (+30 Elo)
    
    games['elo_home_pre'] = home_ratings_before_game
    games['elo_away_pre'] = away_ratings_before_game
    games['elo_diff_pre'] = games['elo_home_pre'] - games['elo_away_pre']
    
    return games
```

### Step 6: Create Feature Matrix

Computes differentials and creates categorical variables:

```python
# For each feature, create home - away difference
for base_feature in ['rolling_win_pct_5', 'rolling_goal_diff_5', ...]:
    games[f'{base_feature}_diff'] = games[f'{base_feature}_home'] - games[f'{base_feature}_away']

# One-hot encode teams
games = pd.get_dummies(games, columns=['teamId_home', 'teamId_away'])

# Final feature matrix
X = games[feature_columns]
y = games['home_win']
```

---

## Feature Families

### 1. Team Strength (Cumulative)
- `season_win_pct_diff`: Win % difference
- `points_prior_diff`: NHL standings points difference
- Season-to-date averages for goals, shots, etc.

### 2. Recent Form (Rolling Windows)
- `rolling_win_pct_{3,5,10}_diff`: Recent win rate
- `rolling_goal_diff_{3,5,10}_diff`: Recent goal margin
- `rolling_pp_pct_{3,5,10}_diff`: Power-play efficiency
- `rolling_pk_pct_{3,5,10}_diff`: Penalty-kill efficiency
- `rolling_faceoff_{3,5,10}_diff`: Faceoff win rate

### 3. Momentum
- `momentum_win_pct_diff`: Recent vs season-long win rate
- `momentum_goal_diff_diff`: Recent vs season-long scoring

### 4. Rest & Scheduling
- `rest_days_diff`: Days since last game
- `is_b2b_home`, `is_b2b_away`: Back-to-back game flags
- `games_last_3d_diff`, `games_last_6d_diff`: Schedule congestion

### 5. Elo Ratings
- `elo_diff_pre`: Pre-game Elo difference
- `elo_expectation_home`: Win probability per Elo

### 6. Special Teams Matchups
- `special_teams_matchup`: Home PP% vs Away PK%
- Captures advantage when penalties occur

### 7. Team Identity
- `home_team_X`, `away_team_X`: One-hot encoded team IDs
- Captures roster quality, home ice advantage per team

---

## Extending the Model

### Adding MoneyPuck xGoals Features

MoneyPuck's **expected goals (xG)** can improve predictions:

```python
# In features.py

def engineer_team_features(logs):
    # ... existing code ...
    
    # xGoals differential
    logs['xg_diff'] = logs['xGoalsFor'] - logs['xGoalsAgainst']
    
    # Over/under-performing xG
    logs['goals_vs_xg'] = logs['goalsFor'] - logs['xGoalsFor']
    
    # Rolling xG averages
    for window in [3, 5, 10]:
        logs[f'rolling_xg_{window}'] = group['xGoalsFor'].transform(
            lambda s: s.shift(1).rolling(window).mean()
        )
    
    # Shot quality
    logs['high_danger_pct'] = logs['highDangerShotsFor'] / logs['shotsOnGoalFor']
    
    return logs
```

Then add to feature list in `pipeline.py`.

### Adding New Situations

MoneyPuck has situation-specific data (5v5, power play, etc.):

```python
# Load specific situation
def load_moneypuck_5v5():
    df = pd.read_csv('data/moneypuck_all_games.csv')
    df = df[(df['position'] == 'Team Level') & (df['situation'] == '5on5')]
    return df
```

### Custom Feature Engineering

Add domain knowledge:

```python
# Division rivalry indicator
def add_rivalry_features(games):
    games['same_division'] = (
        games['divisionId_home'] == games['divisionId_away']
    ).astype(int)
    return games
```

---

## Validation Best Practices

### 1. Temporal Splitting
Always use chronological splits:
```python
train_seasons = ['20212022', '20222023']
test_season = '20232024'
```

Never shuffle or randomly split - this leaks future information!

### 2. Feature Lagging
All features must use `.shift(1)` or cumulative operations:
```python
# ✓ Correct
logs['feature'] = group['stat'].shift(1).rolling(5).mean()

# ✗ Wrong - includes current game!
logs['feature'] = group['stat'].rolling(5).mean()
```

### 3. Check for Leakage
Verify no future data:
```python
# For game on 2023-10-15
# Feature should use data through 2023-10-14 only
assert logs.loc[game_idx, 'season_win_pct'] uses only prior games
```

---

## Troubleshooting

### "No games found for season"
- Check season format: must be 8 digits like `20232024`
- Verify MoneyPuck CSV has data for that season
- Check `playoffGame` filter isn't excluding games

### "Team abbreviation not found"
- Some old franchises (e.g., Atlanta Thrashers) moved/renamed
- `data/nhl_teams.csv` only includes current 32 teams
- Older seasons may have missing teams

### "Feature matrix has NaN values"
- Early-season games lack rolling window history
- Solution: `.fillna(0)` applied in pipeline
- Expected behavior - model learns from available data

### "Elo rating errors"
- Ensure `teamId` is numeric
- Check team ID mapping in `data_ingest.py`
- Verify home/away game pairing is correct

---

## Performance Tips

### Caching
MoneyPuck CSV is large (115MB). Cache processed data:

```python
import pickle

# After engineering features
with open('cache/engineered_logs.pkl', 'wb') as f:
    pickle.dump(logs, f)

# Load cached
with open('cache/engineered_logs.pkl', 'rb') as f:
    logs = pickle.load(f)
```

### Subset Seasons for Testing
During development, use fewer seasons:

```python
dataset = build_dataset(['20232024'])  # Just one season for quick testing
```

### Streamlit Caching
Dashboard uses `@st.cache_data` to avoid recomputing.

---

## Next Steps

1. **Explore MoneyPuck xGoals**: Add expected goals features
2. **Betting Integration**: Compare model vs betting odds (see `docs/betting_integration_plan.md`)
3. **Live Predictions**: Update data weekly for current season
4. **Model Improvements**: Try neural networks, ensembles, or deep learning

---

**Questions?** See `docs/taxonomy.md` for data schema details or `README.md` for general overview.
