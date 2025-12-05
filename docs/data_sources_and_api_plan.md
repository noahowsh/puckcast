# Data Sources & NHL API Integration Plan

This document inventories every dataset currently powering the NHL prediction system and lays out a concrete plan for weaving the NHL Web API (v1), NHL Stats REST, and the Legacy Stats API into the existing MoneyPuck-centric workflow.

## 1. Current Data Inventory

### 1.1 Historical and training assets

| Dataset | Location | Source | Grain | Key fields/features | Consumed by |
| --- | --- | --- | --- | --- | --- |
| MoneyPuck all games | `data/moneypuck_all_games.csv` | MoneyPuck public export | Team-game rows (one per team per game) | Goals, shots, shot attempts, xG, high-danger splits, Corsi/Fenwick, score context, special-teams opportunities | `src/nhl_prediction/data_ingest.py` -> `engineer_team_features` -> `pipeline.build_dataset` |
| MoneyPuck goalie tables | `data/moneypuck_goalies*.csv` | MoneyPuck | Goalie-season | Save %, GSAx, shot-quality splits | (Currently unused; superseded by `team_goaltending.csv`) |
| Team goaltending aggregates | `data/team_goaltending.csv` | Custom/prepared CSV | Team-season | `team_save_pct`, `team_gsax_per_60` derived from MoneyPuck goalie data | `_add_goaltending_metrics` merges into MoneyPuck logs to seed goaltending features |
| NHL team metadata | `data/nhl_teams.csv` | NHL Stats directory snapshot | Static team info | `teamId`, `triCode`, names, division/conference, site URLs | Mapping IDs <-> abbreviations, dashboard display (`add_team_ids`, scripts, dashboards) |
| Historical predictions, feature importances | `reports/*.csv` | Model outputs | Game or feature row | Model probabilities, correctness, feature coefficients | Dashboard/site insights via `scripts/generate_site_metrics.py` |

### 1.2 Real-time feeds already wired up

| Endpoint | Wrapper | Purpose today | Notes |
| --- | --- | --- | --- |
| `https://api-web.nhle.com/v1/schedule/{YYYY-MM-DD}` | `fetch_schedule` / `fetch_future_games` | Pull daily schedule metadata for dashboards and `predict_full.py` | Only metadata (teams, start time, venue); no stats |
| `https://api.nhle.com/stats/rest/en/team/summary` | `fetch_team_special_teams`, `scripts/fetch_current_standings.py` | Season-to-date PP/PK %, standings card on the Next.js site | Cumulative stats for **current** season only; not used inside model training |
| `https://api-web.nhle.com/v1/gamecenter/{gameId}/landing` | `fetch_starting_goalies` | Optional pre-game goalie confirmation | Limited to publicly announced starters shortly before puck drop |

## 2. Gaps and opportunities

- **Historical dependency on MoneyPuck CSVs.** We rely on local exports that need manual refreshes and lag at least one day; there is no automated pull for new seasons.
- **No event-level ingestion.** MoneyPuck supplies xG and high-danger tags, but we cannot recompute or extend those metrics without native play-by-play.
- **Real-time feature debt.** `predict_full.py` trains on historical MoneyPuck data but does not assemble day-of features for future games (the script grabs the latest existing game rows instead of computing upcoming matchups).
- **Limited roster/context awareness.** Starting goalies are an optional call; we do not fetch lines, scratches, injuries, rest/travel, or shift data directly from the NHL APIs.
- **Redundant/fallback coverage.** If Web v1 endpoints change, we have no legacy API fallback even though it exposes similar schedule/game feeds.

## 3. Integration strategy

### 3.1 NHL Web API (v1) & Gamecenter payloads

**Purpose:** Highest-fidelity event stream (shots, goals, penalties) plus boxscore, rosters, team schedules, and standings.

