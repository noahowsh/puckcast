# Archive Manifest (Legacy Docs & Visuals)

This manifest lists where older or superseded documentation and assets now live. Current, maintained docs live under `docs/` (see `docs/INDEX.md`) and the main `README.md`.

## Primary archive locations
- `archive/` — Legacy dashboards, reports, and status writeups.
- `archive/legacy_dashboards/` — Older dashboard docs and assets.
- `archive/docs/` — Prior site plans, deployment guides, audits, and Twitter setup docs.
- `docs/archive/` — Historical notes and intermediate reports.
- `docs/archive_v1/` — Early model/dash docs (pre-v6 series).
- `archive/legacy_web_docs/` — Default Next.js scaffold README (moved from `web/README 2.md`).
- `docs/archive/puckcast7_plan_legacy.md` — superseded v7 planning doc (replaced by `docs/PUCKCAST_V7_SPEC.md`).

## Data/model artifacts
- `data/archive/predictions/` — Daily prediction payloads (JSON) for backtests.
- `data/archive/results_tracker.csv` — Results tracking.
- `model_v6_6seasons.pkl` — Legacy model artifact (superseded by current training pipeline).

## Notes
- Current site data feeds are under `web/src/data/` and are updated by `predict_full.py` and GitHub Actions.
- Current docs: `README.md`, `docs/INDEX.md`, `docs/ROOT_MAP.md`, `docs/puckcast7_plan.md`, `docs/ARCHIVE_MANIFEST.md` (this file).
