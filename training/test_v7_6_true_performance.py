#!/usr/bin/env python3
"""
V7.6 TRUE PERFORMANCE ASSESSMENT

This script determines the HONEST expected performance of V7.6
using proper time-series validation (no look-ahead bias).

Key principle: Always train on past data, test on future data.
Never use any future information in feature selection.

Usage:
    python training/test_v7_6_true_performance.py
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
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def load_data():
    """Load and prepare data with V7.5 features."""
    cache_path = Path("data/cache/dataset_v7_3_full.parquet")
    combined = pd.read_parquet(cache_path)

    target = combined["_target"]
    games = pd.DataFrame({
        "gameId": combined["_game_id"],
        "seasonId": combined["_season_id"],
        "gameDate": pd.to_datetime(combined["_game_date"])
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


def train_v76_model_fresh(X_train, y_train, X_test, n_features=59):
    """
    Train V7.6 model from scratch on training data only.
    Feature selection uses ONLY training data coefficients.
    """
    # Scale
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Get coefficients from training data ONLY
    lr_full = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
    lr_full.fit(X_train_scaled, y_train)

    # Select top features by |coefficient|
    coef_importance = np.abs(lr_full.coef_[0])
    top_idx = np.argsort(coef_importance)[::-1][:n_features]

    # Train final model on selected features
    X_train_sub = X_train_scaled[:, top_idx]
    X_test_sub = X_test_scaled[:, top_idx]

    lr = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
    lr.fit(X_train_sub, y_train)

    proba = lr.predict_proba(X_test_sub)[:, 1]
    return proba, top_idx


def main():
    print("=" * 80)
    print("V7.6 TRUE PERFORMANCE ASSESSMENT")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("OBJECTIVE: Determine honest expected performance using proper")
    print("           time-series validation (train on past, test on future)")
    print()

    # Load data
    games, features, target = load_data()
    feature_names = features.columns.tolist()
    print(f"Loaded {len(games)} games, {len(feature_names)} features")

    # Sort by date
    sorted_idx = games.sort_values('gameDate').index
    games = games.loc[sorted_idx].reset_index(drop=True)
    features = features.loc[sorted_idx].reset_index(drop=True)
    target = target.loc[sorted_idx].reset_index(drop=True)

    X = features.values
    y = target.values
    dates = games['gameDate'].values
    seasons = games['seasonId'].values

    print(f"\nDate range: {dates[0]} to {dates[-1]}")
    print(f"Seasons: {sorted(games['seasonId'].unique())}")

    all_results = []

    # =========================================================================
    # TEST 1: PROPER SEASON-BY-SEASON FORWARD VALIDATION
    # =========================================================================
    print("\n" + "=" * 80)
    print("TEST 1: SEASON-BY-SEASON FORWARD VALIDATION")
    print("=" * 80)
    print("Rule: Train on ALL previous seasons, test on next season")
    print("      Feature selection done fresh each time using only train data")
    print()

    season_list = ["20212022", "20222023", "20232024"]
    season_results = []

    for i, test_season in enumerate(season_list):
        if i == 0:
            print(f"Skipping {test_season} - no prior seasons to train on")
            continue

        train_seasons = season_list[:i]
        train_mask = games['seasonId'].isin(train_seasons)
        test_mask = games['seasonId'] == test_season

        X_train = features[train_mask].values
        X_test = features[test_mask].values
        y_train = target[train_mask].values
        y_test = target[test_mask].values

        proba, _ = train_v76_model_fresh(X_train, y_train, X_test, n_features=59)
        acc = accuracy_score(y_test, (proba >= 0.5).astype(int))
        auc = roc_auc_score(y_test, proba)
        ll = log_loss(y_test, proba)

        season_results.append({
            'test_season': test_season,
            'train_seasons': train_seasons,
            'accuracy': acc,
            'auc': auc,
            'log_loss': ll,
            'n_train': len(y_train),
            'n_test': len(y_test)
        })

        print(f"Train: {train_seasons} -> Test: {test_season}")
        print(f"  Accuracy: {acc:.4f} ({acc:.2%})")
        print(f"  ROC-AUC:  {auc:.4f}")
        print(f"  Log Loss: {ll:.4f}")
        print(f"  Train: {len(y_train)} games, Test: {len(y_test)} games")
        print()

    avg_acc = np.mean([r['accuracy'] for r in season_results])
    avg_auc = np.mean([r['auc'] for r in season_results])
    print(f"AVERAGE (Season-by-Season): {avg_acc:.4f} ({avg_acc:.2%})")
    all_results.append(('Season Forward', avg_acc, season_results))

    # =========================================================================
    # TEST 2: EXPANDING WINDOW VALIDATION (Monthly)
    # =========================================================================
    print("\n" + "=" * 80)
    print("TEST 2: EXPANDING WINDOW VALIDATION (Monthly)")
    print("=" * 80)
    print("Rule: Train on all data up to month X, test on month X")
    print("      Minimum 1000 games for training before testing")
    print()

    # Create monthly bins
    games['year_month'] = games['gameDate'].dt.to_period('M')
    months = sorted(games['year_month'].unique())

    monthly_results = []
    min_train_size = 1000

    for month in months:
        train_mask = games['year_month'] < month
        test_mask = games['year_month'] == month

        if train_mask.sum() < min_train_size:
            continue

        X_train = features[train_mask].values
        X_test = features[test_mask].values
        y_train = target[train_mask].values
        y_test = target[test_mask].values

        if len(y_test) < 50:  # Skip very small test sets
            continue

        proba, _ = train_v76_model_fresh(X_train, y_train, X_test, n_features=59)
        acc = accuracy_score(y_test, (proba >= 0.5).astype(int))

        monthly_results.append({
            'month': str(month),
            'accuracy': acc,
            'n_train': len(y_train),
            'n_test': len(y_test)
        })

    print(f"{'Month':<10} {'Train':>8} {'Test':>8} {'Accuracy':>10}")
    print("-" * 40)
    for r in monthly_results:
        print(f"{r['month']:<10} {r['n_train']:>8} {r['n_test']:>8} {r['accuracy']:>10.2%}")

    avg_monthly = np.mean([r['accuracy'] for r in monthly_results])
    print(f"\nAVERAGE (Monthly Expanding): {avg_monthly:.4f} ({avg_monthly:.2%})")
    all_results.append(('Monthly Expanding', avg_monthly, monthly_results))

    # =========================================================================
    # TEST 3: ROLLING WINDOW VALIDATION
    # =========================================================================
    print("\n" + "=" * 80)
    print("TEST 3: ROLLING WINDOW VALIDATION (1-season window)")
    print("=" * 80)
    print("Rule: Train on previous ~1230 games, test on next ~200 games")
    print("      Rolling forward through the data")
    print()

    window_size = 1230  # ~1 season
    step_size = 200     # ~2 weeks
    rolling_results = []

    start_idx = window_size
    while start_idx + step_size <= len(X):
        train_idx = np.arange(start_idx - window_size, start_idx)
        test_idx = np.arange(start_idx, min(start_idx + step_size, len(X)))

        X_train = X[train_idx]
        X_test = X[test_idx]
        y_train = y[train_idx]
        y_test = y[test_idx]

        proba, _ = train_v76_model_fresh(X_train, y_train, X_test, n_features=59)
        acc = accuracy_score(y_test, (proba >= 0.5).astype(int))

        rolling_results.append(acc)
        start_idx += step_size

    print(f"Number of rolling windows: {len(rolling_results)}")
    print(f"Individual accuracies: {[f'{a:.2%}' for a in rolling_results[:10]]}...")
    avg_rolling = np.mean(rolling_results)
    std_rolling = np.std(rolling_results)
    print(f"\nAVERAGE (Rolling Window): {avg_rolling:.4f} ({avg_rolling:.2%}) +/- {std_rolling:.2%}")
    all_results.append(('Rolling Window', avg_rolling, rolling_results))

    # =========================================================================
    # TEST 4: FEATURE COUNT SENSITIVITY (with proper validation)
    # =========================================================================
    print("\n" + "=" * 80)
    print("TEST 4: FEATURE COUNT SENSITIVITY (Proper Validation)")
    print("=" * 80)
    print("Rule: For each feature count, run season-forward validation")
    print()

    feature_counts = [20, 30, 40, 50, 59, 70, 100, 150, 230]
    feature_sensitivity = {}

    for n_feat in feature_counts:
        accs = []
        for i, test_season in enumerate(season_list):
            if i == 0:
                continue
            train_seasons = season_list[:i]
            train_mask = games['seasonId'].isin(train_seasons)
            test_mask = games['seasonId'] == test_season

            X_train = features[train_mask].values
            X_test = features[test_mask].values
            y_train = target[train_mask].values
            y_test = target[test_mask].values

            proba, _ = train_v76_model_fresh(X_train, y_train, X_test, n_features=n_feat)
            acc = accuracy_score(y_test, (proba >= 0.5).astype(int))
            accs.append(acc)

        avg = np.mean(accs)
        feature_sensitivity[n_feat] = avg
        print(f"Top {n_feat:3d} features: {avg:.4f} ({avg:.2%})")

    best_n = max(feature_sensitivity, key=feature_sensitivity.get)
    print(f"\nBest feature count: {best_n} at {feature_sensitivity[best_n]:.2%}")

    # =========================================================================
    # TEST 5: BASELINE COMPARISONS (Proper Validation)
    # =========================================================================
    print("\n" + "=" * 80)
    print("TEST 5: BASELINE COMPARISONS (Season-Forward)")
    print("=" * 80)

    baselines = {}

    # Random (50%)
    baselines['Random'] = 0.50

    # Home always wins
    home_accs = []
    for i, test_season in enumerate(season_list):
        if i == 0:
            continue
        test_mask = games['seasonId'] == test_season
        y_test = target[test_mask].values
        home_accs.append(y_test.mean())
    baselines['Home Always'] = np.mean(home_accs)

    # Elo only
    elo_cols = [i for i, name in enumerate(feature_names) if 'elo' in name.lower()]
    elo_accs = []
    for i, test_season in enumerate(season_list):
        if i == 0:
            continue
        train_seasons = season_list[:i]
        train_mask = games['seasonId'].isin(train_seasons)
        test_mask = games['seasonId'] == test_season

        X_train = features[train_mask].values[:, elo_cols]
        X_test = features[test_mask].values[:, elo_cols]
        y_train = target[train_mask].values
        y_test = target[test_mask].values

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        lr = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
        lr.fit(X_train_s, y_train)
        proba = lr.predict_proba(X_test_s)[:, 1]
        elo_accs.append(accuracy_score(y_test, (proba >= 0.5).astype(int)))
    baselines['Elo Only'] = np.mean(elo_accs)

    # All features (no selection)
    all_feat_accs = []
    for i, test_season in enumerate(season_list):
        if i == 0:
            continue
        train_seasons = season_list[:i]
        train_mask = games['seasonId'].isin(train_seasons)
        test_mask = games['seasonId'] == test_season

        X_train = features[train_mask].values
        X_test = features[test_mask].values
        y_train = target[train_mask].values
        y_test = target[test_mask].values

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        lr = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
        lr.fit(X_train_s, y_train)
        proba = lr.predict_proba(X_test_s)[:, 1]
        all_feat_accs.append(accuracy_score(y_test, (proba >= 0.5).astype(int)))
    baselines['All 230 Features'] = np.mean(all_feat_accs)

    # V7.6 (59 features)
    baselines['V7.6 (59 features)'] = avg_acc

    print(f"\n{'Model':<25} {'Accuracy':>10}")
    print("-" * 40)
    for name, acc in sorted(baselines.items(), key=lambda x: x[1]):
        print(f"{name:<25} {acc:>10.2%}")

    # =========================================================================
    # TEST 6: CONFIDENCE INTERVALS
    # =========================================================================
    print("\n" + "=" * 80)
    print("TEST 6: TRUE PERFORMANCE CONFIDENCE INTERVALS")
    print("=" * 80)

    # Collect all test predictions from season-forward validation
    all_preds = []
    all_actual = []

    for i, test_season in enumerate(season_list):
        if i == 0:
            continue
        train_seasons = season_list[:i]
        train_mask = games['seasonId'].isin(train_seasons)
        test_mask = games['seasonId'] == test_season

        X_train = features[train_mask].values
        X_test = features[test_mask].values
        y_train = target[train_mask].values
        y_test = target[test_mask].values

        proba, _ = train_v76_model_fresh(X_train, y_train, X_test, n_features=59)
        all_preds.extend(proba)
        all_actual.extend(y_test)

    all_preds = np.array(all_preds)
    all_actual = np.array(all_actual)

    # Bootstrap CI
    n_bootstrap = 2000
    bootstrap_accs = []

    for _ in range(n_bootstrap):
        idx = np.random.choice(len(all_actual), size=len(all_actual), replace=True)
        acc = accuracy_score(all_actual[idx], (all_preds[idx] >= 0.5).astype(int))
        bootstrap_accs.append(acc)

    bootstrap_accs = np.array(bootstrap_accs)
    ci_lower = np.percentile(bootstrap_accs, 2.5)
    ci_upper = np.percentile(bootstrap_accs, 97.5)

    print(f"\nBased on {len(all_actual)} out-of-sample predictions:")
    print(f"  Point estimate:  {np.mean(bootstrap_accs):.4f} ({np.mean(bootstrap_accs):.2%})")
    print(f"  95% CI:          [{ci_lower:.4f}, {ci_upper:.4f}]")
    print(f"                   [{ci_lower:.2%}, {ci_upper:.2%}]")

    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print("\n" + "=" * 80)
    print("TRUE PERFORMANCE SUMMARY")
    print("=" * 80)

    print(f"""