| Target endpoint | Data grain | Why we want it | Integration plan |
| --- | --- | --- | --- |
| `/v1/gamecenter/{gameId}/play-by-play` | Event-level | Raw shots/goals with x/y, shot type, strength state, rush/rebound flags, faceoffs, penalties, stoppages | New module `src/nhl_prediction/data_sources/gamecenter.py` to fetch & cache JSON (e.g., `data/raw/web_v1/{season}/{gameId}_pbp.json`). Build transformation to compute our own xG/GSAx, possession streaks, and live win-probability targets. |
| `/v1/gamecenter/{gameId}/boxscore` | Game-level lineup & TOI | Lines, TOI splits, goalie usage | Persist alongside PBP to label on-ice combinations and confirm starters; feed into new features for average TOI, line continuity, and special teams usage. |
| `/v1/club-schedule-season/{team}/{season}` | Team schedule | Rest days, travel, B2B flags | Replace manual rest heuristics with official schedule metadata (including venue/time). Enables travel distance + time-zone features when combined with `nhl_teams.csv` coordinates. |
| `/v1/roster/{team}/current` (or `/season`) | Player bios | Height, weight, handedness, DOB | Build roster cache to derive age on game day, handedness matchups, and goalie catch hands for xG features. |
| `/v1/standings/{season}` | League table | Seed elo priors / dashboards | Automate Elo and baseline prior updates at season start. |

**Implementation notes:**

1. **Fetcher layer:** Add rate-limited helpers and optional disk caching (ETag/Last-Modified) so we can re-run training offline.
2. **Schema normalization:** Convert Web v1 coordinates to rink-adjusted space (standardize to offensive zone) for xG modeling.
3. **Derived outputs:** Build `pandas` pipelines that transform stored JSON into:
   - Shot feature matrix (distance, angle, pre-shot movement, manpower state).
   - Goalie outcome table (for GSAx training labels).
   - Game context table (rest, travel, start time).
4. **Model hooks:** Extend `data_ingest` to optionally pull Web v1 derived tables instead of MoneyPuck when available, enabling self-maintained xG features.

### 3.2 NHL Stats REST (`https://api.nhle.com/stats/rest/en/...`)

**Purpose:** Season/per-game aggregates, leaders, shift charts, and discoverable schemas via `/config`.

| Report/endpoint | Data grain | Key additions | Plan |
| --- | --- | --- | --- |
| `/stats/rest/en/config` | Metadata | Lists every report ID and column definition | Auto-generate typed clients per report; keeps code resilient to schema drift. |
| `/stats/rest/en/team/summary?cayenneExp=seasonId=... and gameTypeId=2` | Team-season | Goals/shots per game, PP/PK, faceoff %, possession splits | Replace manual CSV updates; store nightly snapshots for time-aware training features. |
| `/stats/rest/en/skater/realtime` & `/goalie/summary` | Player-season / per-game | Individual xG proxies, shooting %, goalie splits by strength | Build pre-game matchup context: recent linemate production, on-ice shooting differentials, probable starter form. |
| `/stats/rest/en/shiftcharts?cayenneExp=gameId=...` | Shift segment | Exact on-ice combinations | Merge with PBP to know attackers/defenders for each event, enabling RAPM-style features and fatigue tracking. |
| `/stats/rest/en/players` directory | Reference | IDs, handedness, bios | Backfill roster data & ensure consistent IDs across APIs. |

**Implementation notes:**

1. Write `src/nhl_prediction/data_sources/stats_rest.py` with general `fetch_report(report, params)` and helper builders (team summary, goalie summary, shift charts).
2. Persist raw responses under `data/raw/stats_rest/{report}/{season}/...json` for reproducibility.
3. Introduce a nightly job (GitHub Action or cron) that refreshes team/skater/goalie summaries so the dashboard and model always see up-to-date cumulative stats.
4. Extend `engineer_team_features` to optionally source rolling windows from Stats REST aggregates when MoneyPuck (xG) is unavailable - e.g., compute rolling shot differential from per-game logs, integrate PP/PK matchup indices, goalie form metrics.

### 3.3 Legacy Stats API (`https://statsapi.web.nhl.com/api/v1/...`)

**Purpose:** Battle-tested schedule/teams/game feed used widely in the community; serves as stability fallback and supplemental data (venues, broadcasts, live feed).

| Endpoint | Usage | Integration idea |
| --- | --- | --- |
| `/api/v1/schedule` | Alternate schedule feed | Use as backup when Web v1 schedule fails; compare payloads in monitoring job to detect upstream changes. |
| `/api/v1/game/{gamePk}/feed/live` | Alternate PBP | Cross-check Web v1 play-by-play for validation; use when new events appear there first. |
| `/api/v1/teams`, `/divisions`, `/conferences` | Reference data | Automate `nhl_teams.csv` regeneration instead of manual CSV edits. |

Implementation-wise, add a lightweight `legacy_api.py` with the same interface as `nhl_api` so higher-level code can swap between sources without refactors.

