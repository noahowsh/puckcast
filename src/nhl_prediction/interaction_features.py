"""
Feature Interaction Terms (V7.5)

Multiply strong baseline features with contextual variables to capture
non-linear effects. E.g., goal differential might matter more in divisional games.
"""

import pandas as pd
import logging

LOGGER = logging.getLogger(__name__)


def add_interaction_features(features: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    """
    Add feature interaction terms.

    Top predictors from V7.4:
    - rolling_goal_diff_10_diff
    - rolling_high_danger_shots_3_diff
    - season_goal_diff_avg_diff
    - rolling_xg_for_5_diff

    Contextual modifiers:
    - divisional_matchup (same division games)
    - rest_diff (rest advantage)
    - home_b2b, away_b2b (fatigue context)

    Interactions added (12 total):
    1-4: Top 4 predictors × divisional_matchup
    5-8: Top 4 predictors × rest_diff
    9-12: Top 4 predictors × b2b_indicator
    """
    LOGGER.info("Adding V7.5 feature interaction terms...")

    features = features.copy()

    # Top predictors to interact
    top_predictors = [
        'rolling_goal_diff_10_diff',
        'rolling_high_danger_shots_3_diff',
        'season_goal_diff_avg_diff',
        'rolling_xg_for_5_diff',
    ]

    # Verify all features exist
    missing = [f for f in top_predictors if f not in features.columns]
    if missing:
        LOGGER.warning(f"Missing features for interactions: {missing}")
        top_predictors = [f for f in top_predictors if f in features.columns]

    # Contextual modifiers from games
    interactions_added = 0

    # 1. Divisional matchup interactions
    if 'divisional_matchup' in games.columns:
        divisional = games['divisional_matchup'].values
        for pred in top_predictors:
            interaction_name = f"{pred}_x_divisional"
            features[interaction_name] = features[pred] * divisional
            interactions_added += 1

    # 2. Rest differential interactions
    if 'rest_diff' in games.columns:
        rest_diff = games['rest_diff'].values
        for pred in top_predictors:
            interaction_name = f"{pred}_x_rest"
            features[interaction_name] = features[pred] * rest_diff
            interactions_added += 1

    # 3. B2B context interactions
    if 'home_b2b' in games.columns and 'away_b2b' in games.columns:
        # Create B2B indicator: 1 if either team is B2B, 0 otherwise
        b2b_indicator = (games['home_b2b'] | games['away_b2b']).astype(int).values
        for pred in top_predictors:
            interaction_name = f"{pred}_x_b2b"
            features[interaction_name] = features[pred] * b2b_indicator
            interactions_added += 1

    LOGGER.info(f"✓ Added {interactions_added} V7.5 feature interaction terms")

    return features


__all__ = ['add_interaction_features']
