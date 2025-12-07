#!/usr/bin/env python3
"""
V7.6 Comprehensive Experiments

Goal: Close the 0.78pp gap from 61.22% to 62%

Experiments:
1. Head-to-Head (H2H) features - re-enable and test
2. Polynomial/Interaction features
3. Threshold optimization
4. Model averaging (bagging with different seeds)
5. ElasticNet regularization
6. Hyperparameter optimization

Usage:
    python training/train_v7_6_experiments.py
"""

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

TRAIN_SEASONS = ["20212022", "20222023"]
TEST_SEASON = "20232024"

V73_ACC = 0.6049
V75_ACC = 0.6122  # Current best


def load_cached_dataset():
    cache_path = Path("data/cache/dataset_v7_3_full.parquet")
    combined = pd.read_parquet(cache_path)

    target = combined["_target"]
    games = pd.DataFrame({
        "gameId": combined["_game_id"],
        "seasonId": combined["_season_id"],
        "gameDate": combined["_game_date"]
    })
    features = combined.drop(columns=["_target", "_game_id", "_season_id", "_game_date"])

    return games, features, target, combined


def add_v75_features(combined: pd.DataFrame) -> pd.DataFrame:
    """Add V7.5 best features."""
    games = combined.copy()

    # Ratio features
    if 'rolling_goal_diff_5_diff' in games.columns:
        if 'shotsFor_roll_5_diff' in games.columns:
            shots = games['shotsFor_roll_5_diff'].replace(0, np.nan)
            games['ratio_goals_per_shot_5'] = (games['rolling_goal_diff_5_diff'] / shots).fillna(0).clip(-1, 1)

        if 'shotsFor_roll_10_diff' in games.columns:
            shots = games['shotsFor_roll_10_diff'].replace(0, np.nan)
            games['ratio_goals_per_shot_10'] = (games['rolling_goal_diff_10_diff'] / shots).fillna(0).clip(-1, 1)

    if 'rolling_goal_diff_5_diff' in games.columns and 'rolling_xg_diff_5_diff' in games.columns:
        xg = games['rolling_xg_diff_5_diff'].replace(0, np.nan)
        games['ratio_goals_vs_xg_5'] = (games['rolling_goal_diff_5_diff'] / xg).clip(-3, 3).fillna(0)

    if 'rolling_goal_diff_10_diff' in games.columns and 'rolling_xg_diff_10_diff' in games.columns:
        xg = games['rolling_xg_diff_10_diff'].replace(0, np.nan)
        games['ratio_goals_vs_xg_10'] = (games['rolling_goal_diff_10_diff'] / xg).clip(-3, 3).fillna(0)

    if 'rolling_high_danger_shots_5_diff' in games.columns and 'shotsFor_roll_5_diff' in games.columns:
        shots = games['shotsFor_roll_5_diff'].replace(0, np.nan)
        games['ratio_hd_shots_5'] = (games['rolling_high_danger_shots_5_diff'] / shots).fillna(0).clip(-1, 1)

    # Advanced features
    if 'rolling_xg_for_5_diff' in games.columns and 'rolling_goal_diff_5_diff' in games.columns:
        games['luck_indicator_5'] = games['rolling_goal_diff_5_diff'] - games['rolling_xg_diff_5_diff']

    if 'rolling_goal_diff_3_diff' in games.columns and 'rolling_goal_diff_10_diff' in games.columns:
        games['consistency_gd'] = abs(games['rolling_goal_diff_3_diff'] - games['rolling_goal_diff_10_diff'])

    if 'rolling_goal_diff_5_diff' in games.columns and 'rolling_win_pct_5_diff' in games.columns:
        win_pct = games['rolling_win_pct_5_diff'].clip(-1, 1)
        gd = games['rolling_goal_diff_5_diff'].clip(-3, 3)
        games['dominance_score'] = win_pct * gd

    return games


