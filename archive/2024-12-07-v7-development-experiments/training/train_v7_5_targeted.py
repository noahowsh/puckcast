#!/usr/bin/env python3
"""
V7.5 Targeted Feature Experiments

Based on initial V7.5 results, only these feature groups showed improvement:
- Ratio features: +0.32pp (best!)
- Momentum features: +0.08pp

This script tests targeted combinations to find optimal feature additions.

Usage:
    python training/train_v7_5_targeted.py
"""

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Configuration
TRAIN_SEASONS = ["20212022", "20222023"]
TEST_SEASON = "20232024"

# Baselines
V73_ACC = 0.6049
V74_BEST_ACC = 0.6098


def load_cached_dataset():
    """Load dataset from cache."""
    cache_path = Path("data/cache/dataset_v7_3_full.parquet")

    if not cache_path.exists():
        raise FileNotFoundError("Cache not found.")

    combined = pd.read_parquet(cache_path)

    target = combined["_target"]
    games = pd.DataFrame({
        "gameId": combined["_game_id"],
        "seasonId": combined["_season_id"],
        "gameDate": combined["_game_date"]
    })
    features = combined.drop(columns=["_target", "_game_id", "_season_id", "_game_date"])

    return games, features, target, combined


def add_ratio_features(games: pd.DataFrame) -> pd.DataFrame:
    """Add only the ratio features that showed improvement."""
    games = games.copy()

    # Goals per shot efficiency
    if 'rolling_goal_diff_5_diff' in games.columns:
        if 'shotsFor_roll_5_diff' in games.columns:
            shots = games['shotsFor_roll_5_diff'].replace(0, np.nan)
            games['ratio_goals_per_shot_5'] = games['rolling_goal_diff_5_diff'] / shots
            games['ratio_goals_per_shot_5'] = games['ratio_goals_per_shot_5'].fillna(0).clip(-1, 1)

        if 'shotsFor_roll_10_diff' in games.columns:
            shots = games['shotsFor_roll_10_diff'].replace(0, np.nan)
            games['ratio_goals_per_shot_10'] = games['rolling_goal_diff_10_diff'] / shots
            games['ratio_goals_per_shot_10'] = games['ratio_goals_per_shot_10'].fillna(0).clip(-1, 1)

    # xG efficiency (actual goals vs expected)
    if 'rolling_goal_diff_5_diff' in games.columns and 'rolling_xg_diff_5_diff' in games.columns:
        xg = games['rolling_xg_diff_5_diff'].replace(0, np.nan)
        games['ratio_goals_vs_xg_5'] = games['rolling_goal_diff_5_diff'] / xg
        games['ratio_goals_vs_xg_5'] = games['ratio_goals_vs_xg_5'].clip(-3, 3).fillna(0)

    if 'rolling_goal_diff_10_diff' in games.columns and 'rolling_xg_diff_10_diff' in games.columns:
        xg = games['rolling_xg_diff_10_diff'].replace(0, np.nan)
        games['ratio_goals_vs_xg_10'] = games['rolling_goal_diff_10_diff'] / xg
        games['ratio_goals_vs_xg_10'] = games['ratio_goals_vs_xg_10'].clip(-3, 3).fillna(0)

    # Shot quality ratio (high danger shots / total shots)
    if 'rolling_high_danger_shots_5_diff' in games.columns and 'shotsFor_roll_5_diff' in games.columns:
        shots = games['shotsFor_roll_5_diff'].replace(0, np.nan)
        games['ratio_hd_shots_5'] = games['rolling_high_danger_shots_5_diff'] / shots
        games['ratio_hd_shots_5'] = games['ratio_hd_shots_5'].fillna(0).clip(-1, 1)

    return games


def add_momentum_diff_features(games: pd.DataFrame) -> pd.DataFrame:
    """Add momentum differential features."""
    games = games.copy()

    # Short-term vs long-term momentum
    if 'rolling_win_pct_3_diff' in games.columns and 'rolling_win_pct_10_diff' in games.columns:
        games['momentum_short_vs_long'] = games['rolling_win_pct_3_diff'] - games['rolling_win_pct_10_diff']

    if 'rolling_goal_diff_3_diff' in games.columns and 'rolling_goal_diff_10_diff' in games.columns:
        games['momentum_gd_short_vs_long'] = games['rolling_goal_diff_3_diff'] - games['rolling_goal_diff_10_diff']

    # Recent form vs season average
    if 'rolling_win_pct_5_diff' in games.columns and 'season_win_pct_diff' in games.columns:
        games['momentum_recent_vs_season'] = games['rolling_win_pct_5_diff'] - games['season_win_pct_diff']

    return games


