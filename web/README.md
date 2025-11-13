# Puckcast landing page

A custom marketing/front-door experience for the NHL prediction engine. The page highlights our differentiators and surfaces a live "Today’s Predictions" slice directly on the homepage. It is optimized for deployment on [Vercel](https://vercel.com/).

## Local development

```bash
cd web
npm install   # already run once, but keep for fresh clones
npm run dev   # http://localhost:3000
```

Tailwind CSS v4 is already wired up. Update `src/app/page.tsx` for layout changes and `src/data/todaysPredictions.json` for the data powering the prediction cards.

### Available routes

- `/` – Hero + marketing story + Tonight's highlights
- `/predictions` – Deep dive table + edge callouts sourced from `todaysPredictions.json`
- `/betting` – Kelly/threshold strategy receipts + bankroll curve
- `/performance` – Team-by-team accuracy + calibration buckets
- `/leaderboards` – Power rankings, streak tracker, matchup receipts + conference tables
- `/analytics` – Feature correlations + distribution notes
- `/goalies` – Goalie pulse cards fed by `src/data/goaliePulse.json`

Supporting data files:

- `src/data/todaysPredictions.json` – slate powering `/` and `/predictions`
- `src/data/goaliePulse.json` – goalie insights for `/goalies`
- `src/data/modelInsights.json` – aggregated metrics used across `/`, `/betting`, `/performance`, `/leaderboards`, `/analytics`
- `src/data/currentStandings.json` – snapshots from the NHL standings API used on `/leaderboards` and `/performance`

## Wiring real data

`predict_full.py` now exports two artifacts per run:

- `predictions_<DATE>.csv` (existing behavior)
- `web/src/data/todaysPredictions.json` (new) — the Next.js app imports this JSON directly.

To refresh the landing page data:

```bash
python scripts/refresh_site_data.py
# optional: python scripts/refresh_site_data.py --date 2025-11-15 --skip-standings
git add web/src/data/todaysPredictions.json web/src/data/currentStandings.json web/src/data/goaliePulse.json
git commit -m "Update predictions"
git push
```

During deployment Vercel will bundle the JSON, so each push automatically syncs the homepage with the most recent model run. Widgets like `PredictionTicker` and `GoalieTicker` now poll `/api` endpoints for fresher data between deploys.

To refresh the aggregate metrics used across the marketing site, rerun:

```bash
python scripts/generate_site_metrics.py
python scripts/fetch_current_standings.py
```

### Automated refresh (GitHub Actions)

`.github/workflows/update-predictions.yml` runs every morning (11:00 UTC) and on manual dispatch. It installs the Python stack, runs `python scripts/refresh_site_data.py`, commits the refreshed `todaysPredictions.json`, `currentStandings.json`, and `goaliePulse.json`, and pushes back to `main` using the built-in `GITHUB_TOKEN`.

- If there are no JSON changes (e.g., NHL off day) the workflow skips the commit
- Tweak the cron or add more steps if you introduce variant models or artifacts

## Deploying to Vercel

1. Push the repo (including `web/`) to GitHub.
2. In Vercel, create a new project and import the repository.
3. Set **Root Directory** to `web`, keep the default build command (`npm run build`) and output directory (`.next`).
4. Add environment variables if you need API keys or private endpoints.
5. Connect your custom domain (e.g., `puckcast.ai`) under _Settings → Domains_.

Every push to `main` will ship a new landing page automatically, while preview branches get their own URLs for approvals.

## API endpoints

- `GET /api/predictions` — returns the latest `todaysPredictions` payload with HTTP caching headers (public, 60s)
- `GET /api/goalies` — returns goalie pulse metadata (public, 5 min)

Client widgets poll these endpoints every 60–120s for live-ish updates, but you can also consume them from partner properties.
