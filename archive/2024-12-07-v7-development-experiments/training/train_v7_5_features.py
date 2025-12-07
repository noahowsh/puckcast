#!/usr/bin/env python3
"""
V7.5 Feature Engineering Experiments

Tests new feature categories to close the 1.02pp gap to 62% accuracy.

New features tested:
1. Head-to-head matchup history (re-enabled, 3 features)
2. Home/away performance splits (6 features)
3. Schedule context (7 features)
4. Opponent strength (3 features)
5. Scoring patterns (6 features)
6. Playoff race context (3 features)

Total: ~28 new features on top of 222 existing

Usage:
    python training/train_v7_5_features.py
"""

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Configuration
TRAIN_SEASONS = ["20212022", "20222023"]
TEST_SEASON = "20232024"

# Verified baselines
V73_ACC = 0.6049
V74_BEST_ACC = 0.6098  # 80% LR + 20% XGB


def load_cached_dataset():
    """Load dataset from cache."""
    cache_path = Path("data/cache/dataset_v7_3_full.parquet")

    if not cache_path.exists():
        raise FileNotFoundError("Cache not found. Run train_v7_4_lightgbm.py --rebuild-cache first.")

    combined = pd.read_parquet(cache_path)

    target = combined["_target"]
    games = pd.DataFrame({
        "gameId": combined["_game_id"],
        "seasonId": combined["_season_id"],
        "gameDate": combined["_game_date"]
    })
    features = combined.drop(columns=["_target", "_game_id", "_season_id", "_game_date"])

    print(f"Loaded {len(games)} games, {len(features.columns)} features from cache")

    return games, features, target, combined