def add_advanced_features(games: pd.DataFrame) -> pd.DataFrame:
    """Add advanced analytical features."""
    games = games.copy()

    # PDO-style luck indicator
    # High goals vs xG + low goals against vs xGA = lucky
    if 'rolling_xg_for_5_diff' in games.columns:
        # Over/underperformance vs expected
        if 'rolling_goal_diff_5_diff' in games.columns:
            games['luck_indicator_5'] = (
                games['rolling_goal_diff_5_diff'] - games['rolling_xg_diff_5_diff']
            )

    # Consistency measure (std of recent performance)
    # Lower variance = more consistent = more predictable
    # This is approximated by gap between 3-game and 10-game rolling
    if 'rolling_goal_diff_3_diff' in games.columns and 'rolling_goal_diff_10_diff' in games.columns:
        games['consistency_gd'] = abs(
            games['rolling_goal_diff_3_diff'] - games['rolling_goal_diff_10_diff']
        )

    # Win margin quality (are wins close or blowouts?)
    # Approximated by goal diff magnitude
    if 'rolling_goal_diff_5_diff' in games.columns and 'rolling_win_pct_5_diff' in games.columns:
        # High win % but low goal diff = close wins
        # High win % and high goal diff = dominant wins
        win_pct = games['rolling_win_pct_5_diff'].clip(-1, 1)
        gd = games['rolling_goal_diff_5_diff'].clip(-3, 3)
        games['dominance_score'] = win_pct * gd

    return games


def run_experiment(X_train, y_train, X_test, y_test, name: str):
    """Run experiment and return results."""
    try:
        from xgboost import XGBClassifier
        has_xgb = True
    except ImportError:
        has_xgb = False

    results = {}

    # LogReg
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

    # 80/20 LR+XGB
    if has_xgb:
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

        ensemble_proba = 0.8 * logreg_proba + 0.2 * xgb_proba
        ensemble_acc = accuracy_score(y_test, (ensemble_proba >= 0.5).astype(int))

        results['ensemble'] = {
            'acc': ensemble_acc,
            'proba': ensemble_proba,
            'logloss': log_loss(y_test, ensemble_proba),
            'auc': roc_auc_score(y_test, ensemble_proba)
        }

    return results


