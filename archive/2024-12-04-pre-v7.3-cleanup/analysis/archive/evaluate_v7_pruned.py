#!/usr/bin/env python3
"""
V7.0 Pruned Feature Evaluation

Trains and evaluates model with 49 zero-coefficient features removed.
Expected: +0.2-0.4% accuracy from reduced overfitting.
"""
import sys
import pickle
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from nhl_prediction.pipeline import build_dataset
from nhl_prediction.model import create_baseline_model, fit_model, predict_probabilities
from nhl_prediction.train import compute_season_weights
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss, brier_score_loss

# Load feature importance to get non-zero features
importance_df = pd.read_csv('reports/v7_feature_importance.csv')
features_to_keep = importance_df[importance_df['abs_importance'] > 0.0]['feature'].tolist()

print("=" * 80)
print("V7.0 PRUNED FEATURE EVALUATION")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Configuration
TRAIN_SEASONS = ["20212022", "20222023"]
TEST_SEASON = "20232024"
OPTIMAL_C = 1.0
OPTIMAL_DECAY = 1.0

print("🔧 Configuration:")
print(f"   Original V7.0 features: 209")
print(f"   Pruned features: {len(features_to_keep)}")
print(f"   Features removed: {209 - len(features_to_keep)}")
print(f"   Training seasons: {TRAIN_SEASONS}")
print(f"   Test season: {TEST_SEASON}")
print()

# Load data
print("=" * 80)
print("[1/6] Loading data...")
print("=" * 80)

dataset = build_dataset(TRAIN_SEASONS + [TEST_SEASON])
print(f"✓ Loaded {len(dataset.games)} games")
print(f"✓ Original features: {len(dataset.features.columns)}")

# Filter to non-zero features
available_features = [f for f in features_to_keep if f in dataset.features.columns]
print(f"✓ Pruned features available: {len(available_features)}")

# Prepare train/test split
print("\n" + "=" * 80)
print("[2/6] Preparing train/test split...")
print("=" * 80)

train_mask = dataset.games["seasonId"].isin(TRAIN_SEASONS)
test_mask = dataset.games["seasonId"] == TEST_SEASON

X = dataset.features[available_features].fillna(0)
y = dataset.target

X_train, y_train = X[train_mask], y[train_mask]
X_test, y_test = X[test_mask], y[test_mask]

print(f"Training games: {train_mask.sum()}")
print(f"Test games: {test_mask.sum()}")
print(f"Home team wins (train): {y_train.mean():.1%}")
print(f"Home team wins (test): {y_test.mean():.1%}")

# Compute sample weights
train_weights = compute_season_weights(dataset.games[train_mask], TRAIN_SEASONS, decay_factor=OPTIMAL_DECAY)
print(f"✓ Sample weights computed")

# Train model
print("\n" + "=" * 80)
print("[3/6] Training V7.0 Pruned model...")
print("=" * 80)

model = create_baseline_model(C=OPTIMAL_C)
train_mask_fit = pd.Series(True, index=X_train.index)
model = fit_model(model, X_train, y_train, train_mask_fit, sample_weight=train_weights)
print("✓ Model trained")
print(f"   Features used: {len(available_features)}")

# Generate predictions
print("\n" + "=" * 80)
print("[4/6] Generating predictions...")
print("=" * 80)

train_mask_pred = pd.Series(True, index=X_train.index)
y_train_pred_proba = predict_probabilities(model, X_train, train_mask_pred)
y_train_pred = (y_train_pred_proba >= 0.5).astype(int)

test_mask_pred = pd.Series(True, index=X_test.index)
y_test_pred_proba = predict_probabilities(model, X_test, test_mask_pred)
y_test_pred = (y_test_pred_proba >= 0.5).astype(int)

print("✓ Predictions generated")

# Calculate metrics
print("\n" + "=" * 80)
print("[5/6] Calculating performance metrics...")
print("=" * 80)

train_acc = accuracy_score(y_train, y_train_pred)
test_acc = accuracy_score(y_test, y_test_pred)
baseline_acc = y_test.mean()  # Predicting all home wins