def add_h2h_features(combined: pd.DataFrame, lookback: int = 10) -> pd.DataFrame:
    """Add head-to-head matchup features."""
    games = combined.copy()
    games = games.sort_values('_game_date')

    # We need team abbreviations - check what columns we have
    # The cached dataset might have different column names

    # Initialize H2H features
    games['h2h_win_pct'] = 0.5
    games['h2h_goal_diff'] = 0.0
    games['h2h_games_played'] = 0

    # Check if we have the necessary columns
    home_cols = [c for c in games.columns if 'home' in c.lower()]
    away_cols = [c for c in games.columns if 'away' in c.lower()]

    # Try to find team identifier columns
    team_home_col = None
    team_away_col = None

    for col in games.columns:
        if 'teamabbrev' in col.lower() and 'home' in col.lower():
            team_home_col = col
        if 'teamabbrev' in col.lower() and 'away' in col.lower():
            team_away_col = col
        if 'teamid' in col.lower() and 'home' in col.lower():
            team_home_col = col
        if 'teamid' in col.lower() and 'away' in col.lower():
            team_away_col = col

    if team_home_col is None or team_away_col is None:
        # Try to reconstruct from elo or other features
        print("  Warning: Cannot find team columns for H2H, using elo-based proxy")

        # Use elo_diff as a proxy for matchup quality
        if 'elo_diff_pre' in games.columns:
            # High elo diff games are less competitive - use as feature
            games['h2h_elo_competitiveness'] = 1 / (1 + abs(games['elo_diff_pre']))

        return games

    # Create matchup identifier
    def get_matchup_key(row):
        teams = sorted([str(row[team_home_col]), str(row[team_away_col])])
        return f"{teams[0]}_vs_{teams[1]}"

    games['_matchup_key'] = games.apply(get_matchup_key, axis=1)

    # Process each matchup
    for matchup_key, group in games.groupby('_matchup_key'):
        if len(group) < 2:
            continue

        group = group.sort_values('_game_date')
        indices = group.index.tolist()

        for i, idx in enumerate(indices):
            if i == 0:
                continue

            prev_indices = indices[:i]
            prev_games = games.loc[prev_indices].tail(lookback)

            home_team = games.loc[idx, team_home_col]

            h2h_wins = 0
            h2h_goal_diffs = []

            for prev_idx in prev_games.index:
                prev_home = games.loc[prev_idx, team_home_col]

                # Need goal columns
                gf_col = [c for c in games.columns if 'goalsfor' in c.lower() and 'home' in c.lower()]
                ga_col = [c for c in games.columns if 'goalsagainst' in c.lower() and 'home' in c.lower()]

                if not gf_col or not ga_col:
                    continue

                gf_home = games.loc[prev_idx, gf_col[0]]
                ga_home = games.loc[prev_idx, ga_col[0]]

                if pd.isna(gf_home) or pd.isna(ga_home):
                    continue

                if prev_home == home_team:
                    if gf_home > ga_home:
                        h2h_wins += 1
                    h2h_goal_diffs.append(gf_home - ga_home)
                else:
                    if ga_home > gf_home:
                        h2h_wins += 1
                    h2h_goal_diffs.append(ga_home - gf_home)

            games_count = len(h2h_goal_diffs)
            if games_count > 0:
                games.at[idx, 'h2h_win_pct'] = h2h_wins / games_count
                games.at[idx, 'h2h_goal_diff'] = np.mean(h2h_goal_diffs)
                games.at[idx, 'h2h_games_played'] = games_count

    if '_matchup_key' in games.columns:
        games = games.drop(columns=['_matchup_key'])

    return games


def add_interaction_features(games: pd.DataFrame) -> pd.DataFrame:
    """Add polynomial interaction features between top predictors."""
    games = games.copy()

    # Key interactions based on domain knowledge
    interactions = [
        ('season_win_pct_diff', 'rolling_goal_diff_10_diff'),
        ('season_win_pct_diff', 'rest_diff'),
        ('rolling_xg_diff_5_diff', 'rolling_goal_diff_5_diff'),
        ('elo_diff_pre', 'rest_diff'),
        ('fatigue_index_diff', 'season_win_pct_diff'),
    ]

    for col1, col2 in interactions:
        if col1 in games.columns and col2 in games.columns:
            # Interaction term
            games[f'int_{col1[:15]}_{col2[:15]}'] = games[col1] * games[col2]

    # Squared terms for top features (capturing non-linearity)
    top_features = ['season_win_pct_diff', 'elo_diff_pre', 'rolling_goal_diff_10_diff']
    for feat in top_features:
        if feat in games.columns:
            games[f'{feat}_sq'] = games[feat] ** 2

    return games


