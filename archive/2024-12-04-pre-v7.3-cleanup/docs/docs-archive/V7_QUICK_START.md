# 🎯 V7.0 Quick Start Guide

## Goal: 62%+ Accuracy, ≤0.670 Log-Loss

Current: 59.92% accuracy, 0.6761 log-loss
Target: 62.0%+ accuracy, 0.670 log-loss
Gap to Close: +2.08% accuracy, -0.0061 log-loss

---

## 🔥 THIS WEEK: Individual Goalie Tracking

**Expected Impact:** +0.8-1.2% accuracy (single biggest improvement)
**Effort:** 2-3 days
**Priority:** CRITICAL

### Why This First?
- Currently missing #5 most important feature
- Goaltending accounts for 30-40% of game outcomes
- We already have starter data (`data/feeds/starters.json`)
- Clear path to implementation with NHL API

### Step 1: Build Goalie Stats Database (Day 1)

**Create:** `src/nhl_prediction/goalie_tracker.py`

```python
"""
Track individual goalie performance from NHL API.
"""

Key functions needed:
- fetch_goalie_stats(goalie_id, season) -> stats dict
- get_goalie_recent_form(goalie_id, last_n_games) -> avg stats
- get_goalie_vs_opponent(goalie_id, opponent_team) -> historical stats
- compute_goalie_gsa(shots_data, saves) -> Goals Saved Above Expected

Stats to track:
- saves, shots_against, save_pct
- high_danger_saves, high_danger_save_pct
- rush_saves, rush_save_pct
- goals_saved_above_expected (GSA)
- games_started, total_ice_time
- vs_opponent_stats (save % against specific teams)
```

**Data Structure:**
```python
{
  "goalie_id": 8471679,  # from NHL API
  "goalie_name": "Andrei Vasilevskiy",
  "season": "20232024",
  "games": [
    {
      "game_id": "2023020001",
      "date": "2023-10-10",
      "opponent": "BUF",
      "saves": 32,
      "shots_against": 35,
      "save_pct": 0.914,
      "high_danger_saves": 8,
      "high_danger_shots": 10,
      "hd_save_pct": 0.800,
      "gsa": 1.2,
      "toi_seconds": 3600
    },
    ...
  ],
  "season_totals": {...},
  "recent_5_avg": {...},
  "recent_10_avg": {...}
}
```

### Step 2: Integrate with Starting Goalies (Day 1-2)

**Modify:** `src/nhl_prediction/goalie_features.py`

Current (team-level):
```python
def enhance_with_goalie_features(team_logs: pd.DataFrame) -> pd.DataFrame:
    """Pass-through - team metrics already in native_ingest"""
    return team_logs
```

New (individual-level):
```python
def enhance_with_goalie_features(
    team_logs: pd.DataFrame,
    starting_goalies: dict  # from starters.json
) -> pd.DataFrame:
    """
    Add individual starting goalie features for each game.
    """
    for idx, row in team_logs.iterrows():
        game_date = row['gameDate']
        home_team = row['teamAbbrev_home']
        away_team = row['teamAbbrev_away']

        # Get starting goalies
        home_goalie_id = starting_goalies.get(game_date, {}).get(home_team)
        away_goalie_id = starting_goalies.get(game_date, {}).get(away_team)

        # Get goalie stats (last 5 games)
        home_goalie_stats = get_goalie_recent_form(home_goalie_id, last_n=5)
        away_goalie_stats = get_goalie_recent_form(away_goalie_id, last_n=5)

        # Add features
        team_logs.at[idx, 'goalie_save_pct_last5_home'] = home_goalie_stats['save_pct']
        team_logs.at[idx, 'goalie_gsa_last5_home'] = home_goalie_stats['gsa_avg']
        team_logs.at[idx, 'goalie_hd_save_pct_last5_home'] = home_goalie_stats['hd_save_pct']

        team_logs.at[idx, 'goalie_save_pct_last5_away'] = away_goalie_stats['save_pct']
        team_logs.at[idx, 'goalie_gsa_last5_away'] = away_goalie_stats['gsa_avg']
        team_logs.at[idx, 'goalie_hd_save_pct_last5_away'] = away_goalie_stats['hd_save_pct']

        # Goalie vs opponent
        home_vs_away = get_goalie_vs_opponent(home_goalie_id, away_team)
        away_vs_home = get_goalie_vs_opponent(away_goalie_id, home_team)

        team_logs.at[idx, 'goalie_vs_opp_save_pct_home'] = home_vs_away['save_pct']
        team_logs.at[idx, 'goalie_vs_opp_save_pct_away'] = away_vs_home['save_pct']

    # Add differential features
    team_logs['goalie_gsa_diff'] = (
        team_logs['goalie_gsa_last5_home'] - team_logs['goalie_gsa_last5_away']
    )
    team_logs['goalie_quality_diff'] = (
        team_logs['goalie_save_pct_last5_home'] - team_logs['goalie_save_pct_last5_away']
    )

    return team_logs
```

