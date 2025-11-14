# Puckcast Native Data Pipeline

This package houses the new ingestion + feature engineering workflow that will eventually replace the MoneyPuck CSV dependency. It intentionally lives in its own module so we can iterate quickly without touching the current production scripts.

## Layout

```
data_pipeline/
├── config.py           # Shared paths + runtime knobs
├── ingest/
│   ├── base.py         # Abstract interface for ingestors
│   └── gamecenter.py   # GameCenter (play-by-play) collector
└── storage/
    └── __init__.py     # Write/read helpers (filesystem, Postgres, S3, ...)
```

## Guiding Principles

1. **Keep production stable** – all new work happens here; existing scripts continue to read `data/moneypuck_all_games.csv` until the cutover.
2. **Document every feature** – the final feature dictionary will live in `docs/features.md` so ops/partners know how each metric is derived.
3. **Composable steps** – ingestion, transformation, and export should be callable independently (e.g., backfill vs nightly incremental).

## Next Steps

- Flesh out `ingest/gamecenter.py` to pull GameCenter play-by-play JSON + store raw/parsed shots/events.
- Add shift chart + roster collectors next.
- Wire feature engineering notebooks/scripts to read from `storage` helpers.