train_auc = roc_auc_score(y_train, y_train_pred_proba)
test_auc = roc_auc_score(y_test, y_test_pred_proba)

train_logloss = log_loss(y_train, y_train_pred_proba)
test_logloss = log_loss(y_test, y_test_pred_proba)

train_brier = brier_score_loss(y_train, y_train_pred_proba)
test_brier = brier_score_loss(y_test, y_test_pred_proba)

print("\n📊 OVERALL PERFORMANCE")
print("=" * 80)
print(f"{'Metric':<25} {'Train':<15} {'Test':<15} {'Baseline':<15}")
print("-" * 80)
print(f"{'Accuracy':<25} {train_acc:>14.2%} {test_acc:>14.2%} {baseline_acc:>14.2%}")
print(f"{'ROC-AUC':<25} {train_auc:>14.4f} {test_auc:>14.4f} {'0.5000':>15}")
print(f"{'Log Loss':<25} {train_logloss:>14.4f} {test_logloss:>14.4f} {'-':>15}")
print(f"{'Brier Score':<25} {train_brier:>14.4f} {test_brier:>14.4f} {'-':>15}")
print(f"{'Improvement vs Baseline':<25} {(train_acc-baseline_acc)*100:>13.2f}% {(test_acc-baseline_acc)*100:>13.2f}% {'-':>15}")

# Confidence bucket analysis
print("\n" + "=" * 80)
print("[6/6] Analyzing confidence buckets...")
print("=" * 80)

def assign_confidence_bucket(edge):
    """Assign confidence grade based on edge from 50%."""
    if edge >= 0.20:
        return "A+"
    elif edge >= 0.15:
        return "A-"
    elif edge >= 0.10:
        return "B+"
    elif edge >= 0.05:
        return "B-"
    else:
        return "C"

# Calculate for test set
test_edges = np.abs(y_test_pred_proba - 0.5)
test_grades = [assign_confidence_bucket(edge) for edge in test_edges]

print("\n📈 CONFIDENCE BUCKET ANALYSIS (Test Set)")
print("=" * 80)
print(f"{'Grade':<8} {'Games':<8} {'Correct':<10} {'Accuracy':<12} {'Avg Edge':<12} {'Avg Prob':<12}")
print("-" * 80)

for grade in ["A+", "A-", "B+", "B-", "C"]:
    grade_mask = [g == grade for g in test_grades]
    if sum(grade_mask) == 0:
        continue

    grade_y_true = y_test.iloc[grade_mask]
    grade_y_pred = y_test_pred.iloc[grade_mask]
    grade_y_proba = y_test_pred_proba.iloc[grade_mask]
    grade_edges = test_edges[grade_mask]

    grade_correct = (grade_y_true == grade_y_pred).sum()
    grade_acc = grade_correct / len(grade_y_true)
    grade_avg_edge = grade_edges.mean()
    grade_avg_prob = grade_y_proba.mean()

    print(f"{grade:<8} {len(grade_y_true):<8} {grade_correct:<10} {grade_acc:>11.2%} {grade_avg_edge:>11.1%} {grade_avg_prob:>11.2%}")

print(f"\nTotal test games: {len(y_test)}")
print(f"Total correct: {(y_test == y_test_pred).sum()}")

# Comparison with V7.0 unpruned
print("\n" + "=" * 80)
print("COMPARISON: V7.0 Unpruned vs Pruned")
print("=" * 80)
print(f"{'Metric':<25} {'V7.0 (209 feat)':<18} {'V7.0 Pruned ({len(available_features)} feat)':<25} {'Change':<10}")
print("-" * 80)
print(f"{'Test Accuracy':<25} {'60.89%':<18} {test_acc:>24.2%} {test_acc-0.6089:>9.2%}")
print(f"{'ROC-AUC':<25} {'0.6363':<18} {test_auc:>24.4f} {test_auc-0.6363:>9.4f}")
print(f"{'Log Loss':<25} {'0.6752':<18} {test_logloss:>24.4f} {test_logloss-0.6752:>9.4f}")

print("\n" + "=" * 80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
