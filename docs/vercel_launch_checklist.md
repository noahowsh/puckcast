# ✅ Vercel Launch Checklist

Use this punch list to prep the new `web/` Next.js experience for Vercel. Each block mirrors a milestone inside Vercel’s dashboard (Preflight → Import → Configure → Launch → Post-ship).

## 1. Preflight (run locally before tagging a deploy)

- [ ] Rebuild the JSON payloads that power the site  
  ```bash
  python predict_full.py                              # refresh web/src/data/todaysPredictions.json
  python scripts/generate_site_metrics.py             # refresh modelInsights + bankroll data
  python scripts/fetch_current_standings.py           # refresh live standings snapshot
  ```
- [ ] Verify the Next.js bundle compiles cleanly  
  ```bash
  cd web
  npm install
  npm run lint
  npm run build
  ```
- [ ] Ensure `.github/workflows/update-predictions.yml` has a valid PAT + schedule for nightly refreshes.
- [ ] Confirm `web/src/data/*.json` reflects the latest slate before pushing.

## 2. Create the Vercel project

- [ ] Visit [vercel.com/new](https://vercel.com/new) → import the `noahowsh/puckcast` repository.
- [ ] Set **Root Directory** to `web`.
- [ ] Build command: `npm run build` (defaults ok).  
      Output directory: `.next`.
- [ ] Select the latest Node runtime (≥ 20.x) under **Project Settings → General**.
- [ ] Optional env vars (add under **Settings → Environment Variables**):
  - `NEXT_TELEMETRY_DISABLED=1`
  - `NODE_OPTIONS=--max-old-space-size=4096` (only if build memory warnings appear)

## 3. Data + revalidation strategy

- [ ] Nightly GitHub Action (`Nightly predictions sync`) confirmed on default branch.
- [ ] Decide whether to trigger redeploys from that action (e.g., call Vercel Deploy Hook at the end of the workflow) so the JSON bundle ships automatically.
- [ ] Keep `scripts/` utilities handy for manual refreshes if the cron fails.
- [ ] Document who owns production data refresh in `README.md` (owner + backup).

## 4. Domains & previews

- [ ] Connect `puckcast.ai` (or preferred) under **Settings → Domains** after the first successful deploy.
- [ ] Verify preview deployments are enabled for feature branches (`main` → Production, other branches → Preview).
- [ ] Configure redirects (if any) via `next.config.ts` before launch.

## 5. Post-ship validation

- [ ] Smoke-test each route (`/`, `/predictions`, `/betting`, `/performance`, `/leaderboards`, `/analytics`, `/goalies`) on the production URL.
- [ ] Hit the API routes (`/api/predictions`, `/api/goalies`) and confirm caching headers in browser devtools.
- [ ] Run Lighthouse (desktop + mobile) to capture baseline scores.
- [ ] Enable Vercel Analytics + Speed Insights for ongoing monitoring.
- [ ] Create an incident runbook (where to check logs, how to rerun `predict_full.py`, who to page).

_Tip:_ Keep this file updated as we discover additional Vercel-specific steps (e.g., deploy hooks, env secrets, partnership logos). It lives in `docs/` so ops can treat it as the canonical launch checklist.
