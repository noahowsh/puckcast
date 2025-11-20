# 🚀 Puckcast Quick Start Guide

Get Puckcast up and running in 5 minutes with complete automation!

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Automation Setup](#automation-setup)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required
- Python 3.11+
- Git
- GitHub account (for automation)

### Optional (for full automation)
- Vercel account (free tier works!)
- Twitter/X Developer account (for social posting)
- Slack/Discord (for alerts)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/puckcast.git
cd puckcast
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `pandas` - Data processing
- `numpy` - Numerical computing
- `scikit-learn` - Machine learning
- `requests` - API calls
- `typer` - CLI framework
- `rich` - Pretty output

### 3. Install Node Dependencies (for web frontend)

```bash
cd web
npm install
cd ..
```

---

## Basic Usage

### Generate Today's Predictions

```bash
# Simple: predict today's games
python predict_full.py

# Specific date
python predict_full.py 2025-11-20
```

**Output:**
- Console: Formatted predictions with confidence grades
- CSV: `predictions_YYYY-MM-DD.csv`
- JSON: `web/src/data/todaysPredictions.json`

### Refresh All Site Data

```bash
# Update all data files (predictions, standings, goalies, etc.)
python scripts/refresh_site_data.py

# For specific date
python scripts/refresh_site_data.py --date 2025-11-20
```

**Generates:**
- `todaysPredictions.json` - Game predictions
- `modelInsights.json` - Model performance
- `currentStandings.json` - NHL standings
- `goaliePulse.json` - Goalie insights
- `startingGoalies.json` - Confirmed starters
- `playerInjuries.json` - Injury reports
- `lineCombos.json` - Line combinations

### Run Web Dashboard Locally

```bash
cd web
npm run dev
```

Visit `http://localhost:3000` to see your predictions!

---

## Automation Setup

### Step 1: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

#### For Vercel Deployment (Required for auto-deploy)
```
VERCEL_TOKEN          # Get from vercel.com/account/tokens
VERCEL_ORG_ID         # Find in Vercel project settings
VERCEL_PROJECT_ID     # Find in Vercel project settings
```

#### For Twitter Posting (Optional)
```
TWITTER_API_KEY
TWITTER_API_SECRET
TWITTER_ACCESS_TOKEN
TWITTER_ACCESS_SECRET
```

#### For Monitoring Alerts (Optional)
```
SLACK_WEBHOOK_URL     # Get from Slack app settings
DISCORD_WEBHOOK_URL   # Get from Discord server settings
```

### Step 2: Enable GitHub Actions

1. Go to your repository on GitHub
2. Click the **Actions** tab
3. Click **"I understand my workflows, go ahead and enable them"**

### Step 3: Verify Workflows

Your automation is now active! Here's what runs automatically:

| Workflow | Schedule | Purpose |
|----------|----------|---------|
| **Daily Predictions** | 10:00 AM ET | Generate predictions, update site |
| **Fetch Results** | 4:00 AM ET | Get game results, update accuracy |
| **Model Retraining** | Monday 3:00 AM ET | Retrain model on new data |
| **Data Validation** | On PR/push | Validate data integrity |
| **Monitoring** | Every 6 hours | Health checks, alerts |
| **Scheduled Refresh** | 4x-1x daily | Granular data updates |
| **Twitter Posting** | 8am, 2pm, 8pm ET | Social media automation |
| **Vercel Deploy** | On push to main | Auto-deploy website |

### Step 4: Manual Triggers

You can manually trigger any workflow:

```bash
# Daily predictions
gh workflow run daily-predictions.yml

# Fetch results for specific date
gh workflow run fetch-results.yml -f date=2025-11-20

# Retrain model
gh workflow run model-retraining.yml -f auto_deploy=true

# Twitter post
gh workflow run twitter-posting.yml -f post_type=morning_preview
```

---

## Testing

### Validate Data

```bash
# Check all JSON files for errors
python scripts/validate_data_schemas.py

# Should output: ✅ All data files passed validation
```

### Archive Predictions

```bash
# Save today's predictions to archive
python scripts/archive_predictions.py

# Archives to: data/archive/predictions/predictions_YYYY-MM-DD.json
```

### Track Calibration

```bash
# Analyze confidence grades vs actual results (needs archived data with results)
python scripts/track_calibration.py --days 30

# Outputs: web/src/data/calibrationReport.json
```

### Test Twitter Variants

```bash
# Generate A/B test variants
python scripts/twitter_ab_testing.py --post-type morning_preview

# Force specific variant
python scripts/twitter_ab_testing.py --post-type morning_preview --variant B
```

### Fetch Results

```bash
# Get yesterday's game results
python scripts/fetch_results.py

# Specific date
python scripts/fetch_results.py --date 2025-11-19

# Outputs: backtestingReport.json with accuracy stats
```

---

## Troubleshooting

### Issue: "No module named 'nhl_prediction'"

**Solution:**
```bash
# Make sure you're in the project root directory
cd /path/to/puckcast

# Add src to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Or install in editable mode
pip install -e .
```

### Issue: "No games scheduled"

**Possible causes:**
1. No NHL games on that date (check NHL schedule)
2. NHL API is down (check https://api.nhle.com/stats/)
3. Date format is wrong (use YYYY-MM-DD)

**Solution:**
```bash
# Check NHL schedule
curl https://api-web.nhle.com/v1/schedule/now

# Try different date
python predict_full.py 2025-11-20
```

### Issue: "GitHub Actions workflow failed"

**Steps to debug:**
1. Go to GitHub → Actions tab
2. Click on the failed workflow
3. Expand the failed step
4. Check error messages

**Common issues:**
- Missing secrets → Add them in repo settings
- API rate limits → Wait and retry
- Data validation errors → Check JSON files

### Issue: "Vercel deployment failed"

**Solution:**
1. Verify secrets are correct:
   ```bash
   # Test Vercel CLI locally
   cd web
   vercel whoami
   ```
2. Check Vercel project is linked:
   ```bash
   vercel link
   ```
3. Review deployment logs in Vercel dashboard

### Issue: "Twitter posts not appearing"

**Solution:**
1. Verify API credentials are correct
2. Check Twitter API permissions (need read+write)
3. Ensure post content doesn't exceed 280 characters
4. Review workflow logs for API errors

---

## Advanced Usage

### Custom Schedules

Edit `.github/workflows/scheduled-data-refresh.yml` to change update frequencies:

```yaml
schedule:
  # Change from 4x daily to 2x daily for predictions
  - cron: '0 14,2 * * *'  # 10am and 10pm ET
```

### Add New Data Sources

1. Create script in `scripts/`
2. Add to `refresh_site_data.py`
3. Update GitHub Actions workflow

Example:
```python
# scripts/fetch_custom_data.py
def fetch_custom_data():
    # Your data fetching logic
    data = {...}

    # Save to web/src/data/
    with open("web/src/data/customData.json", "w") as f:
        json.dump(data, f, indent=2)
```

### Customize Twitter Posts

Edit variant templates in `config/twitter_variants.json`:

```json
{
  "morning_preview": [
    {
      "id": "E",
      "format": "your_custom_format",
      "template": "Your custom template with {variables}"
    }
  ]
}
```

---

## Performance

### Expected Execution Times

| Operation | Duration |
|-----------|----------|
| Generate predictions | 2-3 minutes |
| Refresh all data | 3-5 minutes |
| Validate data | 10 seconds |
| Archive predictions | 5 seconds |
| Fetch results | 30-60 seconds |
| Model retraining | 10-20 minutes |

### Storage Requirements

| Data Type | Size |
|-----------|------|
| Daily predictions | ~5KB |
| Archives (1 year) | ~1.8MB |
| Model artifacts | ~5MB |
| Tracking CSVs | <1MB/year |

---

## Next Steps

### Learn More

- **[AUTOMATION_SETUP.md](docs/AUTOMATION_SETUP.md)** - Detailed automation guide
- **[ENHANCEMENTS.md](docs/ENHANCEMENTS.md)** - Advanced features guide
- **[README.md](README.md)** - Full project documentation
- **[FEATURE_DICTIONARY.md](FEATURE_DICTIONARY.md)** - All 141+ features explained

### Deploy to Production

1. **Set up Vercel project:**
   ```bash
   cd web
   vercel
   ```

2. **Configure custom domain** (optional):
   - Vercel dashboard → Settings → Domains
   - Add your domain (e.g., puckcast.ai)

3. **Enable all workflows** in GitHub Actions

4. **Monitor performance** via:
   - GitHub Actions logs
   - Vercel deployment dashboard
   - Slack/Discord alerts

### Community

- **Issues:** Report bugs or request features on GitHub
- **Pull Requests:** Contributions welcome!
- **Discussions:** Join GitHub Discussions for questions

---

## Quick Reference

### Essential Commands

```bash
# Daily workflow
python scripts/refresh_site_data.py        # Update all data
python scripts/archive_predictions.py      # Save to archive
python scripts/fetch_results.py            # Get game results

# Validation
python scripts/validate_data_schemas.py    # Check data integrity

# Analysis
python scripts/track_calibration.py --days 30    # Calibration analysis
python scripts/twitter_ab_testing.py --post-type morning_preview

# Model
python -m nhl_prediction.train             # Train model
python scripts/retrain_model.py            # Automated retraining

# Deployment
cd web && npm run build                    # Build frontend
vercel --prod                              # Deploy to Vercel
```

### File Locations

```
web/src/data/               # Live data (commit these)
data/archive/               # Historical data (commit these)
models/                     # Model artifacts
reports/                    # Training reports
.github/workflows/          # Automation configs
scripts/                    # All utility scripts
```

---

## Support

**Having issues?**
1. Check [Troubleshooting](#troubleshooting) section
2. Review GitHub Actions logs
3. Search existing GitHub Issues
4. Create a new issue with details

**Need help?**
- Include error messages
- Specify your environment (OS, Python version)
- Share relevant logs

---

**Ready to predict some hockey games? Let's go! 🏒**

For the full documentation, see [README.md](README.md)
