#!/usr/bin/env python3
"""
Comprehensive Model Evaluation - NHL API Only
Generates detailed statistics with confidence bucket analysis.
"""
import sys
import pickle
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from nhl_prediction.pipeline import build_dataset
from nhl_prediction.model import create_baseline_model, fit_model, predict_probabilities
from nhl_prediction.train import compute_season_weights
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss, brier_score_loss
from sklearn.calibration import calibration_curve

print("=" * 80)
print("COMPREHENSIVE MODEL EVALUATION - NHL API ONLY")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Configuration
TRAIN_SEASONS = ["20212022", "20222023"]
TEST_SEASON = "20232024"
OPTIMAL_C = 1.0
OPTIMAL_DECAY = 1.0

print("🔧 Configuration:")
print(f"   Training seasons: {TRAIN_SEASONS}")
print(f"   Test season: {TEST_SEASON}")
print(f"   C (regularization): {OPTIMAL_C}")
print(f"   Decay factor: {OPTIMAL_DECAY}")
print()

# ============================================================================
# STEP 1: Load Data
# ============================================================================
print("=" * 80)
print("[1/6] Loading data from NHL API...")
print("=" * 80)

all_seasons = TRAIN_SEASONS + [TEST_SEASON]
print(f"Fetching {len(all_seasons)} seasons: {', '.join(all_seasons)}")
dataset = build_dataset(all_seasons)
print(f"✓ Loaded {len(dataset.games)} total games")
print(f"✓ Features: {len(dataset.features.columns)} columns")
print()

# ============================================================================
# STEP 2: Prepare Train/Test Split
# ============================================================================
print("=" * 80)
print("[2/6] Preparing train/test split...")
print("=" * 80)

train_mask = dataset.games["seasonId"].isin(TRAIN_SEASONS)
test_mask = dataset.games["seasonId"] == TEST_SEASON

X = dataset.features.fillna(0)
y = dataset.target

X_train, y_train = X[train_mask], y[train_mask]
X_test, y_test = X[test_mask], y[test_mask]

print(f"Training games: {train_mask.sum()}")
print(f"Test games: {test_mask.sum()}")
print(f"Home team wins (train): {y_train.mean():.1%}")
print(f"Home team wins (test): {y_test.mean():.1%}")
print()

# Compute sample weights
train_weights = compute_season_weights(dataset.games[train_mask], TRAIN_SEASONS, decay_factor=OPTIMAL_DECAY)
print(f"✓ Sample weights computed (decay={OPTIMAL_DECAY})")
print()

# ============================================================================
# STEP 3: Train Model
# ============================================================================
print("=" * 80)
print("[3/6] Training Logistic Regression model...")
print("=" * 80)

model = create_baseline_model(C=OPTIMAL_C, random_state=42)
training_mask = pd.Series(True, index=X_train.index)
model = fit_model(model, X_train, y_train, training_mask, sample_weight=train_weights)

print(f"✓ Model trained successfully")
print(f"   Model type: {type(model).__name__}")
print(f"   Features used: {len(X_train.columns)}")
print()

# ============================================================================
# STEP 4: Generate Predictions
# ============================================================================
print("=" * 80)
print("[4/6] Generating predictions...")
print("=" * 80)

# Train set predictions
train_mask_pred = pd.Series(True, index=X_train.index)
y_train_pred_proba = predict_probabilities(model, X_train, train_mask_pred)
y_train_pred = (y_train_pred_proba >= 0.5).astype(int)

# Test set predictions
test_mask_pred = pd.Series(True, index=X_test.index)
y_test_pred_proba = predict_probabilities(model, X_test, test_mask_pred)
y_test_pred = (y_test_pred_proba >= 0.5).astype(int)

print(f"✓ Predictions generated")
print()

# ============================================================================
# STEP 5: Calculate Metrics
# ============================================================================
print("=" * 80)
print("[5/6] Calculating performance metrics...")
print("=" * 80)

# Overall metrics
train_acc = accuracy_score(y_train, y_train_pred)
test_acc = accuracy_score(y_test, y_test_pred)
train_roc = roc_auc_score(y_train, y_train_pred_proba)
test_roc = roc_auc_score(y_test, y_test_pred_proba)
train_logloss = log_loss(y_train, y_train_pred_proba)
test_logloss = log_loss(y_test, y_test_pred_proba)
train_brier = brier_score_loss(y_train, y_train_pred_proba)
test_brier = brier_score_loss(y_test, y_test_pred_proba)

# Baseline (always pick home team)
baseline_acc = y_test.mean()

print("\n📊 OVERALL PERFORMANCE")
print("=" * 80)
print(f"{'Metric':<25} {'Train':<15} {'Test':<15} {'Baseline':<15}")
print("-" * 80)
print(f"{'Accuracy':<25} {train_acc:>14.2%} {test_acc:>14.2%} {baseline_acc:>14.2%}")
print(f"{'ROC-AUC':<25} {train_roc:>14.4f} {test_roc:>14.4f} {'0.5000':>15}")
print(f"{'Log Loss':<25} {train_logloss:>14.4f} {test_logloss:>14.4f} {'-':>15}")
print(f"{'Brier Score':<25} {train_brier:>14.4f} {test_brier:>14.4f} {'-':>15}")
print(f"{'Improvement vs Baseline':<25} {train_acc - y_train.mean():>+13.2%} {test_acc - baseline_acc:>+13.2%} {'-':>15}")
print()

# ============================================================================
# STEP 6: Confidence Bucket Analysis
# ============================================================================
print("=" * 80)
print("[6/6] Analyzing confidence buckets...")
print("=" * 80)

