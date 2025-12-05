# Puckcast 7.0 Expansion Plan

> Working draft of potential upgrades for the next major push. Organized by theme with candidate deliverables, rationale, dependencies, and rough sequencing. Prioritize by user impact vs. effort; not all items are required for 7.0.

---

## 1) Product & Coverage
- **Playoff mode:** Separate calibration, narrative, and visuals for playoff series; add OT/shootout bias adjustments; series win probabilities.
- **Props-style breakdowns:** Shot/goal/point likelihood tiers per top skaters; goalie saves tiers; leverage xG and shot volume baselines.
- **Same-day “live health” badges:** Injury delta, goalie confirmation status, special teams gap, travel fatigue badge on matchup cards.
- **Team/Player hubs:** Form trendlines (xG, possession, special teams), injury timeline, goalie form/rest tracker, PP/PK trend heatmaps.
- **Archive & history:** Season-level timeline of daily slates, accuracy, and bankroll curves; searchable past slates with outcomes.
- **Explainability layer:** Per-game “why” (rest, special teams, goalie edge, injury gap); confidence rationale in plain language.
- **Localization & timezones:** Auto ET/PT switches; user-local time support; concise copy variants.

## 2) Data Ingest & Enrichment
- **Native ingest hardening:** Full NHL API ingest with retries/backoff; cache warming; detect stale/partial pulls.
- **Injuries depth:** Position-aware injury impact weighting; probable lines impact; IR vs day-to-day differentiation.
- **Goalie intelligence:** Recent GSAx/60, high-danger save %, back-to-back likelihood, starter confirmation confidence scoring.
- **Special teams detail:** Rolling PP/PK in multiple windows; opponent-adjusted; flag mismatches (already partially surfaced in fun facts).
- **Travel & fatigue:** Flight distance/segments; circadian penalty for east↔west swings; days-since-crossing-timezone.
- **Rink effects:** Venue shooting/goal environment adjustments; ice-time allocation trends at home vs away.
- **Market scrape (optional):** Pull consensus moneylines for calibration vs market; spot model/market deltas (requires policy check).

## 3) Modeling & Evaluation
- **Playoff-tuned calibration:** Separate playoff models or calibration layers; heavier weight on goalies, special teams, and matchups with high familiarity.
- **Ensemble exploration:** Blend calibrated logreg with gradient boosting (HistGBM) and/or light neural tabular models; maintain calibration via isotonic/Platt.
- **Feature refresh:** Add special-teams diff, goalie rest delta, injury gap, travel penalty to core model; reevaluate regularization strengths.
- **Calibration refresh:** Refit calibrator with larger validation windows (multi-season), test Platt vs isotonic smoothing to avoid plateaus, and publish calibration curves with version tags.
- **Drift monitoring:** Weekly metrics on accuracy, log loss, Brier; alert on drops vs trailing 30-day mean.
- **Simulation:** Monte Carlo sim for playoff brackets; series win odds; scenario explorer.
- **Fair odds export:** Convert probabilities to fair odds, hold-adjusted odds; enable display or downstream pricing comparison (comms only, not betting).
- **Team/venue calibration slices:** Per-team/per-venue calibration curves; surface chronic miscalibration cases for feature tuning.

## 4) Content & UX
- **Daily slate UX:** Timeline view with badges (rest, injury gap, special teams edge, goalie status); per-game “why” chips.
- **Performance page:** Current model metrics (accuracy, log loss, Brier, AUC), calibration curve, feature importance, bankroll curve, update timestamps.
- **Team pages:** Trend charts (rolling xG diff, PP/PK, rest, injuries, goalie form), upcoming schedule with predicted edges.
- **Goalie page:** Starter likelihood, rest days, recent form, matchup xG faced; “rested vs tired” flag.
- **Props-style cards:** Shots/points likelihood tiers for top players; simple “over/under vibe” visualization without lines.
- **Compare view:** Model vs market (if allowed); or model vs home baseline; highlight largest disagreements.
- **Email/notification-ready summaries:** One-click export of slate summary; optional daily digest formatting.

