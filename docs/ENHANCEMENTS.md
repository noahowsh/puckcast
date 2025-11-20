# Puckcast Enhancements

This document covers all the advanced features and enhancements added to the Puckcast automation system.

## Overview

These enhancements build on the core data pipeline and GitHub Actions automation to provide:

1. **Data Validation** - Ensure data integrity before deployment
2. **Historical Archiving** - Track predictions over time
3. **Monitoring & Alerts** - Get notified of issues
4. **API Endpoints** - Dynamic data access (already existed!)
5. **Calibration Tracking** - Validate confidence grades
6. **A/B Testing** - Optimize Twitter content
7. **Granular Scheduling** - Smart refresh timing

---

## 1. Data Validation

**Files:**
- `.github/workflows/data-validation.yml`
- `scripts/validate_data_schemas.py`

**What it does:**
- Validates JSON syntax before deployment
- Checks schema compliance for all data files
- Verifies probability calculations (sum to 1.0)
- Ensures confidence grades match edge values
- Alerts on stale data (>48 hours old)

**Usage:**
```bash
# Manual validation
python scripts/validate_data_schemas.py

# Runs automatically on:
# - Pull requests touching JSON files
# - Pushes to main branch
```

**Benefits:**
- Catches errors before they reach production
- Ensures data quality
- Prevents broken deployments

---

## 2. Historical Data Archiving

**Files:**
- `scripts/archive_predictions.py`
- `data/archive/predictions/` (generated)
- `data/archive/performance_tracker.csv` (generated)

**What it does:**
- Saves each day's predictions to dated archive files
- Tracks key metrics over time (games, confidence, edge)
- Generates rolling performance summaries
- Enables long-term trend analysis

**Usage:**
```bash
# Archive today's predictions
python scripts/archive_predictions.py

# Archive specific date
python scripts/archive_predictions.py --date 2025-11-20

# Runs automatically in daily predictions workflow
```

**Output files:**
```
data/archive/
├── predictions/
│   ├── predictions_2025-11-20.json
│   ├── predictions_2025-11-21.json
│   └── ...
└── performance_tracker.csv
```

**Benefits:**
- Track model evolution over time
- Analyze seasonal patterns
- Build historical performance reports

---

## 3. Monitoring & Alerts

**Files:**
- `.github/workflows/monitoring-alerts.yml`

**What it does:**
- Monitors workflow health
- Checks data freshness
- Detects performance anomalies
- Sends notifications to multiple channels

**Alerting channels:**
- **Slack** - Team notifications
- **Discord** - Community alerts
- **GitHub Issues** - Automatic bug reports

**Triggers:**
- After every daily predictions workflow
- Every 6 hours (health check)
- Manual dispatch

**Alert conditions:**
- Workflow failures
- Stale data (>26 hours old)
- Unusual confidence distribution
- Extreme probabilities (>90% or <10%)

**Setup:**

Add these secrets to GitHub:
```bash
SLACK_WEBHOOK_URL     # Get from Slack workspace
DISCORD_WEBHOOK_URL   # Get from Discord server settings
```

**Benefits:**
- Immediate notification of issues
- Proactive problem detection
- Centralized monitoring

---

## 4. API Endpoints

**Files:** (Already existed in the codebase!)
- `web/src/app/api/predictions/route.ts`
- `web/src/app/api/insights/route.ts`
- `web/src/app/api/standings/route.ts`
- `web/src/app/api/goalies/route.ts`

**Endpoints:**

### GET /api/predictions
Returns today's game predictions

Query params:
- `confidence`: Filter by grade (A, B, C)
- `team`: Filter by team abbreviation

Example:
```bash
# All predictions
curl https://your-site.com/api/predictions

# Only A-grade picks
curl https://your-site.com/api/predictions?confidence=A

# Specific team
curl https://your-site.com/api/predictions?team=TOR
```

### GET /api/insights
Returns model performance analytics

Query params:
- `metric`: Specific metric (overall, strategies, etc.)

### GET /api/standings
Returns NHL standings

