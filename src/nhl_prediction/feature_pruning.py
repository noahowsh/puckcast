"""
V7.0 Feature Pruning - Remove low-importance features

Analyze feature importance and prune bottom 20% to reduce overfitting.
Expected improvement: +0.3-0.5% accuracy

Strategy:
- Remove features with abs(coefficient) < 0.05
- Focus on high-signal features:
  - Goal differential metrics
  - Rolling high-danger shots
  - xG metrics
  - B2B and rest factors
  - Shot quality differentials
"""

import pandas as pd
import numpy as np
from typing import List, Set
import logging

LOGGER = logging.getLogger(__name__)


# Features to ALWAYS keep (proven high value from analysis)
V7_CORE_FEATURES = {
    # Goal differential (TOP importance from feature_importance_v2.csv)
    'season_goal_diff_avg_diff',
    'rolling_goal_diff_10_diff',
    'rolling_goal_diff_5_diff',
    'rolling_goal_diff_3_diff',
    'momentum_goal_diff_diff',

    # High-danger shots (proven valuable #3 feature)
    'rolling_high_danger_shots_5_diff',
    'rolling_high_danger_shots_3_diff',
    'rolling_high_danger_shots_10_diff',

    # xG metrics (custom model advantage)
    'rolling_xg_for_5_diff',
    'rolling_xg_against_5_diff',
    'rolling_xg_for_3_diff',
    'rolling_xg_against_3_diff',
    'rolling_xg_for_10_diff',
    'rolling_xg_against_10_diff',

    # Schedule factors (strong signal - #4 feature is B2B)
    'is_b2b_home',
    'is_b2b_away',
    'rest_days_home',
    'rest_days_away',
    'rest_diff',
    'home_b2b',
    'away_b2b',

    # Shot metrics
    'shotsFor_roll_3_diff',
    'shotsFor_roll_5_diff',
    'shotsAgainst_roll_10_diff',

    # Corsi/Fenwick
    'rolling_corsi_5_diff',
    'rolling_fenwick_10_diff',

    # Win percentage
    'rolling_win_pct_10_diff',
    'rolling_win_pct_5_diff',
    'season_win_pct_diff',

    # Games played
    'games_played_prior_home',
    'games_played_prior_away',
}


# Feature patterns to ALWAYS keep (V7.0 additions)
V7_KEEP_PATTERNS = [
    'goalie_',  # Individual goalie features (V7.0)
    'momentum_',  # Momentum-weighted rolling (V7.0)
    '_diff',  # Differentials are usually high-value
]


# Known low-value features to REMOVE (from analysis)
V7_REMOVE_FEATURES = {
    # Line combination features (often zero importance)
    # Will be populated from feature importance analysis

    # Redundant rolling windows
    # Some rolling window combinations don't add value

    # Low-signal special teams
    # Basic PP/PK without context
}


def analyze_feature_importance(
    model,
    feature_names: List[str],
    threshold: float = 0.05
) -> pd.DataFrame:
    """
    Analyze feature importance from trained model.

    Args:
        model: Trained sklearn model with coef_ attribute
        feature_names: List of feature names
        threshold: Minimum absolute coefficient to keep

    Returns:
        DataFrame with feature importance analysis
    """
    # Get coefficients
    coefs = model.named_steps['clf'].coef_[0]

    importance_df = pd.DataFrame({
        'feature': feature_names,
        'coefficient': coefs,
        'abs_importance': np.abs(coefs)
    }).sort_values('abs_importance', ascending=False)

    # Flag low-importance features
    importance_df['keep'] = importance_df['abs_importance'] >= threshold

    # Always keep core features
    importance_df.loc[
        importance_df['feature'].isin(V7_CORE_FEATURES),
        'keep'
    ] = True

    # Always keep features matching patterns
    for pattern in V7_KEEP_PATTERNS:
        importance_df.loc[
            importance_df['feature'].str.contains(pattern, na=False),
            'keep'
        ] = True

    # Always remove known low-value features
    importance_df.loc[
        importance_df['feature'].isin(V7_REMOVE_FEATURES),
        'keep'
    ] = False

    LOGGER.info(f"Feature importance analysis:")
    LOGGER.info(f"  Total features: {len(importance_df)}")
    LOGGER.info(f"  Keep: {importance_df['keep'].sum()}")
    LOGGER.info(f"  Remove: {(~importance_df['keep']).sum()}")
    LOGGER.info(f"  Threshold: {threshold}")

    return importance_df


def get_pruned_features(importance_df: pd.DataFrame) -> List[str]:
    """
    Get list of features to keep after pruning.

    Args:
        importance_df: Output from analyze_feature_importance

    Returns:
        List of feature names to keep
    """
    features_to_keep = importance_df[importance_df['keep']]['feature'].tolist()

    LOGGER.info(f"Pruned features:")
    LOGGER.info(f"  Original: {len(importance_df)}")
    LOGGER.info(f"  After pruning: {len(features_to_keep)}")
    LOGGER.info(f"  Reduction: {len(importance_df) - len(features_to_keep)} features removed")

    return features_to_keep


def prune_features(X: pd.DataFrame, feature_list: List[str]) -> pd.DataFrame:
    """
    Prune DataFrame to only include specified features.

    Args:
        X: Full feature DataFrame
        feature_list: List of features to keep

    Returns:
        Pruned DataFrame with only specified features
    """
    # Keep only features that exist in X
    features_to_keep = [f for f in feature_list if f in X.columns]
    missing_features = set(feature_list) - set(features_to_keep)

    if missing_features:
        LOGGER.warning(f"Features not found in DataFrame: {missing_features}")

    X_pruned = X[features_to_keep].copy()

    LOGGER.info(f"Features pruned: {X.shape[1]} -> {X_pruned.shape[1]}")

    return X_pruned


def generate_feature_importance_report(
    importance_df: pd.DataFrame,
    output_path: str = "reports/v7_feature_importance.csv"
) -> None:
    """
    Generate detailed feature importance report.

    Args:
        importance_df: Feature importance DataFrame
        output_path: Path to save report
    """
    from pathlib import Path

    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Save full report
    importance_df.to_csv(output_path, index=False)
    LOGGER.info(f"Feature importance report saved: {output_path}")

    # Generate summary stats
    keep_features = importance_df[importance_df['keep']]
    remove_features = importance_df[~importance_df['keep']]

    summary = f"""
V7.0 FEATURE PRUNING SUMMARY
============================

Total Features: {len(importance_df)}
Keep: {len(keep_features)} ({len(keep_features)/len(importance_df)*100:.1f}%)
Remove: {len(remove_features)} ({len(remove_features)/len(importance_df)*100:.1f}%)

Top 10 Features (highest importance):
{keep_features.head(10)[['feature', 'abs_importance']].to_string(index=False)}

Bottom 10 Features (lowest importance):
{importance_df.tail(10)[['feature', 'abs_importance']].to_string(index=False)}

Features to Remove ({len(remove_features)} total):
{remove_features['feature'].tolist()[:20]}
{'...' if len(remove_features) > 20 else ''}
"""

    print(summary)

    # Save summary
    summary_path = output_path.replace('.csv', '_summary.txt')
    with open(summary_path, 'w') as f:
        f.write(summary)

    LOGGER.info(f"Summary saved: {summary_path}")
