"""Feature Importance Analysis for NHL Prediction Model.

This script:
1. Trains baseline model and extracts feature importances
2. Identifies top/bottom features
3. Tests dropping low-importance features
4. Measures impact on accuracy
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.nhl_prediction.pipeline import build_dataset
from src.nhl_prediction.train import compute_season_weights

print("="*80)
print("FEATURE IMPORTANCE ANALYSIS")
print("="*80)

# Load data
print("\n[1/5] Loading dataset...")
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

# Compute sample weights
weights = compute_season_weights(
    games[train_mask],
    ["20212022", "20222023"],
    decay_factor=0.85
)

print(f"  Train games: {len(X_train)}")
print(f"  Test games: {len(X_test)}")

# Train baseline model
print("\n[2/5] Training baseline model...")
model = LogisticRegression(C=0.001, max_iter=1000, random_state=42)
model.fit(X_train, y_train, sample_weight=weights)

# Baseline performance
y_pred_baseline = model.predict(X_test)
y_proba_baseline = model.predict_proba(X_test)[:, 1]
acc_baseline = accuracy_score(y_test, y_pred_baseline)
auc_baseline = roc_auc_score(y_test, y_proba_baseline)
ll_baseline = log_loss(y_test, y_proba_baseline)

print(f"\n  BASELINE PERFORMANCE:")
print(f"  Accuracy:  {acc_baseline:.4f} ({acc_baseline*100:.2f}%)")
print(f"  ROC-AUC:   {auc_baseline:.4f}")
print(f"  Log Loss:  {ll_baseline:.4f}")

# Extract feature importances
print("\n[3/5] Extracting feature importances...")
importances = np.abs(model.coef_[0])
feature_names = X.columns.tolist()

importance_df = pd.DataFrame({
    'feature': feature_names,
    'importance': importances,
    'coefficient': model.coef_[0]
})
importance_df = importance_df.sort_values('importance', ascending=False)

print(f"\n  TOP 20 MOST IMPORTANT FEATURES:")
print("  " + "-"*70)
for i, row in importance_df.head(20).iterrows():
    print(f"  {row['feature'][:50]:<50} {row['importance']:>8.4f}")

print(f"\n  BOTTOM 20 LEAST IMPORTANT FEATURES:")
print("  " + "-"*70)
for i, row in importance_df.tail(20).iterrows():
    print(f"  {row['feature'][:50]:<50} {row['importance']:>8.4f}")

# Save full importance ranking
importance_df.to_csv("feature_importance_rankings.csv", index=False)
print(f"\n  ✓ Saved full rankings to feature_importance_rankings.csv")

# Test dropping bottom features
print("\n[4/5] Testing feature pruning strategies...")
results = []

# Baseline (all features)
results.append({
    'strategy': 'All features (baseline)',
    'num_features': len(X.columns),
    'accuracy': acc_baseline,
    'roc_auc': auc_baseline,
    'log_loss': ll_baseline
})

# Drop bottom N% features
for pct in [10, 20, 30, 40, 50]:
    n_drop = int(len(feature_names) * pct / 100)
    features_to_drop = importance_df.tail(n_drop)['feature'].tolist()
    features_to_keep = [f for f in feature_names if f not in features_to_drop]

    # Train with reduced features
    model_pruned = LogisticRegression(C=0.001, max_iter=1000, random_state=42)
    model_pruned.fit(X_train[features_to_keep], y_train, sample_weight=weights)

    # Evaluate
    y_pred = model_pruned.predict(X_test[features_to_keep])
    y_proba = model_pruned.predict_proba(X_test[features_to_keep])[:, 1]
    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    ll = log_loss(y_test, y_proba)

    results.append({
        'strategy': f'Drop bottom {pct}%',
        'num_features': len(features_to_keep),
        'accuracy': acc,
        'roc_auc': auc,
        'log_loss': ll
    })

    print(f"  Drop bottom {pct}% ({n_drop} features) → {len(features_to_keep)} features")
    print(f"    Accuracy: {acc:.4f} ({(acc-acc_baseline)*100:+.2f}pp)")

# Keep only top N features
for n_keep in [50, 75, 100, 150]:
    if n_keep > len(feature_names):
        continue

    features_to_keep = importance_df.head(n_keep)['feature'].tolist()

    # Train with top features only
    model_top = LogisticRegression(C=0.001, max_iter=1000, random_state=42)
    model_top.fit(X_train[features_to_keep], y_train, sample_weight=weights)

    # Evaluate
    y_pred = model_top.predict(X_test[features_to_keep])
    y_proba = model_top.predict_proba(X_test[features_to_keep])[:, 1]
    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    ll = log_loss(y_test, y_proba)

    results.append({
        'strategy': f'Top {n_keep} only',
        'num_features': n_keep,
        'accuracy': acc,
        'roc_auc': auc,
        'log_loss': ll
    })

    print(f"  Keep top {n_keep} features only")
    print(f"    Accuracy: {acc:.4f} ({(acc-acc_baseline)*100:+.2f}pp)")

# Summary
print("\n[5/5] SUMMARY OF RESULTS")
print("="*80)

results_df = pd.DataFrame(results)
results_df['acc_change'] = (results_df['accuracy'] - acc_baseline) * 100

print(f"\n{'Strategy':<30} {'Features':<12} {'Accuracy':<12} {'Change':<10} {'ROC-AUC':<10}")
print("-"*80)
for _, row in results_df.iterrows():
    print(f"{row['strategy']:<30} {row['num_features']:<12} "
          f"{row['accuracy']*100:>6.2f}%      {row['acc_change']:>+6.2f}pp   "
          f"{row['roc_auc']:>6.4f}")

# Find best configuration
best_idx = results_df['accuracy'].idxmax()
best_result = results_df.loc[best_idx]

print("\n" + "="*80)
print("BEST CONFIGURATION:")
print(f"  Strategy: {best_result['strategy']}")
print(f"  Features: {best_result['num_features']} (from {len(feature_names)})")
print(f"  Accuracy: {best_result['accuracy']*100:.2f}% ({best_result['acc_change']:+.2f}pp vs baseline)")
print(f"  ROC-AUC:  {best_result['roc_auc']:.4f}")
print("="*80)

# Save results
results_df.to_csv("feature_pruning_results.csv", index=False)
print(f"\n✓ Saved results to feature_pruning_results.csv")

# Recommendations
print("\nRECOMMENDATIONS:")
if best_result['acc_change'] > 0.1:
    print(f"  ✅ RECOMMEND: Use {best_result['strategy']} for +{best_result['acc_change']:.2f}pp gain")
else:
    print(f"  ℹ️  Current feature set is well-optimized. Pruning provides minimal benefit.")
    print(f"     Continue with all {len(feature_names)} features.")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
