"""
Team-Specific Calibration Features (V7.6)

Add bias adjustment features for teams that are consistently mis-predicted.
From V7.3 error analysis, some teams have much higher error rates:
- VGK: 34.7% error rate
- PHI: 33.9%
- NYI: 32.2%

These features allow the model to learn team-specific biases.
"""

import pandas as pd
import logging

LOGGER = logging.getLogger(__name__)


def add_team_calibration_features(features: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    """
    Add team-specific calibration features.

    For each team, adds indicator variables that allow the model to learn
    systematic biases in how that team is predicted.

    Features added: 3 per difficult team (home indicator, away indicator, any game)
    - Focuses on VGK, PHI, NYI, WSH, PIT based on error analysis

    Args:
        features: Existing feature dataframe
        games: Games dataframe with team abbreviations

    Returns:
        Features with team calibration terms added
    """
    LOGGER.info("Adding V7.6 team calibration features...")

    features = features.copy()

    # Teams with highest error rates from V7.3 analysis
    difficult_teams = ['VGK', 'PHI', 'NYI', 'WSH', 'PIT']

    features_added = 0

    for team in difficult_teams:
        # Home game indicator
        home_indicator = (games['teamAbbrev_home'] == team).astype(int)
        features[f'team_{team}_home'] = home_indicator
        features_added += 1

        # Away game indicator
        away_indicator = (games['teamAbbrev_away'] == team).astype(int)
        features[f'team_{team}_away'] = away_indicator
        features_added += 1

        # Any game indicator (either home or away)
        any_indicator = (home_indicator | away_indicator).astype(int)
        features[f'team_{team}_any'] = any_indicator
        features_added += 1

    LOGGER.info(f"✓ Added {features_added} V7.6 team calibration features for {len(difficult_teams)} teams")

    return features


__all__ = ['add_team_calibration_features']
