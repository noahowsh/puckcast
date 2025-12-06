# NHL Game Prediction Model — Final Project Report (v3)

**Group:** Puckcast ML Team  
**Date:** December 05, 2025  
**Team Members:** Noah O., Team (update with final roster)

---

## Executive Summary (what changed vs. Report 2)
- **Stronger delivery:** Automated slate summary at 8 AM ET, richer fun-facts (special teams, injuries, goalie rest), and clearer “why” signals on the slate.
- **Production stability:** Hardened fallbacks for predictions API, no leading mentions, validation gates on every run.
- **Model posture:** Calibrated logistic regression remains the primary engine (59.3% accuracy vs 53.7% baseline; log loss 0.676; Brier 0.240) with isotonic calibration and enriched inputs (special teams, goalie/injury metadata).

### Quick Visuals (v6 snapshots)
- Pipeline overview (v6): ![Pipeline](assets/presentation/flow.svg)  
  *NHL API ingest + internal xG → 200+ lagged features → calibrated logreg → JSON/API/reports.*
- Metrics (v6): ![Metrics](assets/presentation/metrics.svg)  
  *Accuracy 59.3% vs 53.7% baseline; log loss 0.676; Brier 0.240.*
- Calibration curve (v6): ![Calibration](assets/presentation/calibration.svg)  
  *Probabilities track observed outcomes; curve near diagonal.*
- Feature signals (v6): ![Feature Importance](assets/feature_importance.png)  
  *Rolling goal diff, special teams, rest/B2B, xG/shot quality, possession.*
- Slate card example: ![Prediction](assets/presentation/prediction_card.svg)  
  *Clean matchup layout with badges and timestamps.*

Key metrics table:

| Metric                             | Value (v6) | Note                                  |
|------------------------------------|------------|---------------------------------------|
| Test accuracy (2023-24 holdout)    | 59.3%      | Baseline 53.7% home win rate          |
| Log loss                           | 0.676      | Lower is better (calibration)         |
| Brier score                        | 0.240      | Probability accuracy                  |
| Games evaluated                    | 1,230      | 2023-24 season                        |
| Feature count                      | 200+       | Rolling form, xG/shot quality, rest   |
| Daily automation                   | 6×/day     | Predictions + social + validation     |

---

## Introduction
We built and deployed an end-to-end NHL win-probability system that ingests live data, engineers features, trains calibrated models, and publishes daily predictions to the web and social channels. This report summarizes the current state (v6), key improvements since Report 2, and recommendations for ongoing operations.

## Objective / Question
Predict NHL game outcomes with calibrated, actionable win probabilities that outperform simple baselines (home-team or moneyline implied) while remaining production-ready for daily automation and public-facing content.

## Assumptions
- Scope: regular season only; playoffs not separately modeled or calibrated.
- Timing: pregame probabilities only; no in-game/live updates.
- Data freshness: NHL API schedule/results/plays available; on gaps we fall back to league-average/zeroed features.
- Automation: GitHub Actions + Vercel secrets are configured and usable.
- No external odds/market data used in training; purely model-based probabilities.

## Analytical Setup & Methods
- **Data ingest:** NHL Stats API (schedule, teams, results, plays) plus internal xG/shot-quality model; goalie and injury context pulled into features.
- **Feature engineering:** 200+ lagged/differenced features (rolling 3/5/10 for win%, goal/xG diff, shot quality, PP/PK, rest/B2B, travel, Elo-like ratings, goalie/injury flags). All rolling stats use lag (`shift(1)`) to avoid leakage; matchup context uses home-away deltas.
- **Modeling:** Calibrated logistic regression with isotonic calibration; edges expressed in percentage points and graded (A–C).
- **Validation:** Temporal split—train on prior seasons, test on most recent (2023-24 holdout). Metrics: accuracy, log loss, Brier, AUC, calibration by edge buckets. Baseline: home-win majority (53.7%).
- **Automation & gates:** Schema/freshness validation on every refresh; failing validation blocks publish; posting workflow avoids leading mentions.

