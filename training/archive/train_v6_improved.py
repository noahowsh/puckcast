"""
Train improved V6.0 model with 6 seasons + optimal hyperparameters.
Goal: Improve 55.97% current season performance to 58-60%+
"""
import pandas as pd
import numpy as np
from src.nhl_prediction.pipeline import build_dataset
from src.nhl_prediction.model import create_baseline_model, fit_model, predict_probabilities, compute_metrics
from src.nhl_prediction.train import compute_season_weights
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
import pickle
from datetime import datetime

print("=" * 80)
print("PUCKCAST V6.0 - IMPROVED MODEL TRAINING")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# ============================================================================
# CONFIGURATION - V6.0 IMPROVEMENTS
# ============================================================================
print("🔧 Configuration:")
print("   Training data: 6 seasons (2018-2024) - DOUBLED from 3 seasons")
print("   Test data: 2025-26 season (current)")
print("   Hyperparameters: C=1.0, decay=1.0 (optimal from tuning)")
print("   Expected gain: +2-4pp accuracy")
print()

# Define seasons
TRAIN_SEASONS = [
    "20182019",  # ← NEW
    "20192020",  # ← NEW
    "20202021",  # ← NEW
    "20212022",
    "20222023",
    "20232024",
    "20242025"
]
TEST_SEASON = "20252026"

# Optimal hyperparameters (from hyperparameter_tuning.py results)
OPTIMAL_C = 1.0
OPTIMAL_DECAY = 1.0  # No sample decay - all seasons weighted equally

print("=" * 80)
print("[1/5] Loading data...")
print("=" * 80)

all_seasons = TRAIN_SEASONS + [TEST_SEASON]
print(f"Fetching {len(all_seasons)} seasons from NHL API...")
dataset = build_dataset(all_seasons)

print(f"✓ Loaded {len(dataset.games)} total games")
print()

# ============================================================================
# SPLIT DATA
# ============================================================================
print("=" * 80)
print("[2/5] Preparing train/test split...")
print("=" * 80)

train_mask = dataset.games["seasonId"].isin(TRAIN_SEASONS)
test_mask = dataset.games["seasonId"] == TEST_SEASON

print(f"Training games: {train_mask.sum()} ({len(TRAIN_SEASONS)} seasons)")
print(f"Test games:     {test_mask.sum()} (2025-26 season)")
print()

if test_mask.sum() == 0:
    print("⚠️  No games found for 2025-26 season!")
    exit(0)

# Prepare features
X = dataset.features.fillna(0)
y = dataset.target

# Compute sample weights with optimal decay factor
# Create full-size weight array (zeros for test data, actual weights for training)
print("Computing sample weights...")
train_weights = compute_season_weights(dataset.games[train_mask], TRAIN_SEASONS, decay_factor=OPTIMAL_DECAY)
weights = np.zeros(len(dataset.games))
weights[train_mask] = train_weights
print(f"✓ Sample weights computed (decay={OPTIMAL_DECAY})")
print()

# ============================================================================
# TRAIN MODEL
# ============================================================================
print("=" * 80)
print("[3/5] Training model with optimal hyperparameters...")
print("=" * 80)
print(f"Using Logistic Regression with C={OPTIMAL_C}")
print()

model = create_baseline_model(C=OPTIMAL_C)
model = fit_model(model, X, y, train_mask, sample_weight=weights)

print("✓ Model trained successfully")
print()

# ============================================================================
# EVALUATE ON TRAINING DATA
# ============================================================================
print("=" * 80)
print("[4/5] Evaluating on training data...")
print("=" * 80)

train_probs = predict_probabilities(model, X, train_mask)
train_metrics = compute_metrics(y[train_mask], train_probs)

print(f"Training Accuracy: {train_metrics['accuracy']:.4f}")
print(f"Training ROC-AUC:  {train_metrics['roc_auc']:.4f}")
print(f"Training Log Loss: {train_metrics['log_loss']:.4f}")
print()

# ============================================================================
# EVALUATE ON CURRENT SEASON (2025-26)
# ============================================================================
print("=" * 80)
print("[5/5] Testing on 2025-26 season (CURRENT REAL GAMES)...")
print("=" * 80)

test_probs = predict_probabilities(model, X, test_mask)
test_preds = (test_probs > 0.5).astype(int)
y_test = y[test_mask]

# Calculate metrics
accuracy = accuracy_score(y_test, test_preds)
try:
    roc_auc = roc_auc_score(y_test, test_probs)
    logloss = log_loss(y_test, test_probs)
