# Puckcast v6.3 — Ingest & Model Source Comparison

This note documents the current state of model training with MoneyPuck vs native NHL ingest, the observed performance, and the workplan to finalize v6.3 decisions tomorrow.

## 1) Current Default (MoneyPuck)
- Source: `data/moneypuck_all_games.csv`, `data/moneypuck_goalies*.csv`.
- Code path: `fetch_multi_season_logs` uses MoneyPuck when the CSV exists and `PUCKCAST_NATIVE_INGEST` is unset.
- Training/serving impacted: `python -m nhl_prediction.train`, `predict_full.py`, and site refreshes all use MoneyPuck by default.
- Latest run (3 seasons: 20212022–20232024):
  - Model: HistGradientBoosting
  - Validation: acc 0.622 | ROC-AUC 0.657 | log-loss 0.658 | threshold 0.570
  - Test: acc 0.5829 | ROC-AUC 0.6161 | log-loss 0.6761 | Brier 0.2414
  - Baseline accuracy (majority class): 0.5008
  - Runtime: ~37s

## 2) Native Ingest Attempt (NHL API)
- Toggle: set `PUCKCAST_NATIVE_INGEST=1` in env.
- Attempted command: `PUCKCAST_NATIVE_INGEST=1 PYTHONPATH=src python -m nhl_prediction.train` (3 seasons).
- Outcome: Did not finish after ~30 minutes; native ingest hit repeated NHL API errors (“10 consecutive errors” mid-season) and aborted partial season, so no model metrics were produced.
- Partial caches were written for 20212022/20222023 native logs, so retry may be faster.
- Risk: Runtime significantly higher; NHL API error handling stops after 10 consecutive failures.

## 3) Observations
- MoneyPuck path is fast, stable, and currently calibrated (~58.3% test accuracy).
- Native path needs reliability/throughput fixes before it can be compared apples-to-apples.
- All production artifacts (predictions, posts, refreshes) are still MoneyPuck-driven unless env var forces native.

## 4) Plan for v6.3 (tomorrow)
1) Fast sanity check (single-season native):
   - `PUCKCAST_NATIVE_INGEST=1 PYTHONPATH=src python -m nhl_prediction.train --train-seasons 20232024 --test-season 20232024`
   - Goal: get a quick metric read without multi-season runtime.
2) Full native re-run with guardrails:
   - Increase timeout; allow more than 10 consecutive errors or add retry/backoff.
   - Use existing native cache to speed up; if available, prefetch/capture error log (`native_run.log`).
3) Side-by-side metrics:
   - Capture acc/ROC/log-loss/Brier for MoneyPuck vs Native on the same season set.
   - Record runtime and failure points.
4) Decision switch:
   - If native is competitive (±1–2% acc, better log-loss) and stable: set `PUCKCAST_NATIVE_INGEST=1` in workflows.
   - Otherwise keep MoneyPuck as default; document native as optional.
5) Pipeline hardening (if we keep native path option):
   - Raise/stagger NHL API retry budget; don’t abort after 10 consecutive failures.
   - Add “native ingest freshness” check; fall back to MoneyPuck if native is stale/incomplete.

## 5) Commands reference
- MoneyPuck (default): `PYTHONPATH=src python -m nhl_prediction.train`
- Native toggle: `PUCKCAST_NATIVE_INGEST=1 PYTHONPATH=src python -m nhl_prediction.train`
- Quick native sanity (1 season): `PUCKCAST_NATIVE_INGEST=1 PYTHONPATH=src python -m nhl_prediction.train --train-seasons 20232024 --test-season 20232024`

## 6) Risk log
- Native ingest runtime: high; may exceed CI time budgets.
- Native ingest reliability: NHL API failures trigger abort after 10 errors.
- MoneyPuck dependency: requires local CSV freshness; ensure periodic refresh if we stay on it.

## 7) What to do first tomorrow
- Run the single-season native sanity check and capture metrics.
- If sane, run the full 3-season native with retries/logs; otherwise document that native is deferred.
- Update this doc with native metrics and final go/no-go for default ingest in v6.3.
