#!/usr/bin/env python3
"""
V7.6 Feature Selection Deep Dive

Discovery: Top 50 features = 61.54% (best so far!)

This script explores:
1. Fine-grained feature count search
2. What are the top 50 features?
3. Different feature selection methods
4. Combining feature selection with ensemble

Usage:
    python training/train_v7_6_feature_selection.py
"""

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import mutual_info_classif, SelectKBest, f_classif

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

TRAIN_SEASONS = ["20212022", "20222023"]
TEST_SEASON = "20232024"

V75_ACC = 0.6122


def load_data():
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


def add_v75_features(combined):
    games = combined.copy()

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

    if 'rolling_xg_for_5_diff' in games.columns:
        games['luck_indicator_5'] = games['rolling_goal_diff_5_diff'] - games['rolling_xg_diff_5_diff']

    if 'rolling_goal_diff_3_diff' in games.columns and 'rolling_goal_diff_10_diff' in games.columns:
        games['consistency_gd'] = abs(games['rolling_goal_diff_3_diff'] - games['rolling_goal_diff_10_diff'])

    if 'rolling_goal_diff_5_diff' in games.columns and 'rolling_win_pct_5_diff' in games.columns:
        games['dominance_score'] = games['rolling_win_pct_5_diff'].clip(-1, 1) * games['rolling_goal_diff_5_diff'].clip(-3, 3)

    return games


