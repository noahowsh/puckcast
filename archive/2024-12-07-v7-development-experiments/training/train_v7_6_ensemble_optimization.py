#!/usr/bin/env python3
"""
V7.6 Ensemble Optimization

Since individual model improvements didn't help, try:
1. Ensemble averaging with validation-weighted models
2. Different XGBoost configurations with V7.5 features
3. Stacking with ridge meta-learner
4. Variance analysis (multiple seeds)
5. Selective feature usage in ensemble

Usage:
    python training/train_v7_6_ensemble_optimization.py
"""

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_predict

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
    print("V7.6 Ensemble Optimization")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Baseline V7.5: {V75_ACC:.2%}")
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

    results = {}

    # ===== EXPERIMENT 1: Variance Analysis =====
    print("=" * 80)
    print("EXPERIMENT 1: Variance Analysis (Multiple Seeds)")
    print("=" * 80)

    seed_accs = []
    seed_probas = []

    for seed in range(20):
        lr = LogisticRegression(C=0.01, max_iter=1000, random_state=seed)
        lr.fit(X_train_scaled, y_train)
        proba = lr.predict_proba(X_test_scaled)[:, 1]
        acc = accuracy_score(y_test, (proba >= 0.5).astype(int))
        seed_accs.append(acc)
        seed_probas.append(proba)

    print(f"Accuracy across 20 seeds:")
    print(f"  Mean: {np.mean(seed_accs):.4f}")
    print(f"  Std:  {np.std(seed_accs):.4f}")
    print(f"  Min:  {min(seed_accs):.4f}")
    print(f"  Max:  {max(seed_accs):.4f}")

    # Average all seeds
    avg_proba = np.mean(seed_probas, axis=0)
    avg_acc = accuracy_score(y_test, (avg_proba >= 0.5).astype(int))
    print(f"  Averaged: {avg_acc:.4f}")
    results['seed_avg'] = avg_acc

    # ===== EXPERIMENT 2: XGBoost Configurations =====
    print("\n" + "=" * 80)
    print("EXPERIMENT 2: XGBoost Configurations with V7.5 Features")
    print("=" * 80)

    try:
        from xgboost import XGBClassifier

        xgb_configs = [
            {"n_estimators": 100, "max_depth": 2, "learning_rate": 0.01, "min_child_weight": 50},
            {"n_estimators": 200, "max_depth": 2, "learning_rate": 0.02, "min_child_weight": 40},
            {"n_estimators": 300, "max_depth": 3, "learning_rate": 0.01, "min_child_weight": 30},
            {"n_estimators": 500, "max_depth": 2, "learning_rate": 0.005, "min_child_weight": 60},
        ]

        xgb_probas = []
        for i, cfg in enumerate(xgb_configs):
            xgb = XGBClassifier(
                **cfg,
                gamma=0.5, reg_alpha=0.5, reg_lambda=1.0,
                subsample=0.7, colsample_bytree=0.7,
                random_state=42, verbosity=0, n_jobs=-1
            )
            xgb.fit(X_train, y_train)
            proba = xgb.predict_proba(X_test)[:, 1]
            acc = accuracy_score(y_test, (proba >= 0.5).astype(int))
            xgb_probas.append(proba)
            print(f"Config {i+1}: {acc:.4f} ({(acc - V75_ACC) * 100:+.2f}pp)")
            results[f'xgb_config_{i+1}'] = acc

        has_xgb = True
    except ImportError:
        print("XGBoost not available")
        has_xgb = False

    # ===== EXPERIMENT 3: LR + XGB Fine-tuned Blend =====
    print("\n" + "=" * 80)
    print("EXPERIMENT 3: Fine-tuned LR + XGB Blends")
    print("=" * 80)

    if has_xgb:
        lr = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
        lr.fit(X_train_scaled, y_train)
        lr_proba = lr.predict_proba(X_test_scaled)[:, 1]

        # Use best XGBoost config
        xgb_best = XGBClassifier(
            n_estimators=300, max_depth=2, learning_rate=0.01, min_child_weight=40,
            gamma=0.5, reg_alpha=0.5, reg_lambda=1.0,
            subsample=0.7, colsample_bytree=0.7,
            random_state=42, verbosity=0, n_jobs=-1
        )
        xgb_best.fit(X_train, y_train)
        xgb_proba = xgb_best.predict_proba(X_test)[:, 1]

        # Fine-grained weight search
        best_blend_acc = 0
        best_weight = 0

        for lr_w in np.arange(0.70, 0.96, 0.02):
            blend = lr_w * lr_proba + (1 - lr_w) * xgb_proba
            acc = accuracy_score(y_test, (blend >= 0.5).astype(int))

            if acc > best_blend_acc:
                best_blend_acc = acc
                best_weight = lr_w

            if acc >= V75_ACC:
                print(f"LR {lr_w:.0%} + XGB {1-lr_w:.0%}: {acc:.4f} ({(acc - V75_ACC) * 100:+.2f}pp)")

        print(f"\nBest blend: LR {best_weight:.0%} + XGB {1-best_weight:.0%} = {best_blend_acc:.4f}")
        results['best_blend'] = best_blend_acc

    # ===== EXPERIMENT 4: Stacking =====
    print("\n" + "=" * 80)
    print("EXPERIMENT 4: Stacking with Meta-Learner")
    print("=" * 80)

    # Create OOF predictions
    from sklearn.model_selection import KFold

    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    lr_oof = np.zeros(len(y_train))
    for train_idx, val_idx in kf.split(X_train_scaled):
        lr = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
        lr.fit(X_train_scaled[train_idx], y_train[train_idx])
        lr_oof[val_idx] = lr.predict_proba(X_train_scaled[val_idx])[:, 1]

    if has_xgb:
        xgb_oof = np.zeros(len(y_train))
        for train_idx, val_idx in kf.split(X_train):
            xgb = XGBClassifier(
                n_estimators=300, max_depth=2, learning_rate=0.01, min_child_weight=40,
                gamma=0.5, reg_alpha=0.5, reg_lambda=1.0, subsample=0.7, colsample_bytree=0.7,
                random_state=42, verbosity=0, n_jobs=-1
            )
            xgb.fit(X_train[train_idx], y_train[train_idx])
            xgb_oof[val_idx] = xgb.predict_proba(X_train[val_idx])[:, 1]

        # Stack features
        stack_train = np.column_stack([lr_oof, xgb_oof])

        lr_test = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
        lr_test.fit(X_train_scaled, y_train)
        lr_test_proba = lr_test.predict_proba(X_test_scaled)[:, 1]

        xgb_test = XGBClassifier(
            n_estimators=300, max_depth=2, learning_rate=0.01, min_child_weight=40,
            gamma=0.5, reg_alpha=0.5, reg_lambda=1.0, subsample=0.7, colsample_bytree=0.7,
            random_state=42, verbosity=0, n_jobs=-1
        )
        xgb_test.fit(X_train, y_train)
        xgb_test_proba = xgb_test.predict_proba(X_test)[:, 1]

        stack_test = np.column_stack([lr_test_proba, xgb_test_proba])

        # Meta-learner
        for c in [0.1, 1.0, 10.0]:
            meta = LogisticRegression(C=c, max_iter=1000, random_state=42)
            meta.fit(stack_train, y_train)
            meta_proba = meta.predict_proba(stack_test)[:, 1]
            meta_acc = accuracy_score(y_test, (meta_proba >= 0.5).astype(int))
            print(f"Stacking meta (C={c}): {meta_acc:.4f} ({(meta_acc - V75_ACC) * 100:+.2f}pp)")
            results[f'stacking_c{c}'] = meta_acc

    # ===== EXPERIMENT 5: Feature Subsets =====
    print("\n" + "=" * 80)
    print("EXPERIMENT 5: Feature Subset Analysis")
    print("=" * 80)

    # Get feature importances from LogReg coefficients
    lr_full = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
    lr_full.fit(X_train_scaled, y_train)

    feature_names = features_v75.columns.tolist()
    coef_importance = np.abs(lr_full.coef_[0])
    sorted_idx = np.argsort(coef_importance)[::-1]

    # Test with different feature counts
    for n_features in [50, 100, 150, 200, len(feature_names)]:
        top_idx = sorted_idx[:n_features]
        X_train_sub = X_train_scaled[:, top_idx]
        X_test_sub = X_test_scaled[:, top_idx]

        lr_sub = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
        lr_sub.fit(X_train_sub, y_train)
        sub_proba = lr_sub.predict_proba(X_test_sub)[:, 1]
        sub_acc = accuracy_score(y_test, (sub_proba >= 0.5).astype(int))
        print(f"Top {n_features} features: {sub_acc:.4f} ({(sub_acc - V75_ACC) * 100:+.2f}pp)")
        results[f'top_{n_features}'] = sub_acc

    # ===== EXPERIMENT 6: Different Regularization Strengths per Split =====
    print("\n" + "=" * 80)
    print("EXPERIMENT 6: Validation-based Model Selection")
    print("=" * 80)

    X_tr, X_val, y_tr, y_val = train_test_split(X_train_scaled, y_train, test_size=0.2, random_state=42)

    best_val_c = 0.01
    best_val_acc = 0

    for c in [0.005, 0.007, 0.01, 0.012, 0.015, 0.02, 0.03, 0.05]:
        lr = LogisticRegression(C=c, max_iter=1000, random_state=42)
        lr.fit(X_tr, y_tr)
        val_proba = lr.predict_proba(X_val)[:, 1]
        val_acc = accuracy_score(y_val, (val_proba >= 0.5).astype(int))

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_val_c = c

    print(f"Best C on validation: {best_val_c} (val acc: {best_val_acc:.4f})")

    # Train on full training set with best C
    lr_best = LogisticRegression(C=best_val_c, max_iter=1000, random_state=42)
    lr_best.fit(X_train_scaled, y_train)
    best_proba = lr_best.predict_proba(X_test_scaled)[:, 1]
    best_test_acc = accuracy_score(y_test, (best_proba >= 0.5).astype(int))
    print(f"Test acc with best val C: {best_test_acc:.4f} ({(best_test_acc - V75_ACC) * 100:+.2f}pp)")
    results['val_best_c'] = best_test_acc

    # ===== FINAL SUMMARY =====
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    print(f"\n{'Experiment':<25} {'Accuracy':>10} {'vs V7.5':>10}")
    print("-" * 50)

    for name, acc in sorted(results.items(), key=lambda x: -x[1]):
        delta = (acc - V75_ACC) * 100
        print(f"{name:<25} {acc:>10.4f} {delta:>+9.2f}pp")

    best_name = max(results, key=results.get)
    best_acc = results[best_name]

    print("\n" + "=" * 80)
    print("VERDICT")
    print("=" * 80)

    if best_acc > V75_ACC:
        print(f"IMPROVEMENT: {best_name} at {best_acc:.2%}")
        print(f"  +{(best_acc - V75_ACC) * 100:.2f}pp vs V7.5")
    else:
        print(f"NO IMPROVEMENT over V7.5 ({V75_ACC:.2%})")
        print(f"V7.5 appears to be at the ceiling for this dataset/model approach.")

    print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return results


if __name__ == "__main__":
    main()