except:
    roc_auc = None
    logloss = None

# Calculate baseline
home_wins = y_test.sum()
baseline_accuracy = home_wins / len(y_test)

# ============================================================================
# RESULTS
# ============================================================================
print()
print("=" * 80)
print("RESULTS: V6.0 IMPROVED MODEL")
print("=" * 80)
print()

print(f"📊 Games Analyzed: {len(y_test)}")
print(f"🏠 Home Team Wins: {int(home_wins)} ({baseline_accuracy:.1%})")
print(f"✈️  Away Team Wins: {len(y_test) - int(home_wins)} ({1 - baseline_accuracy:.1%})")
print()

print("🎯 MODEL PERFORMANCE:")
print(f"   Accuracy:        {accuracy:.2%}")
print(f"   Baseline:        {baseline_accuracy:.2%}")
print(f"   Edge over Home:  {(accuracy - baseline_accuracy) * 100:+.2f}pp")
print()

if roc_auc:
    print(f"   ROC-AUC:         {roc_auc:.4f}")
if logloss:
    print(f"   Log Loss:        {logloss:.4f}")
print()

# Compare to old baseline (from test_current_season.py)
OLD_ACCURACY = 0.5597
improvement = accuracy - OLD_ACCURACY

print("📈 IMPROVEMENT vs BASELINE:")
print(f"   Old Model (3 seasons):     {OLD_ACCURACY:.2%}")
print(f"   New Model (6 seasons):     {accuracy:.2%}")
print(f"   Improvement:               {improvement * 100:+.2f}pp")
print()

# Show prediction breakdown
correct = (test_preds == y_test.values).sum()
incorrect = len(y_test) - correct

print(f"✅ Correct Predictions:   {correct} / {len(y_test)}")
print(f"❌ Incorrect Predictions: {incorrect} / {len(y_test)}")
print()

# ============================================================================
# SAVE MODEL
# ============================================================================
print("=" * 80)
print("Saving model...")
print("=" * 80)

model_filename = "model_v6_6seasons.pkl"
with open(model_filename, 'wb') as f:
    pickle.dump(model, f)

print(f"✓ Model saved to: {model_filename}")
print()

# Save results
results = {
    'train_seasons': TRAIN_SEASONS,
    'test_season': TEST_SEASON,
    'hyperparameters': {'C': OPTIMAL_C, 'decay': OPTIMAL_DECAY},
    'test_accuracy': accuracy,
    'test_roc_auc': roc_auc,
    'test_log_loss': logloss,
    'baseline_accuracy': baseline_accuracy,
    'edge_over_baseline': accuracy - baseline_accuracy,
    'improvement_vs_old': improvement,
    'correct_predictions': int(correct),
    'total_games': len(y_test),
    'trained_at': datetime.now().isoformat()
}

results_df = pd.DataFrame([results])
results_df.to_csv('v6_training_results.csv', index=False)
print("✓ Results saved to: v6_training_results.csv")
print()

# ============================================================================
# FEATURE IMPORTANCE (Top 20)
# ============================================================================
print("=" * 80)
print("TOP 20 FEATURE IMPORTANCE")
print("=" * 80)

# Get feature importance
from src.nhl_prediction.model import compute_feature_effects

importance_df = compute_feature_effects(model, X.columns)
top_20 = importance_df.head(20)

print()
for idx, row in top_20.iterrows():
    print(f"{idx+1:2d}. {row['feature']:40s} {row['absolute_importance']:.6f}")

# Save full importance
importance_df.to_csv('v6_feature_importance.csv', index=False)
print()
print(f"✓ Full feature importance saved to: v6_feature_importance.csv")
print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 80)
print("TRAINING COMPLETE!")
print("=" * 80)
print()
print("Summary:")
print(f"  • Trained on {len(TRAIN_SEASONS)} seasons ({train_mask.sum()} games)")
print(f"  • Tested on {len(y_test)} games from 2025-26 season")
print(f"  • Achieved {accuracy:.2%} accuracy ({improvement * 100:+.2f}pp vs old model)")
print(f"  • Edge over baseline: {(accuracy - baseline_accuracy) * 100:+.2f}pp")
print()

if accuracy > OLD_ACCURACY:
    print("✅ SUCCESS! Improved model performance with 6 seasons + optimal hyperparameters")
elif accuracy == OLD_ACCURACY:
    print("➡️  No change. May need additional improvements (H2H features, more data, etc.)")
else:
    print("❌ Performance decreased. May need to investigate further.")
print()

print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
