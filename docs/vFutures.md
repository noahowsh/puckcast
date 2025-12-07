# vFutures.md

> **Last Updated**: December 7, 2025

## Recently Completed (Dec 2025)
- ✅ **H2H Matchup Pages** (`/matchup/[gameId]`) - Team comparison with colored stat bars, model pick banner, projected goalies
- ✅ **PP/PK Stats** - Power Play % and Penalty Kill % on team pages and H2H matchup comparison
- ✅ **Team Hub Pages** - Individual team pages with stats, special teams, next opponent
- ✅ **Color Contrast System** - Automatic lightening for dark team colors (LAK, SEA, etc.)
- ✅ **Circular Team Crests** - Consistent circular logos across matchup and team pages

---

## v7.1 Candidates (short-cycle additions)
- Goalie Page (starters + rest + basic GSAx)
- Past Slate Archive (recent days)
- Trend expansions for Power Index
- Additional small UX elements
- **Per-Team Model Win Rate** (see implementation plan below)

---

## Per-Team Model Win Rate Implementation Plan

### Overview
Display actual model accuracy per team on the Power Rankings page. Shows how often the model correctly predicted games involving each team this season.

### Prerequisites
1. **Daily prediction archiving** - Archive predictions before games start
2. **Results fetching** - Fetch actual outcomes after games complete
3. **Data aggregation** - Calculate per-team accuracy from results

### Implementation Steps

#### Step 1: Enable Prediction Archiving
The `scripts/archive_predictions.py` script already exists. Set up GitHub Action to run daily:

```yaml
# .github/workflows/archive-predictions.yml
name: Archive Daily Predictions
on:
  schedule:
    - cron: '0 16 * * *'  # 4 PM UTC (before most games)
jobs:
  archive:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python scripts/archive_predictions.py
      - uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: archive daily predictions"
```

#### Step 2: Enable Results Fetching
The `scripts/fetch_results.py` script already exists. Set up GitHub Action:

```yaml
# .github/workflows/fetch-results.yml
name: Fetch Game Results
on:
  schedule:
    - cron: '0 8 * * *'  # 8 AM UTC (after games complete)
jobs:
  fetch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python scripts/fetch_results.py --days-back 7
      - uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: fetch game results"
```

#### Step 3: Generate Per-Team Stats
The `fetch_results.py` already calculates `team_performance` in `generate_backtesting_report()`:

```python
team_performance = [
    {
        "team": team,
        "games": stats["games"],
        "correct": stats["correct"],
        "accuracy": stats["correct"] / stats["games"],
    }
    for team, stats in team_stats.items()
    if stats["games"] >= 3  # Min 3 games
]
```

This outputs to `web/src/data/backtestingReport.json` with a `teamPerformance` array.

#### Step 4: Display in Power Rankings
Once data is populated, update `PowerBoardClient.tsx`:

```tsx
// Add to LeaderboardRow type
modelWinRate?: number;  // From backtestingReport.teamPerformance

// In renderRow()
const winRate = row.modelWinRate ? `${(row.modelWinRate * 100).toFixed(0)}%` : "—";
```

### Data Flow
```
Daily 4 PM UTC: archive_predictions.py → data/archive/predictions/predictions_YYYY-MM-DD.json
Daily 8 AM UTC: fetch_results.py → Updates predictions with actualWinner, generates backtestingReport.json
Power Rankings: Reads teamPerformance from backtestingReport.json
```

### Minimum Data Requirements
- Need ~3+ games per team for meaningful accuracy
- Full data available after ~2 weeks of tracking
- Early season: show "Tracking..." until sufficient data

### Quick Start (Add to existing workflow)
Add this step to `scheduled-data-refresh.yml` after predictions are generated:

```yaml
- name: Archive predictions
  if: steps.check.outputs.predictions == 'true'
  run: python scripts/archive_predictions.py
```

The `fetch-results.yml` workflow already exists and runs daily at 8 AM UTC.

---

## v8 Core
- ~~Matchup Page (deep dive intelligence)~~ ✅ DONE (Dec 2025) - H2H comparison with team-colored stat bars
- Explainability chips
- ~~Team hub pages~~ ✅ DONE - Individual team pages with stats, PP/PK, next game
- ~~PP/PK dashboards~~ ✅ DONE (Dec 2025) - Added to team pages and H2H matchup comparison
- Rink effects system
- Ensemble exploration
- Better forms of injury modeling
- Travel model improvements
- Calibration by matchup category
- Market comparison (tentative)

## Long-Term Research & Vision (v9+)
- Player projection system
- Player props simulator
- Series win model
- Shot-quality neural components
- On-ice matchup adjustments
- Special teams sequence modeling
- Full event-level model refresh
- Real-time in-game updates (if ever)