def assign_confidence_grade(prob, threshold=0.5):
    """Assign confidence grade based on probability distance from 0.5"""
    edge = abs(prob - threshold)
    edge_pct = edge * 100

    if edge_pct >= 20:
        return "A+"
    elif edge_pct >= 17:
        return "A"
    elif edge_pct >= 14:
        return "A-"
    elif edge_pct >= 10:
        return "B+"
    elif edge_pct >= 7:
        return "B"
    elif edge_pct >= 4:
        return "B-"
    elif edge_pct >= 2:
        return "C+"
    else:
        return "C"

def get_predicted_winner(prob):
    """Get predicted winner (1=Home, 0=Away)"""
    return 1 if prob >= 0.5 else 0

# Assign grades to test predictions
test_results = pd.DataFrame({
    'actual': y_test.values,
    'prob_home': y_test_pred_proba,
    'predicted': y_test_pred,
    'grade': [assign_confidence_grade(p) for p in y_test_pred_proba],
    'edge': abs(y_test_pred_proba - 0.5) * 100
})

# Calculate bucket statistics
bucket_stats = []
grade_order = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C"]

for grade in grade_order:
    grade_mask = test_results['grade'] == grade
    if grade_mask.sum() == 0:
        continue

    grade_games = test_results[grade_mask]

    # Calculate accuracy
    correct = (grade_games['actual'] == grade_games['predicted']).sum()
    total = len(grade_games)
    accuracy = correct / total if total > 0 else 0

    # Average edge
    avg_edge = grade_games['edge'].mean()

    # Average probability
    avg_prob = grade_games['prob_home'].mean()

    bucket_stats.append({
        'Grade': grade,
        'Games': total,
        'Correct': correct,
        'Accuracy': accuracy,
        'Avg Edge': avg_edge,
        'Avg Prob': avg_prob
    })

bucket_df = pd.DataFrame(bucket_stats)

print("\n📈 CONFIDENCE BUCKET ANALYSIS (Test Set)")
print("=" * 80)
print(f"{'Grade':<8} {'Games':<8} {'Correct':<10} {'Accuracy':<12} {'Avg Edge':<12} {'Avg Prob':<12}")
print("-" * 80)
for _, row in bucket_df.iterrows():
    print(f"{row['Grade']:<8} {row['Games']:<8} {row['Correct']:<10} "
          f"{row['Accuracy']:>10.2%}  {row['Avg Edge']:>10.1f}%  {row['Accuracy']:>10.2%}")

print()
print(f"Total test games: {len(test_results)}")
print(f"Total correct: {(test_results['actual'] == test_results['predicted']).sum()}")
print()

# ============================================================================
# Probability Calibration Analysis
# ============================================================================
print("=" * 80)
print("CALIBRATION ANALYSIS")
print("=" * 80)

# Bin predictions into 10 buckets
n_bins = 10
fraction_of_positives, mean_predicted_value = calibration_curve(
    y_test, y_test_pred_proba, n_bins=n_bins, strategy='uniform'
)

print(f"\n{'Predicted Prob':<20} {'Actual Freq':<20} {'Count':<15} {'Calibration Error':<20}")
print("-" * 80)

# Group predictions into bins
prob_bins = pd.cut(y_test_pred_proba, bins=n_bins, include_lowest=True)
for i, (pred_prob, actual_freq) in enumerate(zip(mean_predicted_value, fraction_of_positives)):
    bin_mask = prob_bins.cat.codes == i
    count = bin_mask.sum()
    error = abs(pred_prob - actual_freq)
    print(f"{pred_prob:>18.1%}  {actual_freq:>18.1%}  {count:>13}  {error:>18.1%}")

avg_calibration_error = np.mean(np.abs(fraction_of_positives - mean_predicted_value))
print()
print(f"Average Calibration Error: {avg_calibration_error:.4f}")
print()

# ============================================================================
# Summary Statistics
# ============================================================================
print("=" * 80)
print("SUMMARY - NHL API ONLY MODEL")
print("=" * 80)
print()
print("✅ DATA SOURCE:")
print("   - Native NHL API play-by-play ingestion")
print("   - Custom xG model (gradient boosting)")
print("   - NO MoneyPuck dependency")
print()
print("✅ MODEL PERFORMANCE:")
print(f"   - Test Accuracy: {test_acc:.2%} (baseline: {baseline_acc:.2%})")
print(f"   - Improvement: +{(test_acc - baseline_acc)*100:.2f} percentage points")
print(f"   - ROC-AUC: {test_roc:.4f}")
print(f"   - Log Loss: {test_logloss:.4f}")
print(f"   - Brier Score: {test_brier:.4f}")
print()
print("✅ TOP CONFIDENCE PREDICTIONS:")
top_grades = bucket_df[bucket_df['Grade'].isin(['A+', 'A', 'A-'])]
if len(top_grades) > 0:
    top_games = top_grades['Games'].sum()
    top_correct = top_grades['Correct'].sum()
    top_acc = top_correct / top_games if top_games > 0 else 0
    print(f"   - A+/A/A- Grades: {top_games} games, {top_acc:.2%} accuracy")
print()
print("✅ FEATURE COUNT:")
print(f"   - Total engineered features: {len(X.columns)}")
print()
print("=" * 80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Save detailed results
output_file = Path("reports/model_evaluation_comprehensive.csv")
output_file.parent.mkdir(exist_ok=True)

test_results_full = test_results.copy()
test_results_full['correct'] = (test_results_full['actual'] == test_results_full['predicted']).astype(int)
test_results_full.to_csv(output_file, index=False)
print(f"\n💾 Detailed results saved to: {output_file}")

bucket_output = Path("reports/confidence_buckets.csv")
bucket_df.to_csv(bucket_output, index=False)
print(f"💾 Bucket analysis saved to: {bucket_output}")
print()
