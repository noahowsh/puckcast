# Puckcast v7.0 Specification

## 1) Overview / Purpose of v7
- v7 focuses on elevating season-long intelligence (simulation + rankings), sharpening model inputs, and hardening reliability end-to-end.
- Goals: publish season simulations and a refreshed Power Index with explainability, add a performance page, upgrade the model feature set, and solidify goalie inputs and ingest stability.
- Why it matters: delivers league-wide probabilities, transparent rankings, and clearer performance receipts while reducing data staleness and improving model fidelity.
- Themes: simulations, ranking explainability, model feature refresh, goalie pipeline, stability, and streamlined slate UX.

## 2) Scope — Features Included in v7

### A. Season Simulation Engine
- Run 5k–20k simulations daily; compute playoff %, division %, conference %, optional Cup %.
- Output JSON; expose live page at `/season` with table + probability bars, optional trend arrows, and “last updated” timestamp.

### B. Power Index v2 (with explainability)
- Weighted ranking refresh plus 1–2 sentence explainability per team.
- Movement arrows (↑ ↓ –); factors surfaced: recent form, special teams, injuries, shot quality, strength of schedule.
- Clean UI at `/power`.

### C. Performance Page (MVP)
- Surface 7-day accuracy, season accuracy, recent hits/misses (20–30 games), one calibration/reliability graphic, last model update timestamp.
- Clean UI at `/performance`.

### D. Starting Goalie Pipeline
- Automated pull for expected/confirmed starters; integrate goalie rest and confirmation status.
- Light badges (e.g., “Confirmed: Shesterkin”, “Likely: Saros”); inject goalie strength as a feature; increase model reliability.

### E. Model v7 Feature Refresh
- Add/refresh features: injury gap, special teams differential, goalie rest, rolling xG / shot share (EWMA), home/away splits, simple travel adjustment.
- Retrain with new feature set and re-calibrate.

### F. Slate Page UX Improvements
- Remove explainability chips; keep cards clean.
- Add updated timestamp, refined bar visuals, 1–2 badges max (rest, goalie, injury), better spacing/clarity.
- No new deep-dive content here.

### G. Stability & Ingest Hardening
- Anti-stale checks, timestamp validation, silent failure protection, retry logic.
- Validate completeness of JSON artifacts; improve robustness of ingest pipeline.

## 3) Explicit Non-Inclusions for v7
- Explainability chips on predictions; matchup deep-dive pages; player analytics; player props; Power Index charts beyond v2; team hub pages; market comparison; simulation of playoff series; rink effects; ensemble models; past slate archive; goalie page; special teams dashboard; all other large analytics engines.

## 4) Optional v7.1 Patch Goals
- Goalie Page MVP (starters + rest + basic GSAx).
- Past Slate Archive (recent days).
- Additional trend indicators for Power Index.
- Minor visual upgrades.

## 5) Technical Requirements & Data Outputs
- New/updated JSON:
  - Season simulations JSON: playoff/division/conference/Cup % per team, lastUpdated, simCount, optional trend deltas.
  - Power Index JSON v2: rank, score, movement, explainability text, factor snippets (recent form, special teams, injuries, shot quality, SOS).
  - Performance JSON: 7-day accuracy, season accuracy, recent hits/misses list, calibration/reliability points, lastModelUpdate.
- Schema updates:
  - Sim schema: `{ teamAbbrev, playoffPct, divisionPct, conferencePct, cupPct?, movement?, lastUpdated, simCount }`.
  - Power schema: `{ teamAbbrev, rank, score, movement, explainText, factors: { form, specialTeams, injuries, shotQuality, sos }, lastUpdated }`.
  - Performance schema: `{ sevenDayAccuracy, seasonAccuracy, hits: [...], misses: [...], calibration: [...], lastModelUpdate }`.
- Ingest/validation:
  - Enforce generatedAt/lastUpdated timestamps; anti-stale checks; completeness validation on JSON keys.
  - Model metadata updated post-retrain (feature list, C, calibration status, training window).

## 6) UI/UX Summary for Affected Pages
- `/season`: table of teams with probability bars (playoff/division/conference/Cup), optional trend arrows, last updated stamp.
- `/power`: ranked list with movement arrows, 1–2 sentence explainability, factor chips (form, special teams, injuries, shot quality, SOS), clean layout.
- `/performance`: cards for 7-day and season accuracy, list of recent hits/misses (20–30 games), one calibration/reliability chart, last model update.
- `/predictions`: cleaner cards, updated timestamp, refined bars, max 1–2 badges (rest/goalie/injury), no explainability chips.

## 7) Testing & Validation Plan
- Model: accuracy checks (7-day, season), calibration sanity post-retrain.
- Simulations: probability sanity (sums, monotonicity), spot-check deltas after reruns.
- Goalie pipeline: starter detection, rest/confirmation badges present, feature injection confirmed.
- JSON freshness/completeness: generatedAt/lastUpdated checks; schema validation for simulations, power, performance, predictions.
- UI: snapshot/visual checks on `/season`, `/power`, `/performance`, `/predictions`.

## 8) Release Notes / Patch Notes (Human-Readable)
- Added daily season simulations with playoff/division/conference/Cup odds and trend-aware `/season` page.
- Refreshed Power Index with movement arrows and concise explainability at `/power`.
- New `/performance` page with recent accuracy, calibration glimpse, and hits/misses.
- Starting goalie pipeline now injects rest and confirmation, with badges on the slate.
- Model v7 retrain with injury gap, special teams diff, goalie rest, rolling xG/shot share, home/away splits, travel adjustment; re-calibrated.
- Predictions page cleanup: lean cards, updated timestamp, limited badges.
- Stability pass: anti-stale checks, retries, and JSON validation across ingest/export.
