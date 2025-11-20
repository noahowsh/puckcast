# Automation Setup Guide

This guide explains how to set up the automated data pipelines and GitHub Actions workflows for Puckcast.

## Overview

The automation system consists of:

1. **Data Generation Pipeline** - Python scripts that fetch NHL data and generate JSON files
2. **GitHub Actions Workflows** - Automated tasks that run on schedules
3. **Vercel Deployment** - Auto-deploy the Next.js site on every push

## Data Generation Pipeline

### Scripts

All data generation scripts are located in `/scripts/`:

| Script | Purpose | Output |
|--------|---------|--------|
| `refresh_site_data.py` | Master orchestrator - runs all data refresh tasks | All JSON files |
| `predict_full.py` | Generate game predictions using V6.0 model | `todaysPredictions.json` |
| `generate_site_metrics.py` | Calculate model performance metrics | `modelInsights.json` |
| `fetch_current_standings.py` | Fetch NHL standings | `currentStandings.json` |
| `generate_goalie_pulse.py` | Generate goalie performance insights | `goaliePulse.json` |
| `fetch_starting_goalies.py` | Get confirmed starting goalies | `startingGoalies.json` |
| `fetch_injuries.py` | Fetch player injury reports | `playerInjuries.json` |

### Manual Usage

Run the complete data refresh pipeline:

```bash
# Refresh all data for today
python scripts/refresh_site_data.py

# Refresh for a specific date
python scripts/refresh_site_data.py --date 2025-11-20

# Skip certain steps
python scripts/refresh_site_data.py --skip-standings --skip-metrics
```

Run individual scripts:

```bash
# Generate predictions only
python predict_full.py

# Generate model insights only
python scripts/generate_site_metrics.py

# Generate goalie pulse only
python scripts/generate_goalie_pulse.py --date 2025-11-20
```

### Output Files

All generated JSON files are written to `/web/src/data/`:

- `todaysPredictions.json` - Daily game predictions with A-C confidence grades
- `modelInsights.json` - Model accuracy stats, feature importance, backtesting
- `currentStandings.json` - NHL standings by division/conference
- `goaliePulse.json` - Goalie performance trends and insights
- `startingGoalies.json` - Confirmed starting goalie assignments
- `playerInjuries.json` - Active player injury reports
- `lineCombos.json` - Forward/defense line combinations

## GitHub Actions Workflows

### 1. Daily Predictions Update

**File:** `.github/workflows/daily-predictions.yml`

**Schedule:** Runs daily at 10:00 AM ET (2:00 PM UTC)

**What it does:**
- Fetches latest NHL data from APIs
- Runs V6.0 prediction model
- Generates all JSON data files
- Commits and pushes updated files to repo
- Triggers Vercel deployment

**Manual trigger:**
```bash
gh workflow run daily-predictions.yml
```

### 2. X/Twitter Posting Automation

**File:** `.github/workflows/twitter-posting.yml`

**Schedule:** Posts 3 times daily:
- 8:00 AM ET - Morning game preview
- 2:00 PM ET - Afternoon update
- 8:00 PM ET - Evening recap

**What it does:**
- Reads `todaysPredictions.json`
- Generates engaging post content
- Posts to X/Twitter API (when configured)

**Manual trigger:**
```bash
gh workflow run twitter-posting.yml -f post_type=morning_preview
```

**Setup required:**

Add these secrets to your GitHub repository:
- `TWITTER_API_KEY`
- `TWITTER_API_SECRET`
- `TWITTER_ACCESS_TOKEN`
- `TWITTER_ACCESS_SECRET`

To get Twitter API credentials:
1. Go to https://developer.twitter.com/
2. Create a new app
3. Generate API keys and access tokens
4. Add them to GitHub Secrets

### 3. Vercel Auto-Deploy

**File:** `.github/workflows/vercel-deploy.yml`

**Trigger:** Runs on push to `main` branch (when `/web` directory changes)

**What it does:**
- Installs Vercel CLI
- Builds Next.js production bundle
- Deploys to Vercel
- Comments deployment URL on commit

**Setup required:**

Add these secrets to your GitHub repository:
- `VERCEL_TOKEN` - Get from https://vercel.com/account/tokens
- `VERCEL_ORG_ID` - Found in Vercel project settings
- `VERCEL_PROJECT_ID` - Found in Vercel project settings

## Setup Instructions

### 1. Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Node.js dependencies (for Vercel deployment)
cd web
npm install
```

### 2. Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add the following secrets:

**For Vercel deployment:**
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

**For Twitter posting (optional):**
- `TWITTER_API_KEY`
- `TWITTER_API_SECRET`
- `TWITTER_ACCESS_TOKEN`
- `TWITTER_ACCESS_SECRET`

### 3. Enable GitHub Actions

1. Go to your repository on GitHub
2. Click "Actions" tab
3. Enable workflows if prompted
4. Workflows will now run on their schedules

### 4. Test Workflows

Manually trigger each workflow to test:

```bash
# Test daily predictions update
gh workflow run daily-predictions.yml

# Test Twitter posting (morning preview)
gh workflow run twitter-posting.yml -f post_type=morning_preview

# Test Vercel deployment (push to main triggers automatically)
git push origin main
```

## Monitoring

### Check Workflow Status

```bash
# List recent workflow runs
gh run list

# View specific workflow run
gh run view [run-id]

# Watch workflow logs in real-time
gh run watch
```

### Workflow Logs

View logs in GitHub:
1. Go to repository → Actions tab
2. Click on a workflow run
3. View logs for each step

## Troubleshooting

### Daily predictions not updating

1. Check GitHub Actions logs for errors
2. Verify NHL API is accessible
3. Ensure Python dependencies are installed
4. Check if data files are being committed

### Twitter posts not appearing

1. Verify Twitter API credentials are set correctly
2. Check if credentials have proper permissions (read + write)
3. Review workflow logs for API errors
4. Ensure post content doesn't exceed Twitter character limits

### Vercel deployment failing

1. Check Vercel token is valid
2. Verify project is properly linked
3. Review build logs for errors
4. Ensure `web/package.json` is configured correctly

## Customization

### Change prediction schedule

Edit `.github/workflows/daily-predictions.yml`:

```yaml
schedule:
  - cron: '0 14 * * *'  # Change time here (UTC)
```

### Modify Twitter post content

Edit `.github/workflows/twitter-posting.yml` and modify the `generate_post.py` script logic.

### Add new data sources

1. Create a new script in `/scripts/`
2. Add it to `refresh_site_data.py` workflow
3. Update GitHub Actions workflow to include it

## Performance

### Typical execution times:

- Daily predictions update: ~2-3 minutes
- Twitter posting: ~10 seconds
- Vercel deployment: ~1-2 minutes

### API rate limits:

- NHL Stats API: No documented limit, but be respectful
- Twitter API: Varies by tier (check your plan)
- Vercel: Depends on your plan

## Cost Estimate

- **GitHub Actions**: Free for public repos (2,000 minutes/month for private)
- **Vercel**: Free tier supports hobby projects
- **Twitter API**: Free tier available (check current rates)

Total estimated cost: **$0-20/month** depending on usage.

## Support

For issues or questions:
- Check GitHub Actions logs first
- Review this documentation
- Check NHL API status: https://api.nhle.com/stats/
- Check Vercel status: https://vercel.com/status

## Future Enhancements

Potential improvements:
- Add Slack/Discord notifications on deployment
- Implement A/B testing for Twitter post formats
- Add data validation checks before deployment
- Create dashboard for monitoring workflow health
- Add email alerts for prediction anomalies