### Step 3: Update Pipeline (Day 2)

**Modify:** `src/nhl_prediction/data_ingest.py`

```python
def fetch_multi_season_logs(seasons: Iterable[str]) -> pd.DataFrame:
    """Fetch and enhance game logs with individual goalie stats."""
    native = load_native_game_logs(list(seasons))

    # Load starting goalie data
    starting_goalies = load_starting_goalies()  # from starters.json

    # Enhance with individual goalie features (NEW!)
    native = enhance_with_goalie_features(native, starting_goalies)

    return native
```

### Step 4: Test Impact (Day 3)

Run evaluation to measure improvement:

```bash
# Retrain with goalie features
python train_optimal.py

# Evaluate
python evaluate_model_comprehensive.py

# Check improvement
# Expected: 60.7-61.1% accuracy (+0.8-1.2% from goalie features)
```

Compare results:
```
V6.3 Baseline:       59.92% accuracy
V7.0 (+ goalies):    60.8-61.1% (expected)
Improvement:         +0.9-1.2%
```

---

## 🎯 WEEK 2: Feature Pruning

**Expected Impact:** +0.3-0.5% accuracy
**Effort:** 1-2 days
**Priority:** HIGH

### Step 1: Generate Feature Importance

```bash
python -c "
import sys
sys.path.insert(0, 'src')
from nhl_prediction.pipeline import build_dataset
from nhl_prediction.model import create_baseline_model, fit_model
import pandas as pd
import pickle

# Load data
dataset = build_dataset(['20212022', '20222023', '20232024'])
train_mask = dataset.games['seasonId'].isin(['20212022', '20222023'])

X_train = dataset.features.loc[train_mask].fillna(0)
y_train = dataset.target.loc[train_mask]

# Train model
model = create_baseline_model(C=1.0)
mask = pd.Series(True, index=X_train.index)
model.fit(X_train, y_train)

# Get coefficients
coefs = model.named_steps['clf'].coef_[0]
feature_importance = pd.DataFrame({
    'feature': X_train.columns,
    'coefficient': coefs,
    'abs_importance': abs(coefs)
}).sort_values('abs_importance', ascending=False)

feature_importance.to_csv('reports/v7_feature_importance.csv', index=False)
print('✓ Feature importance saved')
"
```

### Step 2: Identify Features to Remove

Look at bottom 20% of features (abs_importance < threshold):
- Line combination features with zero weight
- Rarely-used team embeddings
- Redundant rolling windows
- Low-signal special teams metrics

### Step 3: Create Pruned Feature List

**Create:** `src/nhl_prediction/v7_features.py`

```python
"""
V7.0 optimized feature list - pruned low-importance features.
"""

# Features to KEEP (high importance)
V7_FEATURE_WHITELIST = [
    # Goal differential metrics (TOP importance)
    'season_goal_diff_avg_diff',
    'rolling_goal_diff_10_diff',
    'rolling_goal_diff_5_diff',
    'rolling_goal_diff_3_diff',

    # High-danger shots (proven valuable)
    'rolling_high_danger_shots_5_diff',
    'rolling_high_danger_shots_3_diff',
    'rolling_high_danger_shots_10_diff',

    # xG metrics (custom model advantage)
    'rolling_xg_for_5_diff',
    'rolling_xg_against_5_diff',
    'rolling_xg_for_3_diff',
    'rolling_xg_against_3_diff',

    # Schedule factors (strong signal)
    'is_b2b_home',
    'is_b2b_away',
    'rest_days_home',
    'rest_days_away',
    'rest_diff',

    # Shot metrics
    'shotsFor_roll_3_diff',
    'shotsFor_roll_5_diff',
    'shotsAgainst_roll_10_diff',

    # Individual goalie features (NEW in V7.0)
    'goalie_gsa_last5_home',
    'goalie_gsa_last5_away',
    'goalie_gsa_diff',
    'goalie_save_pct_last5_home',
    'goalie_save_pct_last5_away',
    'goalie_quality_diff',

    # Add more high-importance features...
]

# Features to REMOVE (low/zero importance)
V7_FEATURE_BLACKLIST = [
    # Add low-importance features from analysis
]
```

### Step 4: Retrain and Compare

```bash
# Train with pruned features
python train_optimal.py --features v7_pruned

# Compare
# V6.3: 204 features, 59.92% accuracy
# V7.0: ~170 features, 61.5%+ accuracy (expected)
```

---

## 🎯 WEEK 3: Enhanced Rolling Windows

**Expected Impact:** +0.2-0.3% accuracy
**Effort:** 2-3 days
**Priority:** MEDIUM-HIGH

### Momentum-Weighted Rolling

