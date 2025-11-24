# Repository Map: Active vs Legacy

## Active inputs/outputs (keep current)
- `predict_fast.py`, `predict_full.py`, `predict_simple.py`, `predict_tonight.py`
- `scripts/` (see scripts/README.md) and `scripts/run_daily.sh`
- `web/` (Next.js site), `web/src/data/*.json` feeds, `web/public/` assets
- `src/nhl_prediction/` (model code), `model_v6_6seasons.pkl`
- `data/` (model/data assets), `requirements.txt`, `runtime.txt`
- `tests/`, `analysis/` (active analysis utilities)

## Key docs (active)
- `README.md` (quickstart)
- `docs/INDEX.md` (doc index)
- `FEATURE_DICTIONARY.md`, `COMPREHENSIVE_AUDIT_V2.md`, `V2_OPTIMIZATION_RESULTS.md`
- `web/README.md`, `scripts/README.md`

## Legacy/archives (safe to ignore unless needed)
- `archive/` (legacy dashboards, old assets) and `docs/archive_v1/`
- `archive/legacy_dashboards/` (old Streamlit dashboards)
- Root checklists/plans: `DEPLOYMENT*.md`, `FINAL_CHECKLIST.txt`, `QUICKSTART.md`, `LAUNCH_READY.md`, `MOBILE_VERIFIED.md`, `WEBSITE_AUDIT.md`, `VERCEL_WHY_NOT.md`, `V2_SITE_PLAN*.md`, `V2_SITE_PLAN_REVISED.md`, `TWITTER_*`
- Backups: `README.md.backup`

## Housekeeping
- Ignored: `temp_outputs/`, `predictions_*.csv`, `devserver.log`
- Branches: only `main` and your `Backup-1` are retained; legacy branches removed.