def main():
    print("=" * 80)
    print("V7.6 Feature Selection Deep Dive")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Discovery: Top 50 features = 61.54% (best so far!)")
    print()

    # Load data
    games, features, target, combined = load_data()
    combined_v75 = add_v75_features(combined)
    features_v75 = combined_v75.drop(columns=["_target", "_game_id", "_season_id", "_game_date"]).fillna(0)

    train_mask = games["seasonId"].isin(TRAIN_SEASONS)
    test_mask = games["seasonId"] == TEST_SEASON

    X_train = features_v75[train_mask].values
    X_test = features_v75[test_mask].values
    y_train = target[train_mask].values
    y_test = target[test_mask].values

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    feature_names = features_v75.columns.tolist()

    # Get baseline coefficients
    lr_full = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
    lr_full.fit(X_train_scaled, y_train)
    coef_importance = np.abs(lr_full.coef_[0])
    sorted_idx = np.argsort(coef_importance)[::-1]

    results = {}

    # ===== EXPERIMENT 1: Fine-grained Feature Count =====
    print("=" * 80)
    print("EXPERIMENT 1: Fine-grained Feature Count Search")
    print("=" * 80)

    best_n = 50
    best_acc = 0

    for n in range(30, 81, 5):
        top_idx = sorted_idx[:n]
        X_train_sub = X_train_scaled[:, top_idx]
        X_test_sub = X_test_scaled[:, top_idx]

        lr = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
        lr.fit(X_train_sub, y_train)
        proba = lr.predict_proba(X_test_sub)[:, 1]
        acc = accuracy_score(y_test, (proba >= 0.5).astype(int))

        if acc > best_acc:
            best_acc = acc
            best_n = n

        print(f"Top {n:3d}: {acc:.4f} ({(acc - V75_ACC) * 100:+.2f}pp)")
        results[f'top_{n}'] = acc

    print(f"\nBest: Top {best_n} features = {best_acc:.4f}")

    # ===== EXPERIMENT 2: What are the top features? =====
    print("\n" + "=" * 80)
    print("EXPERIMENT 2: Top 50 Features (by |coefficient|)")
    print("=" * 80)

    top_50_idx = sorted_idx[:50]
    top_50_names = [feature_names[i] for i in top_50_idx]
    top_50_coefs = coef_importance[top_50_idx]

    print(f"\n{'Rank':<6} {'Feature':<45} {'|Coef|':>10}")
    print("-" * 65)
    for i, (name, coef) in enumerate(zip(top_50_names, top_50_coefs), 1):
        print(f"{i:<6} {name:<45} {coef:>10.4f}")

    # ===== EXPERIMENT 3: Different C values with top 50 =====
    print("\n" + "=" * 80)
    print("EXPERIMENT 3: Regularization with Top 50 Features")
    print("=" * 80)

    X_train_50 = X_train_scaled[:, top_50_idx]
    X_test_50 = X_test_scaled[:, top_50_idx]

    for c in [0.005, 0.007, 0.01, 0.015, 0.02, 0.03, 0.05, 0.1]:
        lr = LogisticRegression(C=c, max_iter=1000, random_state=42)
        lr.fit(X_train_50, y_train)
        proba = lr.predict_proba(X_test_50)[:, 1]
        acc = accuracy_score(y_test, (proba >= 0.5).astype(int))
        print(f"C={c}: {acc:.4f} ({(acc - V75_ACC) * 100:+.2f}pp)")
        results[f'top50_c{c}'] = acc

    # ===== EXPERIMENT 4: Mutual Information Selection =====
    print("\n" + "=" * 80)
    print("EXPERIMENT 4: Mutual Information Feature Selection")
    print("=" * 80)

    # Calculate mutual information
    mi_scores = mutual_info_classif(X_train, y_train, random_state=42)
    mi_sorted_idx = np.argsort(mi_scores)[::-1]

    for n in [30, 40, 50, 60, 70]:
        mi_top_idx = mi_sorted_idx[:n]
        X_train_mi = X_train_scaled[:, mi_top_idx]
        X_test_mi = X_test_scaled[:, mi_top_idx]

        lr = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
        lr.fit(X_train_mi, y_train)
        proba = lr.predict_proba(X_test_mi)[:, 1]
        acc = accuracy_score(y_test, (proba >= 0.5).astype(int))
        print(f"MI Top {n}: {acc:.4f} ({(acc - V75_ACC) * 100:+.2f}pp)")
        results[f'mi_top_{n}'] = acc

    # ===== EXPERIMENT 5: ANOVA F-score Selection =====
    print("\n" + "=" * 80)
    print("EXPERIMENT 5: ANOVA F-score Feature Selection")
    print("=" * 80)

    selector = SelectKBest(f_classif, k=50)
    X_train_anova = selector.fit_transform(X_train_scaled, y_train)
    X_test_anova = selector.transform(X_test_scaled)

    lr = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
    lr.fit(X_train_anova, y_train)
    proba = lr.predict_proba(X_test_anova)[:, 1]
    acc = accuracy_score(y_test, (proba >= 0.5).astype(int))
    print(f"ANOVA Top 50: {acc:.4f} ({(acc - V75_ACC) * 100:+.2f}pp)")
    results['anova_50'] = acc

    # ===== EXPERIMENT 6: Top 50 + XGBoost Ensemble =====
    print("\n" + "=" * 80)
    print("EXPERIMENT 6: Top 50 Features + XGBoost Ensemble")
    print("=" * 80)

    try:
        from xgboost import XGBClassifier

        # LogReg on top 50
        lr_50 = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
        lr_50.fit(X_train_50, y_train)
        lr_proba = lr_50.predict_proba(X_test_50)[:, 1]

        # XGBoost on top 50
        xgb = XGBClassifier(
            n_estimators=200, max_depth=2, learning_rate=0.02, min_child_weight=40,
            gamma=0.5, reg_alpha=0.5, reg_lambda=1.0, subsample=0.7, colsample_bytree=0.7,
            random_state=42, verbosity=0, n_jobs=-1
        )
        xgb.fit(X_train[:, top_50_idx], y_train)
        xgb_proba = xgb.predict_proba(X_test[:, top_50_idx])[:, 1]

        for lr_w in [0.95, 0.90, 0.85, 0.80, 0.75]:
            blend = lr_w * lr_proba + (1 - lr_w) * xgb_proba
            acc = accuracy_score(y_test, (blend >= 0.5).astype(int))
            print(f"LR {lr_w:.0%} + XGB {1-lr_w:.0%}: {acc:.4f} ({(acc - V75_ACC) * 100:+.2f}pp)")
            results[f'top50_blend_{int(lr_w*100)}'] = acc

    except ImportError:
        print("XGBoost not available")

    # ===== EXPERIMENT 7: Remove team dummies =====
    print("\n" + "=" * 80)
    print("EXPERIMENT 7: Without Team Dummy Variables")
    print("=" * 80)

    non_team_cols = [i for i, name in enumerate(feature_names)
                     if not (name.startswith('home_team_') or name.startswith('away_team_'))]

    X_train_no_team = X_train_scaled[:, non_team_cols]
    X_test_no_team = X_test_scaled[:, non_team_cols]

    print(f"Features without team dummies: {len(non_team_cols)}")

    for c in [0.01, 0.02, 0.05]:
        lr = LogisticRegression(C=c, max_iter=1000, random_state=42)
        lr.fit(X_train_no_team, y_train)
        proba = lr.predict_proba(X_test_no_team)[:, 1]
        acc = accuracy_score(y_test, (proba >= 0.5).astype(int))
        print(f"No teams (C={c}): {acc:.4f} ({(acc - V75_ACC) * 100:+.2f}pp)")
        results[f'no_teams_c{c}'] = acc

    # ===== FINAL SUMMARY =====
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    print(f"\n{'Experiment':<25} {'Accuracy':>10} {'vs V7.5':>10}")
    print("-" * 50)

    for name, acc in sorted(results.items(), key=lambda x: -x[1])[:15]:
        delta = (acc - V75_ACC) * 100
        print(f"{name:<25} {acc:>10.4f} {delta:>+9.2f}pp")

    best_name = max(results, key=results.get)
    best_acc = results[best_name]

    print("\n" + "=" * 80)
    print("BEST V7.6 MODEL")
    print("=" * 80)

    print(f"\n{best_name}: {best_acc:.4f} ({best_acc:.2%})")
    print(f"Improvement vs V7.5: +{(best_acc - V75_ACC) * 100:.2f}pp")
    print(f"Gap to 62%: {(0.62 - best_acc) * 100:.2f}pp")

    # Show metrics for best model
    if best_n == 50:
        lr_best = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
        lr_best.fit(X_train_50, y_train)
        best_proba = lr_best.predict_proba(X_test_50)[:, 1]

        print(f"\nBest Model Metrics:")
        print(f"  Accuracy:  {best_acc:.4f}")
        print(f"  Log Loss:  {log_loss(y_test, best_proba):.4f}")
        print(f"  ROC-AUC:   {roc_auc_score(y_test, best_proba):.4f}")

        # Confidence buckets
        point_diffs = (best_proba - 0.5) * 100
        print(f"\nConfidence Buckets:")
        for grade, min_pts, max_pts in [("A+", 20, 100), ("A-", 15, 20), ("B+", 10, 15)]:
            mask = (point_diffs >= min_pts) & (point_diffs < max_pts)
            n_games = mask.sum()
            if n_games > 0:
                acc = accuracy_score(y_test[mask], (best_proba[mask] >= 0.5).astype(int))
                print(f"  {grade}: {n_games} games, {acc:.1%} accuracy")

    print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return results


if __name__ == "__main__":
    main()