**Create:** `src/nhl_prediction/momentum_features.py`

```python
"""
Momentum-weighted rolling window features.
Weights recent games more heavily to capture hot/cold streaks.
"""

def compute_momentum_weighted_avg(values: list, weights=None):
    """
    Compute weighted average with recent games weighted more.
    Default weights: [0.4, 0.3, 0.2, 0.1] for last 4 games
    """
    if weights is None:
        weights = [0.4, 0.3, 0.2, 0.1]

    if len(values) < len(weights):
        # Pad with zeros if not enough history
        values = [0] * (len(weights) - len(values)) + values

    return sum(v * w for v, w in zip(values[-len(weights):], weights))

def add_momentum_features(games_df: pd.DataFrame) -> pd.DataFrame:
    """Add momentum-weighted rolling features."""

    # For each team
    for team in games_df['team'].unique():
        team_games = games_df[games_df['team'] == team].sort_values('gameDate')

        # Momentum xG
        xg_values = team_games['xGoalsFor'].tolist()
        momentum_xg = [
            compute_momentum_weighted_avg(xg_values[:i+1][-4:])
            for i in range(len(xg_values))
        ]
        games_df.loc[team_games.index, 'momentum_xg_4'] = momentum_xg

        # Momentum goal differential
        gd_values = team_games['goalDifferential'].tolist()
        momentum_gd = [
            compute_momentum_weighted_avg(gd_values[:i+1][-4:])
            for i in range(len(gd_values))
        ]
        games_df.loc[team_games.index, 'momentum_gd_4'] = momentum_gd

    return games_df
```

Add to pipeline:
- `momentum_xg_4_diff` (home - away)
- `momentum_goal_diff_4_diff`
- `momentum_high_danger_4_diff`

---

## 📊 Expected V7.0 Timeline

```
Week 1: Individual Goalie Tracking
  Days 1-2: Build goalie database + integration
  Day 3: Test and validate (+0.8-1.2% expected)
  Result: ~60.8-61.1% accuracy

Week 2: Feature Pruning
  Days 1-2: Analyze, prune, retrain
  Result: ~61.1-61.6% accuracy

Week 3: Rolling Window Enhancements
  Days 1-2: Momentum weighting implementation
  Day 3: Test and optimize
  Result: ~61.3-61.9% accuracy

Week 4: Calibration + xG Improvements
  Days 1-2: Temperature scaling, beta calibration
  Days 3-4: Enhanced xG with traffic/screening
  Result: ~61.6-62.2% accuracy, 0.670 log-loss

Week 5: Integration + Testing
  Days 1-2: Injury features, special teams
  Days 3-5: Full evaluation and refinement
  Result: 62.0-62.5% accuracy, 0.665-0.670 log-loss

Week 6: Deployment
  Days 1-2: Documentation, final validation
  Days 3-5: Deploy V7.0, monitor performance
```

---

## 🚀 Quick Commands to Get Started

### 1. Generate current feature importance
```bash
python analysis/feature_importance_analysis.py > reports/v7_baseline_importance.txt
```

### 2. Create goalie tracker stub
```bash
touch src/nhl_prediction/goalie_tracker.py
```

### 3. Test current goalie data availability
```bash
python -c "
import json
with open('data/feeds/starters.json') as f:
    starters = json.load(f)
print(f'Starter data available: {len(starters)} entries')
"
```

### 4. Check NHL API for goalie stats
```bash
python -c "
from src.nhl_prediction.nhl_api import NHLApi
api = NHLApi()
# Test fetching goalie game log
goalie_id = 8471679  # Vasilevskiy
print('Testing goalie data fetch...')
# Implement goalie stats endpoint
"
```

---

## ✅ Success Checkpoints

**After Week 1 (Goalie Features):**
- [ ] Goalie database built with 3 seasons of data
- [ ] Individual goalie features integrated
- [ ] Test accuracy: 60.7-61.1%
- [ ] Features added: ~10 goalie metrics

**After Week 2 (Pruning):**
- [ ] Feature importance analyzed
- [ ] Low-importance features removed
- [ ] Test accuracy: 61.1-61.6%
- [ ] Features reduced to ~170

**After Week 3 (Rolling Windows):**
- [ ] Momentum weighting implemented
- [ ] Test accuracy: 61.3-61.9%
- [ ] Features: ~185 total

**After Week 4 (Calibration):**
- [ ] Temperature scaling active
- [ ] Log loss: ≤0.670
- [ ] Test accuracy: 61.6-62.2%

**V7.0 Release Criteria:**
- [ ] Test accuracy ≥62.0%
- [ ] Log loss ≤0.670
- [ ] ROC-AUC ≥0.650
- [ ] A+ predictions ≥70%
- [ ] All features documented
- [ ] Comprehensive evaluation report

---

**Let's build V7.0! Start with goalie tracking this week.** 🏒🚀
