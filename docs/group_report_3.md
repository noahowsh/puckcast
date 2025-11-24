# NHL Game Prediction Model — Final Project Report (v3)

**Group:** Puckcast ML Team  
**Date:** November 24, 2025  
**Team Members:** Noah O., [add teammates]

---

## Introduction
We built and deployed an end-to-end NHL win-probability system that ingests live data, engineers features, trains calibrated models, and publishes daily predictions to the web and social channels. This report summarizes the current state (v6), key improvements since Report 2, and recommendations for ongoing operations.

## Objective / Question
Predict NHL game outcomes with calibrated, actionable win probabilities that outperform simple baselines (home-team or moneyline implied) while remaining production-ready for daily automation and public-facing content.

## Assumptions
- Regular-season context; playoffs not modeled separately.
- MoneyPuck + NHL API data are timely and correct; missing data fall back to league-average/zeroed features.
- No in-game live updating (pregame probabilities only).
- Current automation schedules (GitHub Actions + Vercel) are available and secrets configured.

## Analytical Setup & Analysis
- **Data pipeline:** MoneyPuck game logs (team-level), NHL schedule/results, special teams, goalie/injury ingest; robust validation (schema + freshness checks).
- **Features:** 140+ engineered signals (rolling form, xG/shot quality, special teams splits, rest/back-to-back, travel, Elo-like ratings, goaltending quality).
- **Modeling:** Calibrated logistic regression (isotonic) chosen for stability and interpretability; native ingest/xG model available as fallback.
- **Validation:** Temporal splits (train on past seasons, validate on most recent season); avoids leakage via lagged features; probability calibration measured against baseline.
- **Automation:** Daily/6x-daily refresh workflows, validation gates, fallback fetch, and social posting. Monitoring workflow alerts on stale data or anomalies.

## Key Results (current v6 snapshot)
- Test accuracy: ~59% (≈ +6 pts over home-baseline) with calibrated probabilities and ROC-AUC ≈ 0.62 on recent seasons.
- Model edges surfaced as grades (A–C) and used for site and social content.
- Daily slate summary posts and full JSON payloads auto-publish; API enriched with goalies, injuries, special teams.

## Implications & Recommendations
- **Operational:** Keep the calibrated model as default; continue daily validation (stale-data + anomaly checks). Monitor API fallback success; prioritize stability over marginal feature tweaks.
- **Content:** Use slate summary at 8am ET for coverage; highlight special teams, injury, and goalie-rest facts to diversify posts (already implemented). Avoid leading mentions to keep posts in “Posts” tab.
- **Model:** Next lift likely from improved special-teams and goalie form features; consider playoff-specific calibration before postseason.
- **Data quality:** Maintain MoneyPuck cache freshness; add automatic retries/backoff for predictions API to reduce 500-induced skips.

## Limitations
- No live in-game updates; pregame only.
- Playoffs not separately tuned; high-variance games may be miscalibrated.
- Social automation depends on external API stability and configured secrets.
- Data gaps (e.g., missing injuries/goalies) fall back to averages and can dampen edge quality.

## Conclusion
The v6 system is production-stable, calibrated, and automated end-to-end. It meaningfully beats baseline pickers while staying explainable. With the current automation (web, API, and social), the product is user-facing and repeatable; further gains should focus on richer special-teams/goalie dynamics and postseason calibration rather than core pipeline rewrites.

## References
- MoneyPuck game-by-game data (https://moneypuck.com)  
- NHL Stats API (schedule, teams, results)  
- scikit-learn (logistic regression, calibration)  
- Puckcast repository: data pipeline, model code, and automation workflows