## 5) Automation & Ops
- **Retry/backoff on fetch:** Harden predictions fetch to avoid 500s; add logging for fallback usage frequency.
- **Data freshness SLA:** Track generatedAt ages across JSONs; alert if > X hours stale; Slack/Discord hooks.
- **Secrets/credential health:** Preflight check that social secrets are present; fail loudly if missing.
- **Artifact integrity:** Hash/size checks for JSON outputs; compare to prior day to catch empty payloads.
- **Archival:** Auto-archive daily JSONs; add compact delta logs (games count, generatedAt) for audits.
- **Testing:** Add regression tests for social templates (no leading @, required fields present); schema checks for enriched predictions API.

## 6) Distribution & Growth
- **Social enhancements:** Image cards per slate/feature; threaded breakdowns for marquee games; handle-safe openings; rotation of non-probability insights (injuries, special teams, rest).
- **LinkedIn/content drops:** Weekly recap post template with current metrics and notable edges hit/missed.
- **Landing page refresh:** Highlight calibration, accuracy, and “why” explanations; add live metric badges.
- **Transparency page:** Plain-English methodology, calibration results, update times, data sources.

## 7) Metrics & Reporting
- **Live metrics block:** Pull from `modelInsights.json` to show accuracy/log loss/Brier/edges live on the site and report.
- **Calibration tracker:** Automate `track_calibration.py` to produce calibration_report and tracker CSV daily; surface on performance page.
- **Feature importance refresh:** Recompute and publish top coefficients after each retrain; keep chart in assets.
- **Outcome backfill:** If outcomes become available, backfill archived predictions with actuals to compute true calibration bins for the season.

## 8) Risk & Compliance Considerations
- **Non-betting positioning:** Keep language informational; avoid line/odds presentation unless clearly labeled “fair odds” and non-advisory.
- **API rate limits:** Respect NHL endpoints; cache aggressively; exponential backoff.
- **Data quality:** Fallbacks for missing injuries/goalies; flags when enrichment is partial.
- **Social safety:** No leading mentions; safe copy defaults; avoid duplicate posts on failures.

---

## Sequencing (proposed order)
1) **Stability & metrics:** Harden fetch/retries, freshness SLA, calibration tracker automation, live metric badges.
2) **Explainability & UX:** Per-game “why” chips, badges (rest/injury/special teams/goalie), performance page with real metrics/plots.
3) **Coverage & modeling:** Playoff mode, feature refresh (injury gap, special teams diff, goalie rest), ensemble test.
4) **Content expansion:** Props-style player insights, team/goalie pages, richer social/image cards.
5) **Simulation:** Series odds and bracket sims ahead of playoffs.

---

## New add-ons to consider
- **Mobile-first power board:** Compact view and sticky column headers for small screens; collapse next-game text to opponent + day only.
- **Outcome backfill job:** Nightly NHL results ingest to enrich archived predictions with actual winners; unlock true calibration bins and post-hoc accuracy per slate.
- **Confidence bins on site:** Show live bin accuracies (0–5, 5–10, 10–15, 15–20, 20+) sourced from calibration tracker.
- **Alerting for stale edges:** Surface a banner if predictions are older than X hours or if API fallback was used.
- **Team matchup heatmaps:** Matrix of model accuracy and edge performance vs each opponent; highlight chronic misses.
- **Fast “what-if” toggles:** Simulate a starter swap or injury removal to show sensitivity of win prob/edge.

---

## Data/Artifact Sources to Leverage
- `web/src/data/modelInsights.json` (live metrics, feature importance, buckets)
- `reports/calibration_curve.png`, `reports/feature_importance_v2.csv` (real plots/coefficients)
- `web/src/data/todaysPredictions.json` (enriched predictions with special teams, injuries, goalie projections)
- Archived predictions: `data/archive/predictions/predictions_*.json`
- Validation outputs: `scripts/track_calibration.py`, `scripts/generate_site_metrics.py`

---

## Open Questions
- Should we add market comparison (fair odds vs consensus) publicly, or keep internal?
- Do we want player-level props-style outputs on-site, or just for social snippets?
- How heavy should playoff-specific tuning be (new model vs calibration layer)?
---