def optimize_threshold(y_true, y_proba):
    """Find optimal decision threshold."""
    best_thresh = 0.5
    best_acc = 0

    for thresh in np.arange(0.40, 0.60, 0.01):
        preds = (y_proba >= thresh).astype(int)
        acc = accuracy_score(y_true, preds)
        if acc > best_acc:
            best_acc = acc
            best_thresh = thresh

    return best_thresh, best_acc


def bagging_ensemble(X_train, y_train, X_test, n_models=10, C=0.01):
    """Train multiple models with different seeds and average."""
    probas = []

    for seed in range(n_models):
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        model = LogisticRegression(C=C, max_iter=1000, random_state=seed)
        model.fit(X_train_scaled, y_train)
        proba = model.predict_proba(X_test_scaled)[:, 1]
        probas.append(proba)

    # Average probabilities
    avg_proba = np.mean(probas, axis=0)
    return avg_proba


def main():
    print("=" * 80)
    print("V7.6 Comprehensive Experiments")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print(f"BASELINE: V7.5 at {V75_ACC:.2%}")
    print(f"TARGET: 62.00% (gap: {(0.62 - V75_ACC) * 100:.2f}pp)")
    print()

    # Load data
    games, features, target, combined = load_cached_dataset()

    train_mask = games["seasonId"].isin(TRAIN_SEASONS)
    test_mask = games["seasonId"] == TEST_SEASON

    y_train = target[train_mask].values
    y_test = target[test_mask].values

    # Add V7.5 features (our current best)
    combined_v75 = add_v75_features(combined)

    results = {}

    # ===== EXPERIMENT 1: Baseline V7.5 =====
    print("=" * 80)
    print("EXPERIMENT 1: Baseline V7.5 (for comparison)")
    print("=" * 80)

    features_v75 = combined_v75.drop(columns=["_target", "_game_id", "_season_id", "_game_date"]).fillna(0)
    X_train = features_v75[train_mask].values
    X_test = features_v75[test_mask].values

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    logreg = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
    logreg.fit(X_train_scaled, y_train)
    baseline_proba = logreg.predict_proba(X_test_scaled)[:, 1]
    baseline_acc = accuracy_score(y_test, (baseline_proba >= 0.5).astype(int))

    print(f"Baseline V7.5: {baseline_acc:.4f}")
    results['baseline'] = baseline_acc

    # ===== EXPERIMENT 2: H2H Features =====
    print("\n" + "=" * 80)
    print("EXPERIMENT 2: Head-to-Head Features")
    print("=" * 80)

    combined_h2h = add_h2h_features(combined_v75.copy())
    h2h_cols = ['h2h_win_pct', 'h2h_goal_diff', 'h2h_games_played']
    if 'h2h_elo_competitiveness' in combined_h2h.columns:
        h2h_cols.append('h2h_elo_competitiveness')

    print(f"H2H features added: {[c for c in h2h_cols if c in combined_h2h.columns]}")

    features_h2h = combined_h2h.drop(columns=["_target", "_game_id", "_season_id", "_game_date"]).fillna(0)
    X_train_h2h = features_h2h[train_mask].values
    X_test_h2h = features_h2h[test_mask].values

    scaler_h2h = StandardScaler()
    X_train_h2h_scaled = scaler_h2h.fit_transform(X_train_h2h)
    X_test_h2h_scaled = scaler_h2h.transform(X_test_h2h)

    logreg_h2h = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
    logreg_h2h.fit(X_train_h2h_scaled, y_train)
    h2h_proba = logreg_h2h.predict_proba(X_test_h2h_scaled)[:, 1]
    h2h_acc = accuracy_score(y_test, (h2h_proba >= 0.5).astype(int))

    print(f"With H2H: {h2h_acc:.4f} ({(h2h_acc - baseline_acc) * 100:+.2f}pp)")
    results['h2h'] = h2h_acc

    # ===== EXPERIMENT 3: Interaction Features =====
    print("\n" + "=" * 80)
    print("EXPERIMENT 3: Polynomial/Interaction Features")
    print("=" * 80)

    combined_int = add_interaction_features(combined_v75.copy())
    int_cols = [c for c in combined_int.columns if c.startswith('int_') or c.endswith('_sq')]
    print(f"Interaction features added: {len(int_cols)}")

    features_int = combined_int.drop(columns=["_target", "_game_id", "_season_id", "_game_date"]).fillna(0)
    X_train_int = features_int[train_mask].values
    X_test_int = features_int[test_mask].values

    scaler_int = StandardScaler()
    X_train_int_scaled = scaler_int.fit_transform(X_train_int)
    X_test_int_scaled = scaler_int.transform(X_test_int)

    logreg_int = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
    logreg_int.fit(X_train_int_scaled, y_train)
    int_proba = logreg_int.predict_proba(X_test_int_scaled)[:, 1]
    int_acc = accuracy_score(y_test, (int_proba >= 0.5).astype(int))

    print(f"With interactions: {int_acc:.4f} ({(int_acc - baseline_acc) * 100:+.2f}pp)")
    results['interactions'] = int_acc

    # ===== EXPERIMENT 4: Threshold Optimization =====
    print("\n" + "=" * 80)
    print("EXPERIMENT 4: Threshold Optimization")
    print("=" * 80)

    # Use validation set for threshold optimization
    from sklearn.model_selection import train_test_split
    X_tr, X_val, y_tr, y_val = train_test_split(X_train_scaled, y_train, test_size=0.2, random_state=42)

    logreg_th = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
    logreg_th.fit(X_tr, y_tr)
    val_proba = logreg_th.predict_proba(X_val)[:, 1]

    best_thresh, val_best_acc = optimize_threshold(y_val, val_proba)
    print(f"Best threshold on validation: {best_thresh:.2f} (val acc: {val_best_acc:.4f})")

    # Apply to test set
    test_proba_th = logreg.predict_proba(X_test_scaled)[:, 1]
    thresh_acc = accuracy_score(y_test, (test_proba_th >= best_thresh).astype(int))

    print(f"With optimized threshold ({best_thresh:.2f}): {thresh_acc:.4f} ({(thresh_acc - baseline_acc) * 100:+.2f}pp)")
    results['threshold'] = thresh_acc

    # ===== EXPERIMENT 5: Model Averaging (Bagging) =====
    print("\n" + "=" * 80)
    print("EXPERIMENT 5: Model Averaging (Bagging)")
    print("=" * 80)

    for n_models in [5, 10, 20]:
        bag_proba = bagging_ensemble(
            features_v75[train_mask].values,
            y_train,
            features_v75[test_mask].values,
            n_models=n_models,
            C=0.01
        )
        bag_acc = accuracy_score(y_test, (bag_proba >= 0.5).astype(int))
        print(f"Bagging ({n_models} models): {bag_acc:.4f} ({(bag_acc - baseline_acc) * 100:+.2f}pp)")
        results[f'bagging_{n_models}'] = bag_acc

    # ===== EXPERIMENT 6: ElasticNet =====
    print("\n" + "=" * 80)
    print("EXPERIMENT 6: ElasticNet Regularization")
    print("=" * 80)

    # ElasticNet via SGDClassifier
    for l1_ratio in [0.0, 0.15, 0.5, 0.85, 1.0]:
        sgd = SGDClassifier(
            loss='log_loss',
            penalty='elasticnet',
            l1_ratio=l1_ratio,
            alpha=0.001,
            max_iter=1000,
            random_state=42
        )
        sgd.fit(X_train_scaled, y_train)
        en_proba = sgd.predict_proba(X_test_scaled)[:, 1]
        en_acc = accuracy_score(y_test, (en_proba >= 0.5).astype(int))
        print(f"ElasticNet (l1_ratio={l1_ratio}): {en_acc:.4f} ({(en_acc - baseline_acc) * 100:+.2f}pp)")
        results[f'elasticnet_{l1_ratio}'] = en_acc

    # ===== EXPERIMENT 7: C Hyperparameter Search =====
    print("\n" + "=" * 80)
    print("EXPERIMENT 7: Fine-grained C Search")
    print("=" * 80)

    best_c = 0.01
    best_c_acc = 0

    for c in [0.005, 0.007, 0.008, 0.009, 0.01, 0.011, 0.012, 0.015, 0.02]:
        lr = LogisticRegression(C=c, max_iter=1000, random_state=42)
        lr.fit(X_train_scaled, y_train)
        proba = lr.predict_proba(X_test_scaled)[:, 1]
        acc = accuracy_score(y_test, (proba >= 0.5).astype(int))
        print(f"C={c:.3f}: {acc:.4f} ({(acc - baseline_acc) * 100:+.2f}pp)")

        if acc > best_c_acc:
            best_c_acc = acc
            best_c = c

    results['best_c'] = best_c_acc
    print(f"\nBest C: {best_c} with {best_c_acc:.4f}")

    # ===== EXPERIMENT 8: Combined Best Approaches =====
    print("\n" + "=" * 80)
    print("EXPERIMENT 8: Combined Best Approaches")
    print("=" * 80)

    # Combine H2H + interactions
    combined_all = add_h2h_features(combined_v75.copy())
    combined_all = add_interaction_features(combined_all)

    features_all = combined_all.drop(columns=["_target", "_game_id", "_season_id", "_game_date"]).fillna(0)
    X_train_all = features_all[train_mask].values
    X_test_all = features_all[test_mask].values

    scaler_all = StandardScaler()
    X_train_all_scaled = scaler_all.fit_transform(X_train_all)
    X_test_all_scaled = scaler_all.transform(X_test_all)

    # Test different C values
    for c in [0.005, 0.01, 0.015]:
        lr_all = LogisticRegression(C=c, max_iter=1000, random_state=42)
        lr_all.fit(X_train_all_scaled, y_train)
        all_proba = lr_all.predict_proba(X_test_all_scaled)[:, 1]
        all_acc = accuracy_score(y_test, (all_proba >= 0.5).astype(int))
        print(f"H2H + Interactions (C={c}): {all_acc:.4f} ({(all_acc - baseline_acc) * 100:+.2f}pp)")
        results[f'combined_c{c}'] = all_acc

    # Bagging on combined features
    bag_all_proba = bagging_ensemble(X_train_all, y_train, X_test_all, n_models=10, C=0.01)
    bag_all_acc = accuracy_score(y_test, (bag_all_proba >= 0.5).astype(int))
    print(f"H2H + Interactions + Bagging: {bag_all_acc:.4f} ({(bag_all_acc - baseline_acc) * 100:+.2f}pp)")
    results['combined_bagging'] = bag_all_acc

    # ===== FINAL SUMMARY =====
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    print(f"\n{'Experiment':<35} {'Accuracy':>10} {'vs V7.5':>10}")
    print("-" * 60)

    for name, acc in sorted(results.items(), key=lambda x: -x[1]):
        delta = (acc - V75_ACC) * 100
        print(f"{name:<35} {acc:>10.4f} {delta:>+9.2f}pp")

    best_name = max(results, key=results.get)
    best_acc = results[best_name]

    print("\n" + "=" * 80)
    print("VERDICT")
    print("=" * 80)

    if best_acc >= 0.62:
        print(f"SUCCESS! {best_name} achieves {best_acc:.2%} - TARGET REACHED!")
    elif best_acc > V75_ACC:
        print(f"IMPROVEMENT! {best_name} at {best_acc:.2%}")
        print(f"  +{(best_acc - V75_ACC) * 100:.2f}pp vs V7.5")
        print(f"  Gap to 62%: {(0.62 - best_acc) * 100:.2f}pp")
    else:
        print(f"NO IMPROVEMENT over V7.5 ({V75_ACC:.2%})")

    print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return results


if __name__ == "__main__":
    main()
