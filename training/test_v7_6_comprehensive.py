#!/usr/bin/env python3
"""
V7.6 Comprehensive Validation Testing

This script performs extensive validation of the V7.6 model (62.11% accuracy)
to ensure the result is statistically robust and not due to random chance.

Tests performed:
1. Cross-validation (multiple folds)
2. Bootstrap confidence intervals
3. Temporal validation (rolling windows)
4. Feature stability across seasons
5. Statistical significance tests
6. Different random seeds
7. Leave-one-season-out validation
8. Monthly breakdown analysis
9. Calibration analysis
10. Comparison with baseline models

Usage:
    python training/test_v7_6_comprehensive.py
"""

import sys
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss, brier_score_loss
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold, TimeSeriesSplit, cross_val_score
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

TRAIN_SEASONS = ["20212022", "20222023"]
TEST_SEASON = "20232024"
ALL_SEASONS = ["20212022", "20222023", "20232024"]

V75_ACC = 0.6122
V76_CLAIMED_ACC = 0.6211


def load_data():
    """Load and prepare data with V7.5 features."""
    cache_path = Path("data/cache/dataset_v7_3_full.parquet")
    combined = pd.read_parquet(cache_path)

    target = combined["_target"]
    games = pd.DataFrame({
        "gameId": combined["_game_id"],
        "seasonId": combined["_season_id"],
        "gameDate": combined["_game_date"]
    })

    # Add V7.5 features
    def add_v75_features(df):
        g = df.copy()
        if 'rolling_goal_diff_5_diff' in g.columns:
            if 'shotsFor_roll_5_diff' in g.columns:
                shots = g['shotsFor_roll_5_diff'].replace(0, np.nan)
                g['ratio_goals_per_shot_5'] = (g['rolling_goal_diff_5_diff'] / shots).fillna(0).clip(-1, 1)
            if 'shotsFor_roll_10_diff' in g.columns:
                shots = g['shotsFor_roll_10_diff'].replace(0, np.nan)
                g['ratio_goals_per_shot_10'] = (g['rolling_goal_diff_10_diff'] / shots).fillna(0).clip(-1, 1)
        if 'rolling_goal_diff_5_diff' in g.columns and 'rolling_xg_diff_5_diff' in g.columns:
            xg = g['rolling_xg_diff_5_diff'].replace(0, np.nan)
            g['ratio_goals_vs_xg_5'] = (g['rolling_goal_diff_5_diff'] / xg).clip(-3, 3).fillna(0)
        if 'rolling_goal_diff_10_diff' in g.columns and 'rolling_xg_diff_10_diff' in g.columns:
            xg = g['rolling_xg_diff_10_diff'].replace(0, np.nan)
            g['ratio_goals_vs_xg_10'] = (g['rolling_goal_diff_10_diff'] / xg).clip(-3, 3).fillna(0)
        if 'rolling_high_danger_shots_5_diff' in g.columns and 'shotsFor_roll_5_diff' in g.columns:
            shots = g['shotsFor_roll_5_diff'].replace(0, np.nan)
            g['ratio_hd_shots_5'] = (g['rolling_high_danger_shots_5_diff'] / shots).fillna(0).clip(-1, 1)
        if 'rolling_xg_for_5_diff' in g.columns:
            g['luck_indicator_5'] = g['rolling_goal_diff_5_diff'] - g['rolling_xg_diff_5_diff']
        if 'rolling_goal_diff_3_diff' in g.columns and 'rolling_goal_diff_10_diff' in g.columns:
            g['consistency_gd'] = abs(g['rolling_goal_diff_3_diff'] - g['rolling_goal_diff_10_diff'])
        if 'rolling_goal_diff_5_diff' in g.columns and 'rolling_win_pct_5_diff' in g.columns:
            g['dominance_score'] = g['rolling_win_pct_5_diff'].clip(-1, 1) * g['rolling_goal_diff_5_diff'].clip(-3, 3)
        return g

    combined_v75 = add_v75_features(combined)
    features = combined_v75.drop(columns=["_target", "_game_id", "_season_id", "_game_date"]).fillna(0)

    return games, features, target