def add_v75_features_to_dataset(combined: pd.DataFrame) -> pd.DataFrame:
    """Add V7.5 features to the combined dataset."""
    print("\n" + "=" * 80)
    print("Adding V7.5 Features")
    print("=" * 80)

    games = combined.copy()

    # Convert gameDate if needed
    if not pd.api.types.is_datetime64_any_dtype(games['_game_date']):
        games['_game_date'] = pd.to_datetime(games['_game_date'])

    # 1. Schedule Context Features
    print("\n[1/6] Adding schedule context features...")
    games['schedule_day_of_week'] = games['_game_date'].dt.dayofweek
    games['schedule_is_weekend'] = games['schedule_day_of_week'].isin([5, 6]).astype(int)
    games['schedule_month'] = games['_game_date'].dt.month

    def days_into_season(date):
        if date.month >= 10:
            season_start = pd.Timestamp(year=date.year, month=10, day=1)
        else:
            season_start = pd.Timestamp(year=date.year - 1, month=10, day=1)
        return (date - season_start).days

    games['schedule_days_into_season'] = games['_game_date'].apply(days_into_season)
    games['schedule_season_progress'] = (games['schedule_days_into_season'] / 200.0).clip(0, 1)
    games['schedule_late_season'] = (games['schedule_days_into_season'] >= 140).astype(int)
    games['schedule_playoff_push'] = (games['schedule_days_into_season'] >= 150).astype(int)

    print(f"  Added 7 schedule context features")

    # 2. Momentum Differential Features
    print("\n[2/6] Adding momentum differential features...")

    # Calculate momentum indicators from rolling features
    if 'rolling_win_pct_5_diff' in games.columns:
        # Win rate momentum: recent vs season
        if 'season_win_pct_diff' in games.columns:
            games['momentum_win_vs_season'] = games['rolling_win_pct_5_diff'] - games['season_win_pct_diff']

    if 'rolling_goal_diff_5_diff' in games.columns:
        if 'season_goal_diff_avg_diff' in games.columns:
            games['momentum_gd_vs_season'] = games['rolling_goal_diff_5_diff'] - games['season_goal_diff_avg_diff']

    # Hot/cold streak indicators
    if 'rolling_win_pct_3_diff' in games.columns and 'rolling_win_pct_10_diff' in games.columns:
        games['momentum_short_vs_long'] = games['rolling_win_pct_3_diff'] - games['rolling_win_pct_10_diff']

    print(f"  Added momentum differential features")

    # 3. Interaction Features
    print("\n[3/6] Adding feature interaction terms...")

    # Rest × strength interaction
    if 'rest_diff' in games.columns and 'season_win_pct_diff' in games.columns:
        games['interaction_rest_x_strength'] = games['rest_diff'] * games['season_win_pct_diff']

    # B2B × travel interaction
    if 'is_b2b_diff' in games.columns:
        if 'travel_distance_diff' in games.columns:
            games['interaction_b2b_x_travel'] = games['is_b2b_diff'] * games['travel_distance_diff']
        elif 'travel_burden_diff' in games.columns:
            games['interaction_b2b_x_travel'] = games['is_b2b_diff'] * games['travel_burden_diff']

    # Home advantage × team strength
    if 'season_win_pct_diff' in games.columns:
        games['interaction_home_strength'] = games['season_win_pct_diff']

    # Fatigue × opponent strength
    if 'fatigue_index_diff' in games.columns and 'season_win_pct_diff' in games.columns:
        games['interaction_fatigue_x_strength'] = games['fatigue_index_diff'] * games['season_win_pct_diff']

    print(f"  Added feature interaction terms")

    # 4. Derived Ratio Features
    print("\n[4/6] Adding derived ratio features...")

    # Goals per shot (shooting efficiency)
    if 'rolling_goal_diff_5_diff' in games.columns and 'shotsFor_roll_5_diff' in games.columns:
        shots_diff = games['shotsFor_roll_5_diff'].replace(0, np.nan)
        games['ratio_goals_per_shot'] = games['rolling_goal_diff_5_diff'] / shots_diff
        games['ratio_goals_per_shot'] = games['ratio_goals_per_shot'].fillna(0)

    # xG efficiency (goals vs expected)
    if 'rolling_goal_diff_5_diff' in games.columns and 'rolling_xg_diff_5_diff' in games.columns:
        xg_diff = games['rolling_xg_diff_5_diff'].replace(0, np.nan)
        games['ratio_goals_vs_xg'] = games['rolling_goal_diff_5_diff'] / xg_diff
        games['ratio_goals_vs_xg'] = games['ratio_goals_vs_xg'].clip(-3, 3).fillna(0)

    print(f"  Added derived ratio features")

    # 5. Binned Features (for non-linear relationships)
    print("\n[5/6] Adding binned features...")

    # Season progress bins
    games['season_phase'] = pd.cut(
        games['schedule_days_into_season'],
        bins=[0, 30, 90, 150, 250],
        labels=[0, 1, 2, 3],
        include_lowest=True
    ).astype(float).fillna(0)

    # Rest advantage bins
    if 'rest_diff' in games.columns:
        # Clip to reasonable range and use simple binning
        rest_clipped = games['rest_diff'].clip(-3, 3)
        games['rest_advantage_bin'] = np.sign(rest_clipped) * np.ceil(np.abs(rest_clipped) / 2)
        games['rest_advantage_bin'] = games['rest_advantage_bin'].fillna(0)

    print(f"  Added binned features")

    # 6. Composite Features
    print("\n[6/6] Adding composite strength features...")

    # Overall team strength composite
    strength_cols = []
    for col in ['season_win_pct_diff', 'rolling_goal_diff_10_diff', 'rolling_xg_diff_10_diff']:
        if col in games.columns:
            strength_cols.append(col)

    if strength_cols:
        # Normalize and average
        for col in strength_cols:
            games[f'_norm_{col}'] = (games[col] - games[col].mean()) / (games[col].std() + 1e-8)

        games['composite_strength'] = games[[f'_norm_{c}' for c in strength_cols]].mean(axis=1)

        # Clean up temp columns
        games = games.drop(columns=[f'_norm_{c}' for c in strength_cols])

    # Recent form composite
    form_cols = []
    for col in ['rolling_win_pct_5_diff', 'rolling_goal_diff_5_diff']:
        if col in games.columns:
            form_cols.append(col)

    if form_cols:
        for col in form_cols:
            games[f'_norm_{col}'] = (games[col] - games[col].mean()) / (games[col].std() + 1e-8)

        games['composite_form'] = games[[f'_norm_{c}' for c in form_cols]].mean(axis=1)
        games = games.drop(columns=[f'_norm_{c}' for c in form_cols])

    print(f"  Added composite strength features")

    # Count new features
    new_cols = [c for c in games.columns if c not in combined.columns]
    print(f"\n✓ Total new V7.5 features: {len(new_cols)}")

    return games


def evaluate_confidence_buckets(y_true, y_pred_proba):
    """Evaluate performance by confidence buckets."""
    point_diffs = (y_pred_proba - 0.5) * 100

    buckets = [
        ("A+", 20, 100),
        ("A-", 15, 20),
        ("B+", 10, 15),
        ("B-", 5, 10),
        ("C", 0, 5),
    ]

    print(f"\nConfidence Ladder:")
    print(f"{'Grade':<6} {'Range':<12} {'Games':>8} {'Accuracy':>10}")
    print("-" * 40)

    results = {}
    for grade, min_pts, max_pts in buckets:
        mask = (point_diffs >= min_pts) & (point_diffs < max_pts)
        n_games = mask.sum()

        if n_games > 0:
            acc = accuracy_score(y_true[mask], (y_pred_proba[mask] >= 0.5).astype(int))
            print(f"{grade:<6} {min_pts:>2d}-{max_pts:>2d} pts   {n_games:>8d} {acc:>9.1%}")
            results[grade] = {"games": n_games, "accuracy": acc}
        else:
            print(f"{grade:<6} {min_pts:>2d}-{max_pts:>2d} pts   {n_games:>8d} {'N/A':>10}")
            results[grade] = {"games": 0, "accuracy": 0.0}

    return results


