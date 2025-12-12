# X/Twitter Automation Setup Guide

Complete guide to setting up automated posting to X (Twitter) for Puckcast predictions.

## Overview

The Twitter automation posts predictions 3 times daily:
- **8:00 AM ET** - Morning preview with top picks
- **2:00 PM ET** - Afternoon update with high-confidence games
- **8:00 PM ET** - Evening recap and tomorrow's tease

Features:
- ✅ A/B testing framework to optimize engagement
- ✅ Automatic post generation from predictions data
- ✅ Multiple post format variants
- ✅ Engagement tracking and analysis
- ✅ Manual posting via GitHub Actions

---

## 1. Get Twitter API Credentials

### Create a Twitter Developer Account

1. Go to https://developer.twitter.com/
2. Sign in with your Twitter/X account
3. Apply for a developer account
4. Create a new Project and App

### Generate API Keys

In your Twitter Developer Portal:

1. **API Key and Secret** (Consumer Keys)
   - Go to your App → Keys and tokens
   - Click "Generate" under Consumer Keys
   - Save these immediately (you can't view them again)

2. **Access Token and Secret**
   - In the same Keys and tokens section
   - Click "Generate" under Authentication Tokens
   - Select "Read and Write" permissions
   - Save the Access Token and Access Token Secret

3. **Bearer Token** (Optional but recommended)
   - Also in Keys and tokens
   - Copy the Bearer Token

You should now have:
- `API Key` (Consumer Key)
- `API Key Secret` (Consumer Secret)
- `Access Token`
- `Access Token Secret`
- `Bearer Token` (optional)

---

## 2. Add Credentials to GitHub

### Add as Repository Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each of these secrets:

| Secret Name | Value |
|------------|-------|
| `TWITTER_API_KEY` | Your API Key |
| `TWITTER_API_SECRET` | Your API Key Secret |
| `TWITTER_ACCESS_TOKEN` | Your Access Token |
| `TWITTER_ACCESS_SECRET` | Your Access Token Secret |
| `TWITTER_BEARER_TOKEN` | Your Bearer Token (optional) |

**⚠️ Security**: Never commit these values to your repository!

---

## 3. Test the Automation

### Test Locally (Dry Run)

```bash
# Install dependencies
pip install tweepy

# Set environment variables (don't commit these!)
export TWITTER_API_KEY='your_api_key'
export TWITTER_API_SECRET='your_api_secret'
export TWITTER_ACCESS_TOKEN='your_access_token'
export TWITTER_ACCESS_SECRET='your_access_secret'

# Test post generation (doesn't actually tweet)
python scripts/post_to_twitter.py --post-type morning_preview --dry-run

# Actually post (use with caution!)
python scripts/post_to_twitter.py --post-type morning_preview
```

### Test via GitHub Actions

1. Go to **Actions** tab in your GitHub repo
2. Click **X/Twitter Posting Automation** workflow
3. Click **Run workflow**
4. Select a post type
5. Click **Run workflow**

The first run will be a dry-run if credentials aren't configured. Once credentials are added, it will actually post.

---

## 4. Post Format Customization

### A/B Testing Variants

Post formats are defined in `config/twitter_variants.json` (auto-created).

Example variants:

```json
{
  "morning_preview": [
    {
      "id": "A",
      "format": "emoji_heavy",
      "template": "🏒 NHL TODAY: {games} games\n\n🔥 TOP PICK:\n{top_game}..."
    },
    {
      "id": "B",
      "format": "minimal",
      "template": "Today's NHL predictions:\n\n{top_game}..."
    }
  ]
}
```

The system automatically rotates through variants to A/B test which formats get the most engagement.

### Edit Post Templates

1. The variants file will be auto-created on first run
2. Edit `config/twitter_variants.json`
3. Add/modify templates
4. Available variables:
   - `{games}` - Number of games
   - `{top_game}` - Best matchup
   - `{grade}` - Confidence grade
   - `{home_prob}` - Home win probability %
   - `{away_prob}` - Away win probability %
   - `{high_conf}` - Count of high-confidence games
   - `{url}` - Website URL

---

## 5. Analyze A/B Test Results

### View Results

```bash
python scripts/twitter_ab_testing.py --post-type morning_preview
```

This shows which post formats are performing best based on engagement.

### Track Engagement

Engagement data is logged to `data/archive/twitter_ab_tests.csv`. To add actual Twitter metrics:

1. Use Twitter API to fetch tweet analytics
2. Update the CSV with impressions and engagements
3. Re-run the analysis script

---

## 6. Scheduling

### Automatic Posts

The GitHub Action runs automatically at:
- 12:00 UTC (8:00 AM ET) - Morning preview
- 18:00 UTC (2:00 PM ET) - Afternoon update
- 00:00 UTC (8:00 PM ET) - Evening recap

### Manual Posting

Use the "Run workflow" button in GitHub Actions to post manually anytime.

### Disable Automation

To temporarily disable automated posts:
1. Go to **Actions** → **X/Twitter Posting Automation**
2. Click the "..." menu → **Disable workflow**

---

## 7. Troubleshooting

### "❌ tweepy not installed"

```bash
pip install tweepy
```

### "❌ Missing required environment variables"

Make sure all Twitter API credentials are set as GitHub Secrets.

### "⚠️ Post is XXX characters (limit: 280)"

Edit the variant templates in `config/twitter_variants.json` to be shorter.

### Rate Limits

Twitter API has rate limits:
- Standard access: ~1,500 tweets per month
- Posts should be well within this limit (3/day = ~90/month)

### Errors When Posting

Check Twitter API status: https://api.twitterstat.us/

---

## 8. Advanced Features

### Custom Site URL

Pass a different URL when posting:

```bash
python scripts/post_to_twitter.py \
  --post-type morning_preview \
  --site-url https://your-custom-domain.com
```

### Force Specific Variant

For testing a specific post format:

```bash
python scripts/post_to_twitter.py \
  --post-type morning_preview \
  --variant A
```

---

## 9. Files Reference

| File | Purpose |
|------|---------|
| `scripts/post_to_twitter.py` | Main posting script |
| `scripts/twitter_ab_testing.py` | A/B test framework |
| `.github/workflows/twitter-posting.yml` | Automation workflow |
| `config/twitter_variants.json` | Post format variants |
| `data/archive/twitter_ab_tests.csv` | Engagement tracking |

---

## Support

For issues or questions:
1. Check Twitter API documentation: https://developer.twitter.com/en/docs
2. Check tweepy documentation: https://docs.tweepy.org/
3. Review GitHub Actions logs for error details

---

**Ready to go!** 🚀

Once credentials are added to GitHub Secrets, posts will automatically go out 3x daily.