## 4. Implementation roadmap

1. **Data-access layer (week 1):** Create new client modules (`data_sources/gamecenter.py`, `data_sources/stats_rest.py`, `data_sources/legacy_api.py`) with rate limiting, retries, and optional caching. Add unit tests that hit sample JSON fixtures in `tests/data`.
2. **Storage & versioning (week 1-2):** Define a `data/raw/{source}/` hierarchy plus ingestion scripts (`scripts/pull_gamecenter.py`, `scripts/pull_stats_rest.py`) that can backfill seasons and refresh daily snapshots.
3. **Feature parity (week 2-3):** Build transformers that replicate MoneyPuck-derived features from the newly ingested data (xG model, rolling aggregates, rest/travel). Validate by comparing against existing MoneyPuck-based feature matrices for overlapping seasons.
4. **Model wiring (week 3):** Update `build_dataset` to accept a flag selecting MoneyPuck vs. NHL API data, and ensure `predict_full.py` constructs pre-game feature rows for future matchups using the new aggregated tables plus current rosters/goalies.
5. **Monitoring & fallbacks (ongoing):** Add health checks that compare Web v1 vs. Legacy schedule counts and Stats REST schema hashes; alert when upstream changes occur.

## 5. Immediate next steps

1. Prototype `gamecenter` ingestion for a single recent game (store both PBP and boxscore).
2. Generate a nightly Stats REST team summary snapshot and feed it into the dashboard standings card (replace the manual `scripts/fetch_current_standings.py` run).
3. Spike an xG model using Web v1 PBP to ensure we can reproduce MoneyPuck-like shot values before fully migrating training data.

This roadmap keeps the current MoneyPuck-powered model running while gradually layering in official NHL data feeds, opening the door to richer features and faster updates once the new ingestion pieces are in place.

## 6. Historical Data Expansion

### Available Historical Seasons

The NHL Web API (`api-web.nhle.com/v1`) supports play-by-play data going back to the **2017-18 season**. This means we can expand the training dataset significantly beyond the current 2021-22 to 2023-24 range.

| Season | API Support | Game Count | Notes |
|--------|-------------|------------|-------|
| 2017-18 | ✅ Full | ~1,271 | First season with 31 teams (VGK expansion) |
| 2018-19 | ✅ Full | ~1,271 | Full 82-game season |
| 2019-20 | ✅ Partial | ~1,082 | COVID-shortened - regular season paused March 11, 2020 |
| 2020-21 | ✅ Full | ~868 | COVID-shortened 56-game season, all-division schedule |
| 2021-22 | ✅ Full | ~1,312 | Full 82-game season, 32 teams (SEA expansion) |
| 2022-23 | ✅ Full | ~1,312 | Full 82-game season |
| 2023-24 | ✅ Full | ~1,312 | Full 82-game season |
| 2024-25 | ✅ In Progress | ~1,312 | Current season |

### Fetching Historical Data

Use the `training/fetch_historical_data.py` script to fetch historical seasons:

```bash
# Check what's already cached
python training/fetch_historical_data.py --check

# Fetch all historical seasons (2017-18 to 2020-21)
python training/fetch_historical_data.py

# Fetch a specific season
python training/fetch_historical_data.py --season 20172018
```

### Data Format Compatibility

The NHL API returns identical play-by-play structure for all seasons from 2017-18 onward:
- Shot events with `xCoord`, `yCoord`, `shotType`, `zoneCode`
- Goals, assists, penalties with full detail
- Game state, period info, situation codes (5v5, PP, PK)

This means the existing `native_ingest.py` code works for all historical seasons without modification.

### Season-Specific Considerations

**2019-20 COVID Season**:
- Regular season paused March 11, 2020 after ~68-71 games per team
- Playoffs resumed in August 2020 "bubble" format
- Only pre-pause regular season games are included (playoff bubble not in regular season data)

**2020-21 COVID Season**:
- 56-game shortened season
- All-division schedule (teams only played within their division)
- Canadian teams in separate division due to border restrictions
- May affect divisional feature effectiveness for this season

**Training Strategy with Expanded Data**:

1. **More Training Data**: 2017-18 through 2022-23 (5+ seasons, ~6,200 games)
2. **Holdout Test**: 2023-24 season (consistent with current methodology)
3. **Expected Impact**: More data typically improves model stability, may reduce variance in predictions