Query params:
- `limit`: Limit number of teams

### GET /api/goalies
Returns goalie performance trends

Query params:
- `team`: Filter by team
- `trend`: Filter by trend (surging, steady, etc.)
- `minLikelihood`: Minimum start probability

**Benefits:**
- Enable third-party integrations
- Mobile app support
- Discord bots, Slack bots, etc.
- Custom dashboards

---

## 5. Confidence Calibration Tracking

**Files:**
- `scripts/track_calibration.py`
- `data/archive/calibration_tracker.csv` (generated)
- `web/src/data/calibrationReport.json` (generated)

**What it does:**
- Compares predicted confidence vs actual outcomes
- Validates that A-grade picks win more than B-grade picks
- Measures calibration error per grade
- Generates reports for web frontend

**Calibration metrics:**
- **Accuracy** - Win rate for each grade
- **Avg Probability** - Mean predicted probability
- **Calibration Error** - |Accuracy - AvgProbability|

**Ideal calibration:**
- A+ picks: ~75% win rate, ~75% avg probability
- B picks: ~60% win rate, ~60% avg probability
- C picks: ~50% win rate, ~50% avg probability

**Usage:**
```bash
# Analyze last 30 days
python scripts/track_calibration.py

# Analyze last 60 days
python scripts/track_calibration.py --days 60
```

**Output:**
```
Grade     Games    Correct  Accuracy   Avg Prob   Error
A+        45       34       75.6%      74.2%      0.014
A         78       56       71.8%      69.5%      0.023
B+        120      75       62.5%      61.8%      0.007
...
```

**Benefits:**
- Validates model confidence
- Identifies overconfidence/underconfidence
- Improves trust in predictions

---

## 6. A/B Testing for Twitter

**Files:**
- `scripts/twitter_ab_testing.py`
- `config/twitter_variants.json` (generated)
- `data/archive/twitter_ab_tests.csv` (generated)

**What it does:**
- Tests different post formats
- Randomly selects variants for A/B testing
- Tracks engagement metrics
- Identifies winning formats

**Post variants:**

**Morning Preview:**
- **Variant A**: Emoji-heavy, excitement-focused
- **Variant B**: Minimal, professional
- **Variant C**: Stats-focused, numbers
- **Variant D**: Question hook, engagement bait

**Afternoon Update:**
- **Variant A**: Excitement, action-focused
- **Variant B**: Value proposition, track record

**Evening Recap:**
- **Variant A**: Tomorrow tease
- **Variant B**: Call to action

**Usage:**
```bash
# Generate random variant
python scripts/twitter_ab_testing.py --post-type morning_preview

# Force specific variant
python scripts/twitter_ab_testing.py --post-type morning_preview --variant B

# View A/B test results
# (automatically shown after each generation)
```

**Metrics tracked:**
- Impressions
- Engagements
- Engagement rate
- Per-variant performance

**Benefits:**
- Optimize content strategy
- Data-driven decisions
- Improve reach and engagement

---

## 7. Granular Scheduling

**Files:**
- `.github/workflows/scheduled-data-refresh.yml`

**What it does:**
- Different refresh frequencies for different data types
- Optimizes resource usage
- Reduces unnecessary API calls

**Refresh schedules:**

| Data Type | Frequency | Times (ET) |
|-----------|-----------|------------|
| Predictions | 4x daily | 6am, 12pm, 6pm, 12am |
| Goalie Pulse | 2x daily | 9am, 7pm |
| Standings | 1x daily | 12am |
| Model Insights | 1x weekly | Monday 10am |

**Why granular?**
- Predictions change frequently (lineups, injuries)
- Standings update once per day
- Model insights rarely change

**Manual triggers:**
```bash
# Refresh specific data type
gh workflow run scheduled-data-refresh.yml -f data_type=predictions
gh workflow run scheduled-data-refresh.yml -f data_type=standings
gh workflow run scheduled-data-refresh.yml -f data_type=all
```

**Benefits:**
- Reduced API usage
- Lower costs
- Faster workflows
- Less git noise