## Analytical Setup & Analysis
- **Data sources:** NHL Stats API (schedule, results, teams, play-by-play) plus internal xG/shot-quality model; special teams and lineup context; goalie/injury ingest. Validation includes schema and freshness checks.
- **Data pipeline:** Native ingest + cached internal artifacts; enriched predictions payload with special teams, injury counts, goalie projections, start times, and edges.
- **Features (200+):** Rolling form (3/5/10), xG/shot quality, special teams splits (PP/PK diff), rest/back-to-back, travel penalties, Elo-like ratings, goaltending quality, injury gap, goalie rest delta, venue/home ice.
- **Feature engineering approach:** Lagged rolling windows to avoid leakage; deltas (home-away) for matchup context; categorical buckets for rest/travel; calibrated probabilities via isotonic regression; edges expressed in percentage points and graded (A–C).
- **Modeling:** Calibrated logistic regression (isotonic) chosen for stability and interpretability; native ingest/xG model available as fallback.
- **Validation:** Temporal splits (train on past seasons, validate on most recent season); avoids leakage via lagged features; probability calibration measured against baseline.
- **Automation:** Daily/6x-daily refresh workflows, validation gates, fallback fetch, and social posting. Monitoring workflow alerts on stale data or anomalies.

### Visual snapshot: Automation map
| Time (ET) | Post/Task              | Workflow                    |
|-----------|------------------------|-----------------------------|
| 08:00     | Slate summary (all games, probs, grades) | X: Core daily / High-frequency |
| 10:30     | Micro insight          | X: High-frequency           |
| 14:00     | Afternoon update       | X: Core daily / High-frequency |
| 17:00     | Game of the night      | X: High-frequency           |
| 18:30     | Upset watch            | X: High-frequency           |
| 20:00     | Evening recap          | X: Core daily / High-frequency |

## Key Results (current v6 snapshot)
- Test accuracy: 59.3% vs 53.7% home baseline (2023-24 holdout); log loss 0.676, Brier 0.240.
- Calibration by edge buckets (2023-24 holdout): 0–5 pts ~49% (n=198), 5–10 pts ~50.7% (n=221), 10–15 pts ~59.5% (n=195), 15–20 pts ~56.1% (n=180), 20+ pts ~69.5% (n=436).
- Model edges surfaced as grades (A–C) and used for site/API content.
- Daily slate summary auto-publishes; API enriched with goalies, injuries, special teams; validation/fallbacks keep payload fresh.

## Implications & Recommendations
- **Operational:** Keep the calibrated model as default; continue daily validation (stale-data + anomaly checks). Monitor API fallback success; keep retries/backoff for predictions API.
- **Content:** Lead with the 8 AM slate summary; rotate insights (special teams, injury gaps, goalie rest) to avoid “all probability” tone. Maintain handle-safe openings to stay in the Posts tab.
- **Model:** Next lift likely from richer special-teams and goalie form dynamics; add playoff-specific calibration before postseason.
- **Data quality:** Monitor injury/goalie ingest coverage; ensure GitHub secrets stay valid; keep ingest caches warm and validated.

## Limitations
- No live in-game updates; pregame only.
- Playoffs not separately tuned; high-variance games may be miscalibrated.
- Social automation depends on external API stability and configured secrets.
- Data gaps (e.g., missing injuries/goalies) fall back to averages and can dampen edge quality.

## Future Work (Puckcast 7.0 themes)
- Playoff mode: separate calibration, series odds, OT/shootout bias adjustments.
- Feature refresh: injury gap weighting, richer special teams, goalie rest delta, travel penalties.
- Explainability: per-game “why” chips (rest, special teams, goalie, injury) on slate and API.
- Performance page: live metrics (accuracy, log loss, Brier, calibration bins), feature importance, bankroll curve.
- Props-style insights: shots/points/save tiers for top skaters/goalies; simple “over/under vibe” without odds.
- Drift and freshness: SLA monitors on generatedAt, retry/backoff on fetch, and calibration tracker automation.

## Conclusion
The v6 system is production-stable, calibrated, and automated end-to-end. It meaningfully beats baseline pickers while staying explainable. With the current automation (web, API, and social), the product is user-facing and repeatable; further gains should focus on richer special-teams/goalie dynamics and postseason calibration rather than core pipeline rewrites.

## References
- NHL Stats API (schedule, teams, results, plays)  
- Internal xG/shot-quality model + derived team logs  
- scikit-learn (logistic regression, calibration)  
- Puckcast repository (data pipeline, model code, automation workflows)  
- GitHub Actions + Vercel deployment (automation and hosting)  
- Pandas/NumPy (data prep), internal validation scripts (schema/freshness), isotonic calibration toolkit  
- Visualization assets in `docs/assets/` (pipeline, automation, accuracy, calibration, feature importance)  