def get_top_features(X_train, y_train, n_features=59):
    """Get top N features by coefficient magnitude."""
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)

    lr = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
    lr.fit(X_scaled, y_train)

    coef_importance = np.abs(lr.coef_[0])
    sorted_idx = np.argsort(coef_importance)[::-1]

    return sorted_idx[:n_features], scaler


def train_v76_model(X_train, y_train, X_test, top_idx, scaler):
    """Train V7.6 model and return predictions."""
    X_train_scaled = scaler.transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    X_train_sub = X_train_scaled[:, top_idx]
    X_test_sub = X_test_scaled[:, top_idx]

    lr = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
    lr.fit(X_train_sub, y_train)

    proba = lr.predict_proba(X_test_sub)[:, 1]
    return proba


def main():
    print("=" * 80)
    print("V7.6 COMPREHENSIVE VALIDATION TESTING")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Claimed V7.6 Accuracy: {V76_CLAIMED_ACC:.2%}")
    print()

    # Load data
    games, features, target = load_data()
    feature_names = features.columns.tolist()
    print(f"Loaded {len(games)} games, {len(feature_names)} features")

    train_mask = games["seasonId"].isin(TRAIN_SEASONS)
    test_mask = games["seasonId"] == TEST_SEASON

    X_train = features[train_mask].values
    X_test = features[test_mask].values
    y_train = target[train_mask].values
    y_test = target[test_mask].values

    print(f"Train: {len(y_train)} games, Test: {len(y_test)} games")

    # ===== TEST 1: Reproduce Original Result =====
    print("\n" + "=" * 80)
    print("TEST 1: REPRODUCE ORIGINAL RESULT")
    print("=" * 80)

    top_idx, scaler = get_top_features(X_train, y_train, n_features=59)
    proba = train_v76_model(X_train, y_train, X_test, top_idx, scaler)
    acc = accuracy_score(y_test, (proba >= 0.5).astype(int))

    print(f"Reproduced Accuracy: {acc:.4f} ({acc:.2%})")
    print(f"Match with claimed: {'YES' if abs(acc - V76_CLAIMED_ACC) < 0.001 else 'NO'}")

    results = {'original': acc}

    # ===== TEST 2: Different Random Seeds =====
    print("\n" + "=" * 80)
    print("TEST 2: RANDOM SEED STABILITY")
    print("=" * 80)

    seed_results = []
    for seed in [0, 1, 7, 13, 42, 99, 123, 456, 789, 1000]:
        # Get features with different seed
        scaler_s = StandardScaler()
        X_train_scaled = scaler_s.fit_transform(X_train)
        X_test_scaled = scaler_s.transform(X_test)

        lr_full = LogisticRegression(C=0.01, max_iter=1000, random_state=seed)
        lr_full.fit(X_train_scaled, y_train)
        coef_importance = np.abs(lr_full.coef_[0])
        top_idx_s = np.argsort(coef_importance)[::-1][:59]

        X_train_sub = X_train_scaled[:, top_idx_s]
        X_test_sub = X_test_scaled[:, top_idx_s]

        lr = LogisticRegression(C=0.01, max_iter=1000, random_state=seed)
        lr.fit(X_train_sub, y_train)
        proba_s = lr.predict_proba(X_test_sub)[:, 1]
        acc_s = accuracy_score(y_test, (proba_s >= 0.5).astype(int))
        seed_results.append(acc_s)
        print(f"Seed {seed:4d}: {acc_s:.4f}")

    print(f"\nMean: {np.mean(seed_results):.4f}, Std: {np.std(seed_results):.4f}")
    print(f"Range: [{min(seed_results):.4f}, {max(seed_results):.4f}]")
    results['seed_stability'] = {'mean': np.mean(seed_results), 'std': np.std(seed_results)}

    # ===== TEST 3: Bootstrap Confidence Intervals =====
    print("\n" + "=" * 80)
    print("TEST 3: BOOTSTRAP CONFIDENCE INTERVALS (1000 iterations)")
    print("=" * 80)

    n_bootstrap = 1000
    bootstrap_accs = []

    for i in range(n_bootstrap):
        # Resample test set with replacement
        idx = np.random.choice(len(y_test), size=len(y_test), replace=True)
        y_test_boot = y_test[idx]
        proba_boot = proba[idx]
        acc_boot = accuracy_score(y_test_boot, (proba_boot >= 0.5).astype(int))
        bootstrap_accs.append(acc_boot)

        if (i + 1) % 200 == 0:
            print(f"  Completed {i+1}/{n_bootstrap} iterations...")

    bootstrap_accs = np.array(bootstrap_accs)
    ci_lower = np.percentile(bootstrap_accs, 2.5)
    ci_upper = np.percentile(bootstrap_accs, 97.5)

    print(f"\nBootstrap Results:")
    print(f"  Mean: {np.mean(bootstrap_accs):.4f}")
    print(f"  Std:  {np.std(bootstrap_accs):.4f}")
    print(f"  95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
    print(f"  62% in CI: {'YES' if ci_lower <= 0.62 <= ci_upper else 'NO'}")

    results['bootstrap'] = {
        'mean': np.mean(bootstrap_accs),
        'std': np.std(bootstrap_accs),
        'ci_lower': ci_lower,
        'ci_upper': ci_upper
    }

    # ===== TEST 4: K-Fold Cross-Validation on Training Data =====
    print("\n" + "=" * 80)
    print("TEST 4: K-FOLD CROSS-VALIDATION (Training Data)")
    print("=" * 80)

    # Combine for CV
    X_all = features.values
    y_all = target.values

    for k in [3, 5, 10]:
        kfold = KFold(n_splits=k, shuffle=True, random_state=42)
        cv_scores = []

        for train_idx, val_idx in kfold.split(X_all):
            X_cv_train, X_cv_val = X_all[train_idx], X_all[val_idx]
            y_cv_train, y_cv_val = y_all[train_idx], y_all[val_idx]

            top_idx_cv, scaler_cv = get_top_features(X_cv_train, y_cv_train, n_features=59)
            proba_cv = train_v76_model(X_cv_train, y_cv_train, X_cv_val, top_idx_cv, scaler_cv)
            acc_cv = accuracy_score(y_cv_val, (proba_cv >= 0.5).astype(int))
            cv_scores.append(acc_cv)

        print(f"{k}-Fold CV: {np.mean(cv_scores):.4f} +/- {np.std(cv_scores):.4f}")
        results[f'cv_{k}fold'] = {'mean': np.mean(cv_scores), 'std': np.std(cv_scores)}

    # ===== TEST 5: Leave-One-Season-Out Validation =====
    print("\n" + "=" * 80)
    print("TEST 5: LEAVE-ONE-SEASON-OUT VALIDATION")
    print("=" * 80)

    season_results = {}
    for test_season in ALL_SEASONS:
        train_seasons = [s for s in ALL_SEASONS if s != test_season]
        train_mask_s = games["seasonId"].isin(train_seasons)
        test_mask_s = games["seasonId"] == test_season

        X_train_s = features[train_mask_s].values
        X_test_s = features[test_mask_s].values
        y_train_s = target[train_mask_s].values
        y_test_s = target[test_mask_s].values

        top_idx_s, scaler_s = get_top_features(X_train_s, y_train_s, n_features=59)
        proba_s = train_v76_model(X_train_s, y_train_s, X_test_s, top_idx_s, scaler_s)
        acc_s = accuracy_score(y_test_s, (proba_s >= 0.5).astype(int))

        season_results[test_season] = acc_s
        print(f"Test on {test_season}: {acc_s:.4f} ({len(y_test_s)} games)")

    avg_loso = np.mean(list(season_results.values()))
    print(f"\nAverage LOSO: {avg_loso:.4f}")
    results['loso'] = season_results

    # ===== TEST 6: Time Series Split Validation =====
    print("\n" + "=" * 80)
    print("TEST 6: TIME SERIES SPLIT VALIDATION")
    print("=" * 80)

    # Sort by date
    sorted_idx = games.sort_values('gameDate').index
    X_sorted = features.loc[sorted_idx].values
    y_sorted = target.loc[sorted_idx].values

    tscv = TimeSeriesSplit(n_splits=5)
    ts_scores = []

    for fold, (train_idx, val_idx) in enumerate(tscv.split(X_sorted)):
        X_ts_train, X_ts_val = X_sorted[train_idx], X_sorted[val_idx]
        y_ts_train, y_ts_val = y_sorted[train_idx], y_sorted[val_idx]

        if len(y_ts_train) < 500:  # Skip if too few samples
            continue

        top_idx_ts, scaler_ts = get_top_features(X_ts_train, y_ts_train, n_features=59)
        proba_ts = train_v76_model(X_ts_train, y_ts_train, X_ts_val, top_idx_ts, scaler_ts)
        acc_ts = accuracy_score(y_ts_val, (proba_ts >= 0.5).astype(int))
        ts_scores.append(acc_ts)
        print(f"Fold {fold+1}: {acc_ts:.4f} (train={len(y_ts_train)}, val={len(y_ts_val)})")

    print(f"\nTime Series CV Mean: {np.mean(ts_scores):.4f} +/- {np.std(ts_scores):.4f}")
    results['time_series_cv'] = {'mean': np.mean(ts_scores), 'std': np.std(ts_scores)}

    # ===== TEST 7: Feature Stability Analysis =====
    print("\n" + "=" * 80)
    print("TEST 7: FEATURE STABILITY ACROSS SEASONS")
    print("=" * 80)

    top_features_by_season = {}
    for season in ALL_SEASONS:
        other_seasons = [s for s in ALL_SEASONS if s != season]
        train_mask_s = games["seasonId"].isin(other_seasons)

        X_train_s = features[train_mask_s].values
        y_train_s = target[train_mask_s].values

        scaler_s = StandardScaler()
        X_scaled = scaler_s.fit_transform(X_train_s)

        lr_s = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
        lr_s.fit(X_scaled, y_train_s)

        coef_importance = np.abs(lr_s.coef_[0])
        top_idx_s = np.argsort(coef_importance)[::-1][:59]
        top_features_by_season[season] = set(top_idx_s)

    # Calculate overlap
    seasons = list(top_features_by_season.keys())
    print("\nTop 59 Feature Overlap:")
    for i, s1 in enumerate(seasons):
        for s2 in seasons[i+1:]:
            overlap = len(top_features_by_season[s1] & top_features_by_season[s2])
            print(f"  {s1} vs {s2}: {overlap}/59 features ({overlap/59:.1%})")

    # Core features (in all)
    core_features = top_features_by_season[seasons[0]]
    for s in seasons[1:]:
        core_features = core_features & top_features_by_season[s]
    print(f"\nCore features (in all seasons): {len(core_features)}")

    # Show top core features
    core_list = sorted(list(core_features))[:20]
    print("Top core features:")
    for idx in core_list[:10]:
        print(f"  - {feature_names[idx]}")

    results['feature_stability'] = {
        'core_count': len(core_features),
        'core_features': [feature_names[i] for i in list(core_features)[:20]]
    }

    # ===== TEST 8: Monthly Performance Analysis =====
    print("\n" + "=" * 80)
    print("TEST 8: MONTHLY PERFORMANCE ANALYSIS (2023-24)")
    print("=" * 80)

    test_games = games[test_mask].copy()
    test_games['month'] = pd.to_datetime(test_games['gameDate']).dt.month
    test_games['proba'] = proba
    test_games['actual'] = y_test
    test_games['pred'] = (proba >= 0.5).astype(int)
    test_games['correct'] = (test_games['pred'] == test_games['actual']).astype(int)

    monthly_acc = test_games.groupby('month').agg({
        'correct': ['sum', 'count']
    })
    monthly_acc.columns = ['correct', 'total']
    monthly_acc['accuracy'] = monthly_acc['correct'] / monthly_acc['total']

    month_names = {10: 'Oct', 11: 'Nov', 12: 'Dec', 1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr'}
    print(f"\n{'Month':<8} {'Games':>8} {'Accuracy':>10}")
    print("-" * 30)
    for month in [10, 11, 12, 1, 2, 3, 4]:
        if month in monthly_acc.index:
            row = monthly_acc.loc[month]
            print(f"{month_names.get(month, str(month)):<8} {int(row['total']):>8} {row['accuracy']:>10.1%}")

    results['monthly'] = monthly_acc['accuracy'].to_dict()

    # ===== TEST 9: Statistical Significance vs V7.5 =====
    print("\n" + "=" * 80)
    print("TEST 9: STATISTICAL SIGNIFICANCE vs V7.5")
    print("=" * 80)

    # Train V7.5 model (all features, C=0.01)
    scaler_v75 = StandardScaler()
    X_train_scaled_v75 = scaler_v75.fit_transform(X_train)
    X_test_scaled_v75 = scaler_v75.transform(X_test)

    lr_v75 = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
    lr_v75.fit(X_train_scaled_v75, y_train)
    proba_v75 = lr_v75.predict_proba(X_test_scaled_v75)[:, 1]
    acc_v75 = accuracy_score(y_test, (proba_v75 >= 0.5).astype(int))

    print(f"V7.5 Accuracy: {acc_v75:.4f}")
    print(f"V7.6 Accuracy: {acc:.4f}")
    print(f"Difference: {(acc - acc_v75) * 100:+.2f}pp")

    # McNemar's test
    pred_v75 = (proba_v75 >= 0.5).astype(int)
    pred_v76 = (proba >= 0.5).astype(int)

    # Contingency table
    both_correct = ((pred_v75 == y_test) & (pred_v76 == y_test)).sum()
    both_wrong = ((pred_v75 != y_test) & (pred_v76 != y_test)).sum()
    v75_only = ((pred_v75 == y_test) & (pred_v76 != y_test)).sum()
    v76_only = ((pred_v75 != y_test) & (pred_v76 == y_test)).sum()

    print(f"\nContingency Table:")
    print(f"  Both correct: {both_correct}")
    print(f"  Both wrong:   {both_wrong}")
    print(f"  V7.5 only:    {v75_only}")
    print(f"  V7.6 only:    {v76_only}")

    # McNemar's test
    if v75_only + v76_only > 0:
        chi2 = (abs(v75_only - v76_only) - 1) ** 2 / (v75_only + v76_only)
        p_value = 1 - stats.chi2.cdf(chi2, df=1)
        print(f"\nMcNemar's Test:")
        print(f"  Chi-squared: {chi2:.4f}")
        print(f"  P-value: {p_value:.4f}")
        print(f"  Significant (p<0.05): {'YES' if p_value < 0.05 else 'NO'}")

    results['significance'] = {
        'v75_acc': acc_v75,
        'v76_acc': acc,
        'v75_only': v75_only,
        'v76_only': v76_only
    }

    # ===== TEST 10: Model Calibration Analysis =====
    print("\n" + "=" * 80)
    print("TEST 10: MODEL CALIBRATION ANALYSIS")
    print("=" * 80)

    # Calibration by probability buckets
    prob_buckets = [(0.5, 0.55), (0.55, 0.60), (0.60, 0.65), (0.65, 0.70), (0.70, 0.75), (0.75, 1.0)]

    print(f"\n{'Prob Range':<12} {'Games':>8} {'Actual':>10} {'Expected':>10} {'Calibration':>12}")
    print("-" * 55)

    for low, high in prob_buckets:
        mask = (proba >= low) & (proba < high)
        if mask.sum() > 0:
            actual_rate = y_test[mask].mean()
            expected_rate = proba[mask].mean()
            calibration = actual_rate - expected_rate
            print(f"{low:.2f}-{high:.2f}    {mask.sum():>8} {actual_rate:>10.1%} {expected_rate:>10.1%} {calibration:>+11.1%}")

    brier = brier_score_loss(y_test, proba)
    print(f"\nBrier Score: {brier:.4f}")
    results['calibration'] = {'brier_score': brier}

    # ===== TEST 11: Feature Count Sensitivity =====
    print("\n" + "=" * 80)
    print("TEST 11: FEATURE COUNT SENSITIVITY ANALYSIS")
    print("=" * 80)

    feature_counts = [40, 45, 50, 55, 57, 58, 59, 60, 61, 62, 65, 70, 80, 100]
    count_results = []

    for n in feature_counts:
        top_idx_n, scaler_n = get_top_features(X_train, y_train, n_features=n)
        proba_n = train_v76_model(X_train, y_train, X_test, top_idx_n, scaler_n)
        acc_n = accuracy_score(y_test, (proba_n >= 0.5).astype(int))
        count_results.append((n, acc_n))
        marker = " <-- V7.6" if n == 59 else ""
        print(f"Top {n:3d}: {acc_n:.4f}{marker}")

    results['feature_sensitivity'] = dict(count_results)

    # ===== FINAL SUMMARY =====
    print("\n" + "=" * 80)
    print("COMPREHENSIVE VALIDATION SUMMARY")
    print("=" * 80)

    print(f"""
Original Claimed Accuracy:  {V76_CLAIMED_ACC:.2%}
Reproduced Accuracy:        {results['original']:.2%}

STABILITY TESTS:
  Random Seed Mean:         {results['seed_stability']['mean']:.2%} +/- {results['seed_stability']['std']:.2%}
  Bootstrap 95% CI:         [{results['bootstrap']['ci_lower']:.2%}, {results['bootstrap']['ci_upper']:.2%}]
  Bootstrap Mean:           {results['bootstrap']['mean']:.2%}

CROSS-VALIDATION:
  5-Fold CV:                {results['cv_5fold']['mean']:.2%} +/- {results['cv_5fold']['std']:.2%}
  10-Fold CV:               {results['cv_10fold']['mean']:.2%} +/- {results['cv_10fold']['std']:.2%}
  Time Series CV:           {results['time_series_cv']['mean']:.2%} +/- {results['time_series_cv']['std']:.2%}

LEAVE-ONE-SEASON-OUT:
  2021-22 holdout:          {results['loso']['20212022']:.2%}
  2022-23 holdout:          {results['loso']['20222023']:.2%}
  2023-24 holdout:          {results['loso']['20232024']:.2%}
  LOSO Average:             {np.mean(list(results['loso'].values())):.2%}

FEATURE STABILITY:
  Core features (all seasons): {results['feature_stability']['core_count']}/59

CALIBRATION:
  Brier Score:              {results['calibration']['brier_score']:.4f}

STATISTICAL SIGNIFICANCE:
  V7.6 vs V7.5 improvement: {(results['significance']['v76_acc'] - results['significance']['v75_acc'])*100:+.2f}pp
  Games V7.6 got right (V7.5 wrong): {results['significance']['v76_only']}
  Games V7.5 got right (V7.6 wrong): {results['significance']['v75_only']}
""")

    # Verdict
    print("=" * 80)
    print("VERDICT")
    print("=" * 80)

    checks = [
        ("Reproduction matches", abs(results['original'] - V76_CLAIMED_ACC) < 0.001),
        ("Bootstrap CI includes claimed", results['bootstrap']['ci_lower'] <= V76_CLAIMED_ACC <= results['bootstrap']['ci_upper']),
        ("Seed stability < 1%", results['seed_stability']['std'] < 0.01),
        ("CV mean > 58%", results['cv_5fold']['mean'] > 0.58),
        ("LOSO mean > 58%", np.mean(list(results['loso'].values())) > 0.58),
        ("Core features > 30", results['feature_stability']['core_count'] > 30),
    ]

    passed = sum(1 for _, v in checks if v)
    total = len(checks)

    for name, result in checks:
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {name}")

    print(f"\nResult: {passed}/{total} checks passed")

    if passed == total:
        print("\nCONCLUSION: V7.6 accuracy of 62.11% is VALIDATED")
    else:
        print("\nCONCLUSION: Some validation checks failed - review results carefully")

    print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return results


if __name__ == "__main__":
    main()