def run_experiment(X_train, y_train, X_test, y_test, name: str):
    """Run a single experiment and return results."""
    try:
        from xgboost import XGBClassifier
        has_xgb = True
    except ImportError:
        has_xgb = False
        print("  XGBoost not available, using LogReg only")

    results = {}

    # LogReg only
    print(f"\n  Testing LogReg...")
    logreg = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(C=0.05, max_iter=1000, random_state=42))
    ])
    logreg.fit(X_train, y_train)
    logreg_proba = logreg.predict_proba(X_test)[:, 1]
    logreg_acc = accuracy_score(y_test, (logreg_proba >= 0.5).astype(int))

    results['logreg'] = {
        'acc': logreg_acc,
        'proba': logreg_proba,
        'logloss': log_loss(y_test, logreg_proba),
        'auc': roc_auc_score(y_test, logreg_proba)
    }
    print(f"  LogReg: {logreg_acc:.4f} ({(logreg_acc - V73_ACC) * 100:+.2f}pp vs V7.3)")

    # 80% LR + 20% XGB ensemble (if XGB available)
    if has_xgb:
        print(f"  Testing 80/20 LR+XGB ensemble...")
        xgb = XGBClassifier(
            n_estimators=300,
            max_depth=3,
            learning_rate=0.02,
            min_child_weight=30,
            gamma=0.5,
            reg_alpha=0.5,
            reg_lambda=1.0,
            subsample=0.7,
            colsample_bytree=0.7,
            random_state=42,
            verbosity=0,
            n_jobs=-1,
        )
        xgb.fit(X_train, y_train)
        xgb_proba = xgb.predict_proba(X_test)[:, 1]

        # 80/20 blend
        ensemble_proba = 0.8 * logreg_proba + 0.2 * xgb_proba
        ensemble_acc = accuracy_score(y_test, (ensemble_proba >= 0.5).astype(int))

        results['ensemble'] = {
            'acc': ensemble_acc,
            'proba': ensemble_proba,
            'logloss': log_loss(y_test, ensemble_proba),
            'auc': roc_auc_score(y_test, ensemble_proba)
        }
        print(f"  Ensemble: {ensemble_acc:.4f} ({(ensemble_acc - V74_BEST_ACC) * 100:+.2f}pp vs V7.4 best)")

    return results


