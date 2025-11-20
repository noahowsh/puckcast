"""Hyperparameter Tuning for NHL Prediction Model.

This script performs grid search over:
1. Regularization strength (C)
2. Sample weighting decay factor
3. Model selection (LogisticRegression vs HistGradientBoosting)
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
from itertools import product

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.nhl_prediction.pipeline import build_dataset
from src.nhl_prediction.train import compute_season_weights

print("="*80)
print("HYPERPARAMETER TUNING - COMPREHENSIVE GRID SEARCH")
print("="*80)

# Load data
print("\n[1/4] Loading dataset...")
dataset = build_dataset(["20212022", "20222023", "20232024"])
games = dataset.games
X = dataset.features
y = dataset.target

print(f"  Total features: {len(X.columns)}")
print(f"  Total games: {len(games)}")

# Split train/test
train_mask = games["seasonId"].isin(["20212022", "20222023"])
test_mask = games["seasonId"].isin(["20232024"])

X_train = X[train_mask]
y_train = y[train_mask]
X_test = X[test_mask]
y_test = y[test_mask]

print(f"  Train games: {len(X_train)}")
print(f"  Test games: {len(X_test)}")

# Grid search parameters
C_VALUES = [0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
DECAY_FACTORS = [0.75, 0.80, 0.85, 0.90, 0.95, 1.0]  # 1.0 = no decay

print(f"\n[2/4] Grid search configuration:")
print(f"  C values: {C_VALUES}")
print(f"  Decay factors: {DECAY_FACTORS}")
print(f"  Total combinations: {len(C_VALUES) * len(DECAY_FACTORS)}")

# Grid search
print(f"\n[3/4] Running grid search...")
print("  (This will take a few minutes...)")

results = []
best_acc = 0
best_config = None

for i, (C, decay) in enumerate(product(C_VALUES, DECAY_FACTORS), 1):
    # Compute weights with current decay factor
    weights = compute_season_weights(
        games[train_mask],
        ["20212022", "20222023"],
        decay_factor=decay
    )

    # Train LogisticRegression
    model = LogisticRegression(C=C, max_iter=1000, random_state=42)
    model.fit(X_train, y_train, sample_weight=weights)

    # Evaluate
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    ll = log_loss(y_test, y_proba)

    results.append({
        'model': 'LogisticRegression',
        'C': C,
        'decay': decay,
        'accuracy': acc,
        'roc_auc': auc,
        'log_loss': ll
    })

    # Track best
    if acc > best_acc:
        best_acc = acc
        best_config = f"LR(C={C}, decay={decay})"

    # Progress indicator
    if i % 10 == 0:
        print(f"    Completed {i}/{len(C_VALUES) * len(DECAY_FACTORS)} configurations...")

print(f"  ✓ Grid search complete!")

# Also try HistGradientBoosting with different decay factors
print(f"\n  Testing HistGradientBoosting...")

for decay in DECAY_FACTORS:
    weights = compute_season_weights(
        games[train_mask],
        ["20212022", "20222023"],
        decay_factor=decay
    )

    # Train HistGradientBoosting
    model = HistGradientBoostingClassifier(
        learning_rate=0.05,
        max_depth=3,
        max_leaf_nodes=31,
        min_samples_leaf=20,
        random_state=42
    )
    model.fit(X_train, y_train, sample_weight=weights)

    # Evaluate
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    ll = log_loss(y_test, y_proba)

    results.append({
        'model': 'HistGradientBoosting',
        'C': None,
        'decay': decay,
        'accuracy': acc,
        'roc_auc': auc,
        'log_loss': ll
    })

    if acc > best_acc:
        best_acc = acc
        best_config = f"HGB(decay={decay})"

# Results analysis
print(f"\n[4/4] RESULTS ANALYSIS")
print("="*80)

results_df = pd.DataFrame(results)

# Overall best
best_idx = results_df['accuracy'].idxmax()
best_result = results_df.loc[best_idx]

print(f"\n🏆 BEST OVERALL CONFIGURATION:")
print(f"  Model:     {best_result['model']}")
if best_result['C'] is not None:
    print(f"  C:         {best_result['C']}")
print(f"  Decay:     {best_result['decay']}")
print(f"  Accuracy:  {best_result['accuracy']*100:.2f}%")
print(f"  ROC-AUC:   {best_result['roc_auc']:.4f}")
print(f"  Log Loss:  {best_result['log_loss']:.4f}")

# Current baseline for comparison
baseline = results_df[(results_df['model'] == 'LogisticRegression') &
                      (results_df['C'] == 0.001) &
                      (results_df['decay'] == 0.85)]
if not baseline.empty:
    baseline_acc = baseline.iloc[0]['accuracy']
    improvement = (best_result['accuracy'] - baseline_acc) * 100
    print(f"\n  Improvement over baseline (C=0.001, decay=0.85): {improvement:+.2f}pp")

# Best by model type
print(f"\n📊 BEST CONFIGURATION BY MODEL TYPE:")
print("-"*80)

for model_name in results_df['model'].unique():
    model_results = results_df[results_df['model'] == model_name]
    best_for_model = model_results.loc[model_results['accuracy'].idxmax()]

    print(f"\n  {model_name}:")
    if best_for_model['C'] is not None:
        print(f"    Best C:         {best_for_model['C']}")
    print(f"    Best Decay:     {best_for_model['decay']}")
    print(f"    Accuracy:       {best_for_model['accuracy']*100:.2f}%")
    print(f"    ROC-AUC:        {best_for_model['roc_auc']:.4f}")

# Impact of decay factor
print(f"\n📈 DECAY FACTOR IMPACT (LogisticRegression, C=0.001):")
print("-"*80)
lr_c001 = results_df[(results_df['model'] == 'LogisticRegression') &
                      (results_df['C'] == 0.001)].sort_values('decay')

if not lr_c001.empty:
    print(f"  {'Decay':<10} {'Accuracy':<12} {'ROC-AUC':<10} {'Log Loss':<10}")
    print("  " + "-"*50)
    for _, row in lr_c001.iterrows():
        print(f"  {row['decay']:<10.2f} {row['accuracy']*100:>6.2f}%      "
              f"{row['roc_auc']:>6.4f}    {row['log_loss']:>6.4f}")

# Impact of C value
print(f"\n📈 REGULARIZATION (C) IMPACT (LogisticRegression, decay=0.85):")
print("-"*80)
lr_decay85 = results_df[(results_df['model'] == 'LogisticRegression') &
                        (results_df['decay'] == 0.85)].sort_values('C')

if not lr_decay85.empty:
    print(f"  {'C':<12} {'Accuracy':<12} {'ROC-AUC':<10} {'Log Loss':<10}")
    print("  " + "-"*50)
    for _, row in lr_decay85.iterrows():
        print(f"  {row['C']:<12.4f} {row['accuracy']*100:>6.2f}%      "
              f"{row['roc_auc']:>6.4f}    {row['log_loss']:>6.4f}")

# Save results
results_df.to_csv("hyperparameter_tuning_results.csv", index=False)
print(f"\n✓ Saved detailed results to hyperparameter_tuning_results.csv")

# Top 10 configurations
print(f"\n🔝 TOP 10 CONFIGURATIONS:")
print("-"*80)
top10 = results_df.nlargest(10, 'accuracy')
print(f"  {'Rank':<6} {'Model':<25} {'C':<10} {'Decay':<8} {'Accuracy':<10}")
print("  " + "-"*70)
for i, (_, row) in enumerate(top10.iterrows(), 1):
    c_str = f"{row['C']:.4f}" if row['C'] is not None else "N/A"
    print(f"  {i:<6} {row['model']:<25} {c_str:<10} {row['decay']:<8.2f} "
          f"{row['accuracy']*100:>6.2f}%")

# Recommendations
print("\n" + "="*80)
print("RECOMMENDATIONS:")
print("="*80)

if improvement > 0.2:
    print(f"  ✅ SIGNIFICANT IMPROVEMENT FOUND: +{improvement:.2f}pp")
    print(f"  📝 Update train.py with:")
    if best_result['model'] == 'LogisticRegression':
        print(f"     C = {best_result['C']}")
    print(f"     decay_factor = {best_result['decay']}")
    print(f"     model = {best_result['model']}")
elif improvement > 0:
    print(f"  ✅ Small improvement found: +{improvement:.2f}pp")
    print(f"  Consider updating if targeting maximum accuracy")
else:
    print(f"  ℹ️  Current hyperparameters are optimal")
    print(f"     No tuning needed")

print("\n" + "="*80)
print("TUNING COMPLETE")
print("="*80)
