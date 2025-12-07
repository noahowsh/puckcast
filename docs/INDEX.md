# 📚 Puckcast Documentation Index

> **Last Updated**: December 7, 2025
> **Production Model**: V7.0 (60.9% accuracy - 4-season holdout)

---

## 🎯 Quick Start

**New to the project?** Start here:
1. **[../README.md](../README.md)** - Project overview and quick start
2. **[vFutures.md](vFutures.md)** - Roadmap and future features
3. **[MODEL_COMPARISON_V7.md](MODEL_COMPARISON_V7.md)** - Model evolution history

---

## 📊 Current Model: V7.0

### Key Metrics (4-Season Holdout Validation)
| Metric | Value |
|--------|-------|
| **Test Accuracy** | 60.9% |
| **Games Tested** | 5,002 |
| **Baseline (Home Win Rate)** | 53.9% |
| **Edge vs Baseline** | +6.9 pts |
| **Brier Score** | 0.2317 |
| **Log Loss** | 0.6554 |
| **Features** | 39 + adaptive weights |

### Accuracy by Confidence Grade
| Grade | Edge | Accuracy | Games | Coverage |
|-------|------|----------|-------|----------|
| A+ | ≥25 pts | 79.3% | 333 | 6.7% |
| A | 20-25 pts | 72.0% | 404 | 8.1% |
| B+ | 15-20 pts | 67.3% | 687 | 13.7% |
| B | 10-15 pts | 62.0% | 975 | 19.5% |
| C+ | 5-10 pts | 57.8% | 1,231 | 24.6% |
| C | 0-5 pts | 51.9% | 1,372 | 27.4% |

### Season Breakdown (Holdout)
| Season | Games | Accuracy | Log Loss | Baseline |
|--------|-------|----------|----------|----------|
| 2024-25 | 1,312 | 59.7% | 0.659 | 56.3% |
| 2023-24 | 1,230 | 60.4% | 0.659 | 53.7% |
| 2022-23 | 1,230 | 60.9% | 0.653 | 51.4% |
| 2021-22 | 1,230 | 62.5% | 0.651 | 54.2% |

### Current Season (2025-26) - Early
- Games: 440
- Accuracy: 54.3% (early season, improves ~7pp by spring)
- A-Grade Accuracy: 65% (60 games)

---

## 🎨 Recent Visual Updates (Dec 2025)

### H2H Matchup Pages (`/matchup/[gameId]`)
- **NEW**: Click any prediction card to view detailed matchup
- Team comparison with colored stat bars (Points, Point%, Goal Diff, Goals/Game, Goals Against, Power Score, **PP%**, **PK%**)
- Win probability display with team colors
- Model pick banner with grade, edge, confidence
- Projected goalies section
- Links to team pages

### Team Pages (`/teams/[abbrev]`)
- Circular team crests in hero section
- Power rank ring visualization
- Season record bar (W/L/OT)
- Point percentage and goal differential stats
- **NEW**: Special Teams section with PP% and PK% ranks
- Next opponent card with prediction

### Predictions Page (`/predictions`)
- Clickable prediction cards → matchup pages
- "View matchup details" CTA on hover
- Sorted by edge (strongest picks first)

### Color System Improvements
- Team-colored comparison bars
- Automatic contrast detection for similar team colors
- Dark color visibility fix (LAK, SEA, EDM, etc.)
- Medium-dark color lightening (MTL, MIN, COL, etc.)

---

## 🔧 Infrastructure

### GitHub Actions Workflows
| Workflow | Schedule | Purpose |
|----------|----------|---------|
| `scheduled-data-refresh.yml` | 4 AM UTC | Update standings, predictions, goalies |
| `fetch-results.yml` | 8 AM UTC | Fetch game results, generate backtesting |
| `twitter-daily.yml` | 2 PM UTC | Post daily predictions |
| `twitter-weekly-posts.yml` | Mondays | Post weekly recap |
| `model-retraining.yml` | Manual | Retrain model with new data |
| `data-validation.yml` | On push | Validate data integrity |
| `monitoring-alerts.yml` | Every 30 min | Alert on failures |

### Data Files
| File | Updated | Description |
|------|---------|-------------|
| `currentStandings.json` | Daily | All 32 teams with stats (incl. PP%, PK%) |
| `todaysPredictions.json` | Daily | Today's game predictions |
| `modelInsights.json` | Static | Model performance metrics |
| `goaliePulse.json` | Daily | Starting goalie info |
| `powerIndexSnapshot.json` | Daily | Power rankings |

---

## 📁 Documentation Structure

```
docs/
├── INDEX.md                      # ← You are here
├── vFutures.md                   # Roadmap & future features
├── MODEL_COMPARISON_V7.md        # Model version history
├── current/                      # Current model docs
├── experiments/                  # Experiment results
└── archive/                      # Historical docs
```

---

## 📈 Version History

| Version | Accuracy | Date | Status | Notes |
|---------|----------|------|--------|-------|
| **V7.0** | **60.9%** | **Dec 2025** | ✅ **PRODUCTION** | **39 features + adaptive weights** |
| V6.4 | ~59% | Nov 2025 | Superseded | Previous production |
| V6.x | 58-60% | Oct-Nov 2025 | Archived | Various experiments |

### V7.0 Development Tests
The V7.0 release represents the culmination of extensive experimentation:

| Test | Accuracy | Result | Notes |
|------|----------|--------|-------|
| Baseline features | 60.24% | ✅ Included | Initial 209-feature set |
| Situational features | 60.49% | ✅ Included | Fatigue, travel, divisional |
| Head-to-head | 60.00% | ❌ Rejected | Multicollinearity issues |
| Feature interactions | 60.08% | ❌ Rejected | Overfitting |
| Team calibration | 60.73% | ❌ Rejected | Weak signal |
| Adaptive weights | 60.9% | ✅ Production | Handles evolving patterns |

---

**Last Updated**: Dec 7, 2025
