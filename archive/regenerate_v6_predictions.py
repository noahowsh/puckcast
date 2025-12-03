"""
Regenerate predictions using V6.0 model on 2023-24 test set.
This should restore the 60.89% accuracy in model insights.
"""
import sys
import pickle
from pathlib import Path
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from nhl_prediction.pipeline import build_dataset
from nhl_prediction.model import predict_probabilities

print("=" * 80)
print("REGENERATING V6.0 MODEL PREDICTIONS")
print("=" * 80)
print()

# Configuration from V2_OPTIMIZATION_RESULTS.md
TRAIN_SEASONS = ["20212022", "20222023"]
TEST_SEASON = "20232024"
MODEL_PATH = Path("model_v6_6seasons.pkl")
OUTPUT_PATH = Path("reports/predictions_20232024.csv")

print(f"Loading model: {MODEL_PATH}")
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)
print(f"✓ Model loaded: {type(model).__name__}")
print()

print(f"Loading dataset (train: {TRAIN_SEASONS}, test: {TEST_SEASON})...")
all_seasons = TRAIN_SEASONS + [TEST_SEASON]
dataset = build_dataset(all_seasons)
print(f"✓ Loaded {len(dataset.games)} games")
print()

# Split into train/test
train_mask = dataset.games["seasonId"].isin(TRAIN_SEASONS)
test_mask = dataset.games["seasonId"] == TEST_SEASON

train_games = train_mask.sum()
test_games = test_mask.sum()

print(f"Training games: {train_games}")
print(f"Test games: {test_games}")
print()

# Get test data
X = dataset.features.fillna(0)
y = dataset.target
test_games_df = dataset.games[test_mask].copy()

# Generate predictions on test set
print("Generating predictions on 2023-24 season...")
test_probs = predict_probabilities(model, X, test_mask)
test_preds = (test_probs > 0.5).astype(int)
y_test = y[test_mask]

# Calculate metrics
correct = (test_preds == y_test).astype(int)
accuracy = correct.mean()

print(f"\n✓ Test Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
print()

# Build predictions dataframe matching expected format
predictions_df = test_games_df.copy()
predictions_df["home_win_probability"] = test_probs
predictions_df["predicted_home_win"] = test_preds
predictions_df["home_win"] = y_test.values
predictions_df["correct"] = correct

# Ensure required columns exist
required_cols = ["gameDate", "id", "teamFullName_home", "teamFullName_away",
                 "home_win", "home_win_probability", "predicted_home_win", "correct"]

# Check which columns we have
available_cols = predictions_df.columns.tolist()
print(f"Available columns: {len(available_cols)}")

# Save predictions
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
predictions_df.to_csv(OUTPUT_PATH, index=False)
print(f"\n✓ Saved predictions to: {OUTPUT_PATH}")
print(f"  Total predictions: {len(predictions_df)}")
print(f"  Accuracy: {accuracy:.4f}")
print()

print("=" * 80)
print("SUCCESS - Now regenerate model insights:")
print("  python scripts/generate_site_metrics.py")
print("=" * 80)
