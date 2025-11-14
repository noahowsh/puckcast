# Puckcast Native Pipeline Plan

## Goal
Replace the MoneyPuck CSV dependency with a self-owned ingest + feature engineering + model stack that produces richer, more accurate predictions while keeping the current production workflow running until cutover.

Timeline target: **~2 weeks** for the first feature wave (ingestion + core metrics + goalie metrics + documentation). During this period, we continue to ship the existing MoneyPuck-based JSON bundles nightly so the site stays fresh.

## Phase 1 – Ingestion
1. **GameCenter Play-by-Play**
   - Endpoint: `https://api.nhle.com/stats/rest/en/gamecenter/{gameId}/landing`
   - Persist raw JSON for every game (historical backfill + nightly updates).
   - Extract per-event data: x/y coordinates, shot type, shooter, goalie, rebound flag, pre-shot movement, strength state.

2. **Shift Charts + Rosters**
   - Endpoints: `.../shiftcharts`, `.../game/{team}/{date}`.
   - Capture on-ice players, line combinations, TOI, goalie starts/relief appearances.

3. **Schedules / Metadata**
   - Endpoint: `https://api-web.nhle.com/v1/schedule/{date}`.
   - Feed rest/travel calculations (home/road streaks, days rest, time zones).

4. **Storage**
   - Raw JSON to S3/local.
   - Parsed tables to Postgres/Supabase (tables: `games`, `events`, `shifts`, `rosters`).

## Phase 2 – Feature Engineering
1. **Team/Game Features**
   - Re-derive xG/xGA using shot context (distance, angle, shot type, rebound, rush).
   - Build rolling possession metrics (Corsi/Fenwick), special teams efficiency, score-adjusted differentials.
   - Rest/travel features from schedule data (days rest, back-to-back flags, timezone hops).

2. **Goalie Features**
   - Compute GSAx (saves above expected), rebound control, streaks, rest days, opponent context.
   - Produce per-game goalie summaries so we can power `/goalies`, the predictions table, and the model.

3. **Player-Level (foundation for player hub)**
   - On-ice xG contribution, line chemistry, matchup advantages derived from shifts + events.

4. **Documentation**
   - Maintain `docs/features.md`: for each feature include definition, formula, inputs, and caveats.

## Phase 3 – Model Integration
1. Export the new feature set in a format compatible with `predict_full.py` (so we can A/B train without touching production).
2. Run parallel training jobs (MoneyPuck baseline vs Puckcast-native) to compare accuracy/log loss.
3. Iterate until the new model matches or exceeds baseline metrics.

## Phase 4 – Cutover Prep
1. Introduce a managed DB (Supabase/Postgres) to persist predictions, goalie pulse, standings snapshots, etc.
2. Update nightly workflow to write both JSON bundles and DB rows so the front-end + partner APIs have a stable source.
3. Once confidence is high, flip the nightly publish to the new model and retire the MoneyPuck CSV path (keep gz backup until we’re certain).

## Distribution & Growth Add-ons
- Automated X/blog posts after the 6 AM run (highlight top edge, goalie heat check, link back to site).
- API tokens + partner docs once DB is in place.
- Player hub and season projections built on the new data foundation.

## Guardrails
- Never break the existing nightly publish while the new pipeline is in progress (tag important commits, keep JSON bundling in place).
- Document every feature in `docs/features.md` to answer future questions (what it measures, how calculated, any smoothing/rolling windows).
- Use the new `/api/status` + `/ops` page to monitor freshness so we catch ingest failures early.
