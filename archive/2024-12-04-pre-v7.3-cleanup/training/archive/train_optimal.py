"""
Train model with optimal hyperparameters to achieve ~60.24% accuracy.
Uses ONLY NHL API data (no MoneyPuck).
"""
import sys
import pickle
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from nhl_prediction.pipeline import build_dataset
from nhl_prediction.model import create_baseline_model, fit_model, predict_probabilities, compute_metrics
from nhl_prediction.train import compute_season_weights
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss

print("=" * 80)
print("PUCKCAST - OPTIMAL MODEL TRAINING")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Optimal configuration from hyperparameter tuning
TRAIN_SEASONS = ["20212022", "20222023"]
TEST_SEASON = "20232024"
OPTIMAL_C = 1.0
OPTIMAL_DECAY = 1.0
MODEL_OUTPUT = Path("model_v6_6seasons.pkl")
PREDICTIONS_OUTPUT = Path("reports/predictions_20232024.csv")

print("🔧 Configuration:")
print(f"   Training seasons: {TRAIN_SEASONS}")
print(f"   Test season: {TEST_SEASON}")
print(f"   C (regularization): {OPTIMAL_C}")
print(f"   Decay factor: {OPTIMAL_DECAY}")
print(f"   Expected accuracy: ~60.24%")
print()

# Load data (from NHL API only)
print("=" * 80)
print("[1/5] Loading data from NHL API...")
print("=" * 80)

all_seasons = TRAIN_SEASONS + [TEST_SEASON]
print(f"Fetching {len(all_seasons)} seasons: {', '.join(all_seasons)}")
dataset = build_dataset(all_seasons)
print(f"✓ Loaded {len(dataset.games)} total games (NHL API only)")
print()

# Split train/test
print("=" * 80)
print("[2/5] Preparing train/test split...")
print("=" * 80)

train_mask = dataset.games["seasonId"].isin(TRAIN_SEASONS)
test_mask = dataset.games["seasonId"] == TEST_SEASON

print(f"Training games: {train_mask.sum()}")
print(f"Test games: {test_mask.sum()}")
print()

# Prepare features
X = dataset.features.fillna(0)
y = dataset.target

# Compute sample weights
print("Computing sample weights (decay={})...".format(OPTIMAL_DECAY))
train_weights = compute_season_weights(dataset.games[train_mask], TRAIN_SEASONS, decay_factor=OPTIMAL_DECAY)
weights = np.zeros(len(dataset.games))
weights[train_mask] = train_weights
print("✓ Sample weights computed")
print()

# Train model
print("=" * 80)
print("[3/5] Training Logistic Regression model...")
print("=" * 80)
print(f"Using C={OPTIMAL_C}, decay={OPTIMAL_DECAY}")
print()

model = create_baseline_model(C=OPTIMAL_C)
model = fit_model(model, X, y, train_mask, sample_weight=weights)
print("✓ Model trained successfully")
print()

# Evaluate on test set
print("=" * 80)
print("[4/5] Evaluating on test set (2023-24 season)...")
print("=" * 80)

test_probs = predict_probabilities(model, X, test_mask)
test_preds = (test_probs > 0.5).astype(int)
y_test = y[test_mask]

# Calculate metrics
accuracy = accuracy_score(y_test, test_preds)
roc_auc = roc_auc_score(y_test, test_probs)
logloss = log_loss(y_test, test_probs)

# Baseline
home_wins = y_test.sum()
baseline_accuracy = home_wins / len(y_test)

print(f"Test Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)")
print(f"Test ROC-AUC:   {roc_auc:.4f}")
print(f"Test Log Loss:  {logloss:.4f}")
print(f"Baseline (home):{baseline_accuracy:.4f} ({baseline_accuracy*100:.2f}%)")
print(f"Improvement:    +{(accuracy-baseline_accuracy)*100:.2f}pp")
print()

# Save predictions
print("=" * 80)
print("[5/5] Saving results...")
print("=" * 80)

# Build predictions dataframe
test_games_df = dataset.games[test_mask].copy()
test_games_df["home_win_probability"] = test_probs
test_games_df["predicted_home_win"] = test_preds
test_games_df["home_win"] = y_test.values
test_games_df["correct"] = (test_preds == y_test).astype(int)

# Save predictions CSV
PREDICTIONS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
test_games_df.to_csv(PREDICTIONS_OUTPUT, index=False)
print(f"✓ Saved predictions to: {PREDICTIONS_OUTPUT}")
print(f"  Total predictions: {len(test_games_df)}")
print(f"  Accuracy: {accuracy:.4f}")
print()

# Save model
with open(MODEL_OUTPUT, "wb") as f:
    pickle.dump(model, f)
print(f"✓ Saved model to: {MODEL_OUTPUT}")
print()

# Summary
print("=" * 80)
print("SUCCESS! RESULTS SUMMARY")
print("=" * 80)
print(f"✓ Model trained with optimal hyperparameters")
print(f"✓ Test Accuracy: {accuracy*100:.2f}%")
print(f"✓ Data source: NHL API only (no MoneyPuck)")
print(f"✓ Predictions saved: {PREDICTIONS_OUTPUT}")
print(f"✓ Model saved: {MODEL_OUTPUT}")
print()
print("Next steps:")
print("  1. python scripts/generate_site_metrics.py")
print("  2. Commit and push to deploy")
print("=" * 80)
