#!/usr/bin/env bash
set -euo pipefail

# Fast path: generate predictions + validate + archive + site metrics

python predict_fast.py
python scripts/validate_predictions.py web/src/data/todaysPredictions.json
python scripts/archive_predictions.py --date "$(date +%Y-%m-%d)" || true
python scripts/generate_site_metrics.py || true
python scripts/refresh_site_data.py || true

echo "✅ Daily run complete"
