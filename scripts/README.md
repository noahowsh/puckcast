# Scripts Overview

## Live/Automation
- `predict_fast.py` / `predict_full.py` — generate web feed (`web/src/data/todaysPredictions.json`).
- `scripts/validate_predictions.py` — sanity-check predictions payload (used in workflows).
- `scripts/twitter_ab_testing.py` + `scripts/post_to_twitter.py` — X automation (hashtags/mentions auto-added).
- `scripts/archive_predictions.py` — archives daily predictions.
- `scripts/refresh_site_data.py` — wrapper to refresh feeds.
- `scripts/run_daily.sh` — one-shot runner for the above.

## Data fetchers
- `scripts/fetch_current_standings.py`
- `scripts/fetch_starting_goalies.py`
- `scripts/fetch_injuries.py`
- `scripts/generate_goalie_pulse.py`
- `scripts/generate_site_metrics.py`

## Diagnostics
- `scripts/validate_data_schemas.py`
- `scripts/track_calibration.py`

## Legacy/utility
- `scripts/explain_prediction.py`, `scripts/generate_dashboard.py`, `scripts/retrain_model.py` (manual)
- Archive / prototypes live under `analysis/` or `archive/`.

## Env/Secrets
- X/Twitter: `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_SECRET`, (optional) `TWITTER_BEARER_TOKEN`.