VALIDATION METHOD COMPARISON:
-----------------------------
Season-Forward Validation:  {avg_acc:.2%}
Monthly Expanding Window:   {avg_monthly:.2%}
Rolling Window (1 season):  {avg_rolling:.2%} +/- {std_rolling:.2%}

TRUE EXPECTED PERFORMANCE:
--------------------------
Point Estimate:             {np.mean(bootstrap_accs):.2%}
95% Confidence Interval:    [{ci_lower:.2%}, {ci_upper:.2%}]

vs PREVIOUSLY CLAIMED:
----------------------
Claimed on 2023-24 test:    62.11%
True expected performance:  {np.mean(bootstrap_accs):.2%}
Difference:                 {(np.mean(bootstrap_accs) - 0.6211)*100:+.2f}pp

INTERPRETATION:
---------------
The claimed 62.11% on the 2023-24 test set is a single-point estimate.
The TRUE expected performance on unseen future data is approximately:

    *** {np.mean(bootstrap_accs):.2%} ({ci_lower:.2%} - {ci_upper:.2%}) ***

This is the accuracy you should expect on new games.
""")

    # Key metrics
    print("=" * 80)
    print("KEY METRICS FOR PRODUCTION")
    print("=" * 80)

    overall_acc = accuracy_score(all_actual, (all_preds >= 0.5).astype(int))
    overall_auc = roc_auc_score(all_actual, all_preds)
    overall_ll = log_loss(all_actual, all_preds)
    overall_brier = brier_score_loss(all_actual, all_preds)

    print(f"""
Model: V7.6 (Top 59 features, C=0.01 LogReg)

Overall Metrics (out-of-sample):
  Accuracy:    {overall_acc:.4f} ({overall_acc:.2%})
  ROC-AUC:     {overall_auc:.4f}
  Log Loss:    {overall_ll:.4f}
  Brier Score: {overall_brier:.4f}

Confidence-Stratified Performance:
""")

    # Confidence buckets
    point_diffs = np.abs(all_preds - 0.5) * 100
    for name, low, high in [('High (15+)', 15, 100), ('Medium (10-15)', 10, 15),
                            ('Low (5-10)', 5, 10), ('Very Low (0-5)', 0, 5)]:
        mask = (point_diffs >= low) & (point_diffs < high)
        if mask.sum() > 0:
            acc = accuracy_score(all_actual[mask], (all_preds[mask] >= 0.5).astype(int))
            print(f"  {name}: {mask.sum():4d} games, {acc:.1%} accuracy")

    print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return {
        'season_forward': avg_acc,
        'monthly_expanding': avg_monthly,
        'rolling_window': avg_rolling,
        'point_estimate': np.mean(bootstrap_accs),
        'ci_lower': ci_lower,
        'ci_upper': ci_upper
    }


if __name__ == "__main__":
    main()