def main():
    print("=" * 80)
    print("V7.5 Targeted Feature Experiments")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load data
    games, features, target, combined = load_cached_dataset()
    print(f"Loaded {len(games)} games, {len(features.columns)} features")

    train_mask = games["seasonId"].isin(TRAIN_SEASONS)
    test_mask = games["seasonId"] == TEST_SEASON

    y_train = target[train_mask]
    y_test = target[test_mask]

    # Baseline
    print("\n" + "=" * 80)
    print("BASELINE")
    print("=" * 80)

    X_baseline = features.fillna(0)
    baseline = run_experiment(
        X_baseline[train_mask], y_train,
        X_baseline[test_mask], y_test,
        "Baseline"
    )
    print(f"LogReg: {baseline['logreg']['acc']:.4f}")
    print(f"Ensemble: {baseline['ensemble']['acc']:.4f}")

    # Test feature combinations
    experiments = []

    # 1. Ratio features only
    print("\n" + "=" * 80)
    print("EXPERIMENT 1: Ratio Features Only")
    print("=" * 80)

    combined_ratio = add_ratio_features(combined.copy())
    new_ratio_cols = [c for c in combined_ratio.columns if c.startswith('ratio_')]
    print(f"New features: {new_ratio_cols}")

    features_ratio = combined_ratio.drop(columns=["_target", "_game_id", "_season_id", "_game_date"]).fillna(0)

    result_ratio = run_experiment(
        features_ratio[train_mask], y_train,
        features_ratio[test_mask], y_test,
        "Ratio"
    )
    print(f"LogReg: {result_ratio['logreg']['acc']:.4f} ({(result_ratio['logreg']['acc'] - V73_ACC) * 100:+.2f}pp)")
    print(f"Ensemble: {result_ratio['ensemble']['acc']:.4f} ({(result_ratio['ensemble']['acc'] - V74_BEST_ACC) * 100:+.2f}pp)")

    experiments.append(("Ratio", result_ratio, new_ratio_cols))

    # 2. Momentum features only
    print("\n" + "=" * 80)
    print("EXPERIMENT 2: Momentum Features Only")
    print("=" * 80)

    combined_momentum = add_momentum_diff_features(combined.copy())
    new_momentum_cols = [c for c in combined_momentum.columns if c.startswith('momentum_')]
    print(f"New features: {new_momentum_cols}")

    features_momentum = combined_momentum.drop(columns=["_target", "_game_id", "_season_id", "_game_date"]).fillna(0)

    result_momentum = run_experiment(
        features_momentum[train_mask], y_train,
        features_momentum[test_mask], y_test,
        "Momentum"
    )
    print(f"LogReg: {result_momentum['logreg']['acc']:.4f} ({(result_momentum['logreg']['acc'] - V73_ACC) * 100:+.2f}pp)")
    print(f"Ensemble: {result_momentum['ensemble']['acc']:.4f} ({(result_momentum['ensemble']['acc'] - V74_BEST_ACC) * 100:+.2f}pp)")

    experiments.append(("Momentum", result_momentum, new_momentum_cols))

    # 3. Advanced analytical features
    print("\n" + "=" * 80)
    print("EXPERIMENT 3: Advanced Analytical Features")
    print("=" * 80)

    combined_advanced = add_advanced_features(combined.copy())
    new_advanced_cols = [c for c in combined_advanced.columns if c in ['luck_indicator_5', 'consistency_gd', 'dominance_score']]
    print(f"New features: {new_advanced_cols}")

    features_advanced = combined_advanced.drop(columns=["_target", "_game_id", "_season_id", "_game_date"]).fillna(0)

    result_advanced = run_experiment(
        features_advanced[train_mask], y_train,
        features_advanced[test_mask], y_test,
        "Advanced"
    )
    print(f"LogReg: {result_advanced['logreg']['acc']:.4f} ({(result_advanced['logreg']['acc'] - V73_ACC) * 100:+.2f}pp)")
    print(f"Ensemble: {result_advanced['ensemble']['acc']:.4f} ({(result_advanced['ensemble']['acc'] - V74_BEST_ACC) * 100:+.2f}pp)")

    experiments.append(("Advanced", result_advanced, new_advanced_cols))

    # 4. Ratio + Momentum combination
    print("\n" + "=" * 80)
    print("EXPERIMENT 4: Ratio + Momentum Combined")
    print("=" * 80)

    combined_rm = add_ratio_features(combined.copy())
    combined_rm = add_momentum_diff_features(combined_rm)

    features_rm = combined_rm.drop(columns=["_target", "_game_id", "_season_id", "_game_date"]).fillna(0)

    result_rm = run_experiment(
        features_rm[train_mask], y_train,
        features_rm[test_mask], y_test,
        "Ratio+Momentum"
    )
    print(f"LogReg: {result_rm['logreg']['acc']:.4f} ({(result_rm['logreg']['acc'] - V73_ACC) * 100:+.2f}pp)")
    print(f"Ensemble: {result_rm['ensemble']['acc']:.4f} ({(result_rm['ensemble']['acc'] - V74_BEST_ACC) * 100:+.2f}pp)")

    experiments.append(("Ratio+Momentum", result_rm, new_ratio_cols + new_momentum_cols))

    # 5. All beneficial features
    print("\n" + "=" * 80)
    print("EXPERIMENT 5: All Beneficial Features")
    print("=" * 80)

    combined_all = add_ratio_features(combined.copy())
    combined_all = add_momentum_diff_features(combined_all)
    combined_all = add_advanced_features(combined_all)

    features_all = combined_all.drop(columns=["_target", "_game_id", "_season_id", "_game_date"]).fillna(0)

    result_all = run_experiment(
        features_all[train_mask], y_train,
        features_all[test_mask], y_test,
        "All"
    )
    print(f"LogReg: {result_all['logreg']['acc']:.4f} ({(result_all['logreg']['acc'] - V73_ACC) * 100:+.2f}pp)")
    print(f"Ensemble: {result_all['ensemble']['acc']:.4f} ({(result_all['ensemble']['acc'] - V74_BEST_ACC) * 100:+.2f}pp)")

    experiments.append(("All Beneficial", result_all, []))

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(f"\n{'Experiment':<20} {'LogReg':>10} {'Ensemble':>10} {'vs V7.4':>10}")
    print("-" * 55)
    print(f"{'Baseline':<20} {baseline['logreg']['acc']:>10.4f} {baseline['ensemble']['acc']:>10.4f} {'baseline':>10}")

    best_name = "Baseline"
    best_acc = baseline['ensemble']['acc']

    for name, result, _ in experiments:
        delta = (result['ensemble']['acc'] - V74_BEST_ACC) * 100
        print(f"{name:<20} {result['logreg']['acc']:>10.4f} {result['ensemble']['acc']:>10.4f} {delta:>+9.2f}pp")

        if result['ensemble']['acc'] > best_acc:
            best_acc = result['ensemble']['acc']
            best_name = name

    # Verdict
    print("\n" + "=" * 80)
    print("VERDICT")
    print("=" * 80)

    if best_acc > V74_BEST_ACC:
        print(f"NEW BEST: {best_name} at {best_acc:.4f} ({(best_acc - V74_BEST_ACC) * 100:+.2f}pp vs V7.4)")
    else:
        print(f"NO IMPROVEMENT: V7.4 remains best at {V74_BEST_ACC:.4f}")

    print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