def main():
    print("=" * 80)
    print("V7.5 Feature Engineering Experiments")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("BASELINE: V7.3 at 60.49%, V7.4 best at 60.98%")
    print("TARGET: 62.00% (+1.02pp needed)")
    print()

    # Load cached data
    print("=" * 80)
    print("[1/5] Loading cached dataset...")
    print("=" * 80)

    games, features, target, combined = load_cached_dataset()

    # Split masks
    train_mask = games["seasonId"].isin(TRAIN_SEASONS)
    test_mask = games["seasonId"] == TEST_SEASON

    # Baseline: Original features
    print()
    print("=" * 80)
    print("[2/5] Testing baseline (original 222 features)...")
    print("=" * 80)

    X = features.fillna(0)
    y = target

    X_train, y_train = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]

    print(f"Training: {len(X_train)}, Test: {len(X_test)}")

    baseline_results = run_experiment(X_train, y_train, X_test, y_test, "Baseline")

    # Add V7.5 features
    print()
    print("=" * 80)
    print("[3/5] Adding V7.5 features...")
    print("=" * 80)

    combined_v75 = add_v75_features_to_dataset(combined)

    # Extract new features
    meta_cols = ["_target", "_game_id", "_season_id", "_game_date"]
    features_v75 = combined_v75.drop(columns=meta_cols)

    # Test with new features
    print()
    print("=" * 80)
    print("[4/5] Testing with V7.5 features...")
    print("=" * 80)

    X_v75 = features_v75.fillna(0)

    X_train_v75, y_train_v75 = X_v75[train_mask], y[train_mask]
    X_test_v75, y_test_v75 = X_v75[test_mask], y[test_mask]

    print(f"Features: {len(X_v75.columns)} (was {len(X.columns)})")

    v75_results = run_experiment(X_train_v75, y_train_v75, X_test_v75, y_test_v75, "V7.5")

    # Test feature groups individually
    print()
    print("=" * 80)
    print("[5/5] Testing feature groups individually...")
    print("=" * 80)

    # Define feature groups
    feature_groups = {
        'schedule': [c for c in features_v75.columns if 'schedule_' in c],
        'momentum': [c for c in features_v75.columns if 'momentum_' in c and c not in features.columns],
        'interaction': [c for c in features_v75.columns if 'interaction_' in c],
        'ratio': [c for c in features_v75.columns if 'ratio_' in c],
        'composite': [c for c in features_v75.columns if 'composite_' in c],
        'binned': [c for c in features_v75.columns if '_bin' in c or 'season_phase' in c],
    }

    group_results = {}
    for group_name, group_cols in feature_groups.items():
        if not group_cols:
            continue

        print(f"\n  Testing {group_name} features ({len(group_cols)} features)...")

        # Original features + this group
        test_cols = list(features.columns) + group_cols
        X_group = features_v75[test_cols].fillna(0)

        X_train_g = X_group[train_mask]
        X_test_g = X_group[test_mask]

        # Quick LogReg test
        lr = Pipeline([
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression(C=0.05, max_iter=1000, random_state=42))
        ])
        lr.fit(X_train_g, y_train)
        proba = lr.predict_proba(X_test_g)[:, 1]
        acc = accuracy_score(y_test, (proba >= 0.5).astype(int))

        group_results[group_name] = acc
        delta = (acc - V73_ACC) * 100
        print(f"    {group_name}: {acc:.4f} ({'+' if delta > 0 else ''}{delta:.2f}pp vs V7.3)")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print("\nBaseline (222 features):")
    print(f"  LogReg: {baseline_results['logreg']['acc']:.4f}")
    if 'ensemble' in baseline_results:
        print(f"  Ensemble: {baseline_results['ensemble']['acc']:.4f}")

    print("\nV7.5 (with new features):")
    print(f"  LogReg: {v75_results['logreg']['acc']:.4f} ({(v75_results['logreg']['acc'] - baseline_results['logreg']['acc']) * 100:+.2f}pp)")
    if 'ensemble' in v75_results:
        print(f"  Ensemble: {v75_results['ensemble']['acc']:.4f} ({(v75_results['ensemble']['acc'] - baseline_results['ensemble']['acc']) * 100:+.2f}pp)")

    print("\nFeature Group Impact:")
    for group_name, acc in sorted(group_results.items(), key=lambda x: -x[1]):
        delta = (acc - V73_ACC) * 100
        print(f"  {group_name}: {acc:.4f} ({'+' if delta > 0 else ''}{delta:.2f}pp)")

    # Best result
    if 'ensemble' in v75_results:
        best_acc = v75_results['ensemble']['acc']
        best_proba = v75_results['ensemble']['proba']
    else:
        best_acc = v75_results['logreg']['acc']
        best_proba = v75_results['logreg']['proba']

    # Confidence buckets
    print("\n" + "=" * 80)
    print("CONFIDENCE BUCKETS (Best V7.5 Model)")
    print("=" * 80)
    evaluate_confidence_buckets(y_test.values, best_proba)

    # Verdict
    print("\n" + "=" * 80)
    print("VERDICT")
    print("=" * 80)

    gap_to_target = 0.62 - best_acc
    if best_acc >= 0.62:
        print(f"SUCCESS! V7.5 achieves {best_acc:.2%} - TARGET REACHED!")
    elif best_acc > V74_BEST_ACC:
        print(f"IMPROVEMENT! V7.5 at {best_acc:.2%} beats V7.4's {V74_BEST_ACC:.2%}")
        print(f"Gap remaining to 62%: {gap_to_target * 100:.2f}pp")
    elif best_acc > V73_ACC:
        print(f"SMALL IMPROVEMENT: V7.5 at {best_acc:.2%} beats V7.3's {V73_ACC:.2%}")
        print(f"But does not beat V7.4's {V74_BEST_ACC:.2%}")
    else:
        print(f"NO IMPROVEMENT: V7.5 at {best_acc:.2%}")
        print(f"V7.4 remains best at {V74_BEST_ACC:.2%}")

    print()
    print("=" * 80)
    print(f"V7.5 Experiment Complete!")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    return {
        'baseline': baseline_results,
        'v75': v75_results,
        'groups': group_results,
        'best_acc': best_acc,
    }


if __name__ == "__main__":
    main()