---

## Quick Start

### Enable All Features

1. **Install dependencies:**
```bash
pip install -r requirements.txt
pip install jsonschema  # For validation
```

2. **Configure GitHub Secrets:**
```bash
# Monitoring (optional)
SLACK_WEBHOOK_URL
DISCORD_WEBHOOK_URL

# Deployment (required)
VERCEL_TOKEN
VERCEL_ORG_ID
VERCEL_PROJECT_ID

# Twitter (optional)
TWITTER_API_KEY
TWITTER_API_SECRET
TWITTER_ACCESS_TOKEN
TWITTER_ACCESS_SECRET
```

3. **Enable workflows:**
- Go to GitHub → Actions
- Enable all workflows

4. **Test locally:**
```bash
# Validate data
python scripts/validate_data_schemas.py

# Archive predictions
python scripts/archive_predictions.py

# Track calibration
python scripts/track_calibration.py --days 30

# Test A/B variants
python scripts/twitter_ab_testing.py --post-type morning_preview
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions (Scheduler)                │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Daily      │  │  Granular    │  │  Monitoring  │
│ Predictions  │  │   Refresh    │  │   & Alerts   │
└──────┬───────┘  └───────┬──────┘  └──────┬───────┘
       │                  │                 │
       ▼                  ▼                 ▼
┌──────────────────────────────────────────────────┐
│            Python Data Pipeline                  │
│  • predict_full.py                               │
│  • refresh_site_data.py                          │
│  • archive_predictions.py                        │
│  • track_calibration.py                          │
│  • validate_data_schemas.py                      │
└────────────────┬─────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────┐
│            Data Storage                          │
│  • web/src/data/*.json (site data)               │
│  • data/archive/ (historical data)               │
│  • data/archive/performance_tracker.csv          │
│  • data/archive/calibration_tracker.csv          │
│  • data/archive/twitter_ab_tests.csv             │
└────────────────┬─────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────┐
│            Vercel Deployment                     │
│  • Next.js build                                 │
│  • API routes (/api/predictions, etc.)           │
│  • Static site                                   │
└──────────────────────────────────────────────────┘
```

---

## Performance Metrics

**Estimated execution times:**
- Data validation: ~10 seconds
- Archive predictions: ~5 seconds
- Track calibration (30 days): ~20 seconds
- A/B test generation: ~2 seconds
- Full data refresh: ~2-3 minutes

**Storage requirements:**
- Archives grow ~5KB per day
- 1 year of archives: ~1.8MB
- CSV trackers: <1MB per year

**API rate limits:**
- NHL API: No documented limit (be respectful)
- Use caching where possible

---

## Troubleshooting

### Validation failing
```bash
# Check specific file
python -m json.tool web/src/data/todaysPredictions.json

# Run validation manually
python scripts/validate_data_schemas.py
```

### Archiving not working
```bash
# Check if predictions file exists
ls -la web/src/data/todaysPredictions.json

# Run manually
python scripts/archive_predictions.py
```

### Calibration showing no data
```bash
# Check if archives exist
ls -la data/archive/predictions/

# Need to run archive first
python scripts/archive_predictions.py

# Then track calibration
python scripts/track_calibration.py
```

### Alerts not sending
1. Check webhook URLs are configured correctly
2. Verify secrets are set in GitHub
3. Test webhooks manually:
```bash
# Slack
curl -X POST "$SLACK_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test message"}'

# Discord
curl -X POST "$DISCORD_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{"content":"Test message"}'
```

---

## Future Enhancements

Potential additions:
- Automated bet slip generation
- SMS alerts for high-confidence picks
- Telegram bot integration
- Real-time odds comparison
- Automated results fetching (currently manual)
- Machine learning for post optimization
- Multi-language support
- White-label API for partners

---

## Support

For issues:
1. Check GitHub Actions logs
2. Review this documentation
3. Test scripts locally first
4. Check webhook/API credentials

## Credits

Built for Puckcast.AI - Data-driven NHL predictions
