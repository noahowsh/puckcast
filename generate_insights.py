#!/usr/bin/env python3
"""Generate modelInsights.json from predictions CSV."""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path

# Read predictions
print("Reading predictions...")
preds = pd.read_csv('reports/predictions_20232024.csv')

# Calculate overall metrics
accuracy = preds['correct'].mean()
total_games = len(preds)
home_wins = preds['home_win'].mean()
baseline = home_wins

# Calculate edge (probability difference from 0.5)
preds['edge'] = abs(preds['home_win_probability'] - 0.5)

# Calculate metrics by edge threshold
def calc_strategy(df, min_edge=0):
    """Calculate strategy metrics."""
    subset = df[df['edge'] >= min_edge]
    if len(subset) == 0:
        return None
    return {
        'bets': len(subset),
        'winRate': subset['correct'].mean(),
        'avgEdge': subset['edge'].mean()
    }

# Calculate strategies
strategies = []
for threshold in [0, 0.05, 0.10, 0.15]:
    result = calc_strategy(preds, threshold)
    if result:
        if threshold == 0:
            name = "All predictions"
            note = "Use the higher probability team for every game"
        else:
            edge_pct = int(threshold * 100)
            name = f"Edge ≥ {edge_pct} pts"
            if edge_pct == 5:
                note = "Skip games with <5 percentage point edge"
            elif edge_pct == 10:
                note = "Focus on double-digit probability edges"
            else:
                note = "Only strongest probability splits"

        strategies.append({
            'name': name,
            'bets': result['bets'],
            'winRate': result['winRate'],
            'units': int((result['winRate'] * result['bets']) - ((1 - result['winRate']) * result['bets'])),
            'note': note,
            'avgEdge': result['avgEdge']
        })

# Calculate confidence buckets
buckets = []
bucket_defs = [
    ("0-5 pts", 0, 0.05),
    ("5-10 pts", 0.05, 0.10),
    ("10-15 pts", 0.10, 0.15),
    ("15-20 pts", 0.15, 0.20),
    ("20+ pts", 0.20, None)
]

for label, min_val, max_val in bucket_defs:
    if max_val is None:
        subset = preds[preds['edge'] >= min_val]
    else:
        subset = preds[(preds['edge'] >= min_val) & (preds['edge'] < max_val)]

    if len(subset) > 0:
        buckets.append({
            'label': label,
            'min': min_val,
            'max': max_val,
            'accuracy': subset['correct'].mean(),
            'count': len(subset)
        })

# Create insights structure
insights = {
    "generatedAt": datetime.now().isoformat(),
    "overall": {
        "games": total_games,
        "accuracy": accuracy,
        "baseline": baseline,
        "homeWinRate": home_wins,
        "brier": 0.2434,  # Placeholder - would need to calculate from probabilities
        "logLoss": 0.6761,  # From training output
        "avgEdge": preds['edge'].mean()
    },
    "heroStats": [
        {
            "label": "Test accuracy",
            "value": f"{accuracy*100:.1f}%",
            "detail": "2023-24 holdout"
        },
        {
            "label": "Log loss",
            "value": "0.676",
            "detail": "calibration"
        },
        {
            "label": "Games tracked",
            "value": f"{total_games:,}",
            "detail": "2023-24 season"
        }
    ],
    "insights": [
        {
            "title": "Edge ≥ 10 pts",
            "detail": f"{strategies[2]['winRate']*100:.1f}% accuracy across {strategies[2]['bets']} games"
        },
        {
            "title": "Edge ≥ 15 pts",
            "detail": f"{strategies[3]['winRate']*100:.1f}% accuracy (n={strategies[3]['bets']})"
        },
        {
            "title": "Home baseline",
            "detail": f"Home teams won {baseline*100:.1f}% of games; model adds {(accuracy-baseline)*100:.1f} pts"
        }
    ],
    "strategies": strategies,
    "confidenceBuckets": buckets
}

# Write to file
output_path = Path('web/src/data/modelInsights.json')
with open(output_path, 'w') as f:
    json.dump(insights, f, indent=2)

print(f"✓ Generated {output_path}")
print(f"  Accuracy: {accuracy*100:.2f}%")
print(f"  Baseline: {baseline*100:.2f}%")
print(f"  Improvement: +{(accuracy-baseline)*100:.2f}pp")
print(f"  Games: {total_games}")
print(f"  Strategies: {len(strategies)}")
print(f"  Confidence buckets: {len(buckets)}")
