# V7.4 Head-to-Head Features - Analysis and Findings

## Executive Summary

**Result: FAILED - V7.4 underperforms V7.3 by -1.38pp**

- **V7.3 (situational features)**: 61.38% accuracy
- **V7.4 (+ head-to-head)**: 60.00% accuracy
- **Gap to target**: Still -2.00pp from 62% goal

## What We Tried

Based on V7.3 error analysis revealing 20+ problematic head-to-head matchups (e.g., ANA vs VGK with 4 errors out of 6-8 games), we built 6 H2H features:

1. **h2h_win_pct_last_season**: Team win% vs opponent in previous season
2. **h2h_win_pct_recent**: Win% in last 3 head-to-head matchups
3. **h2h_goal_diff_recent**: Average goal differential in last 3 H2H games
4. **h2h_home_advantage**: Historical home team win% for this specific matchup
5. **season_series_home_wins**: Current season series standing (home team wins)
6. **season_series_away_wins**: Current season series standing (away team wins)

## Critical Bug Found and Fixed

### Data Leakage Issue

**Initial implementation** calculated H2H features chronologically across all games, meaning test games used outcomes from OTHER test games in their features.

**Fix applied**: Modified `add_head_to_head_features()` to only build history from training seasons:

```python
def add_head_to_head_features(games: pd.DataFrame, train_seasons: list = None):
    # Only add to history if this is a training season (prevents test set leakage)
    if train_seasons is None or season in train_seasons:
        h2h_history[matchup_key].append({...})
```

**Result after fix**: Still underperformed (60.00% vs 61.38%)

## Why H2H Features Failed

### 1. Weak Predictive Signal

After fixing data leakage, H2H feature coefficients are small:
- h2h_win_pct_recent: 0.0889
- h2h_win_pct_last_season: -0.0754
- h2h_goal_diff_recent: -0.0745

None appear in top 20 features. Compare to existing features:
- rolling_goal_diff_10_diff: -0.1939 (strongest)
- rolling_high_danger_shots_3_diff: 0.1829

### 2. Multicollinearity with Existing Features

H2H features capture information already present in:
- **rolling_goal_diff_10_diff**: Recent team performance
- **season_goal_diff_avg_diff**: Overall team strength
- **rolling_win_pct_3_diff**: Recent winning trends

Adding H2H features introduces redundancy without new signal.

### 3. Sample Size Issues

Most matchups only play 2-4 times per season, leading to:
- High variance in H2H statistics
- Unreliable estimates
- Overfitting to noise

### 4. Problematic Matchups ≠ Predictable Patterns

Error analysis showed matchups like ANA vs VGK with 4/6 errors. But:
- These might be inherently unpredictable (high variance matchups)
- Not necessarily fixable with H2H history
- Could be due to roster changes, injuries, or random variance

## Feature Importance Comparison

### V7.3 (61.38% accuracy)
Top features all from V7.0 baseline:
1. rolling_goal_diff_10_diff: -0.2167
2. rolling_high_danger_shots_3_diff: 0.2065
3. home_team_28: -0.1902

Situational features had minor impact.

### V7.4 (60.00% accuracy)
Same V7.0 features dominate. H2H features all below 0.09 coefficient.

## Key Lessons

1. **Error patterns don't always suggest solutions**: Matchup-specific errors might be noise, not signal

2. **Existing features already capture matchup dynamics**: Rolling stats implicitly include H2H performance

3. **Simple is better**: Adding 6 features with weak signal hurts generalization

4. **Data leakage is subtle**: Always verify train/test separation in temporal features

## Recommendations

**V7.3 remains production model at 61.38% accuracy**

Next approaches to close 0.62pp gap to 62%:

### 1. Target Specific Weak Points
From error analysis:
- **Away B2B games**: 56 errors vs 14 home B2B (4x worse)
- **Hardest teams**: VGK (34.7% error rate), PHI (33.9%), NYI (32.2%)

**Action**: Analyze *why* away B2B is underweighted. Might need feature engineering or weight adjustment.

### 2. Feature Interaction Terms
Instead of adding new features, try interactions of existing strong features:
- rolling_goal_diff_10 × home_team indicator
- rolling_high_danger_shots × fatigue_index
- rest_diff × divisional_matchup

### 3. Team-Specific Calibration
Some teams consistently over/under-predicted. Try:
- Team-specific bias terms
- Separate model calibration for difficult teams

### 4. Confidence-Based Filtering
Error analysis by confidence shows:
- 15-20pt confidence: 47% error rate (worst)
- Could exclude or reweight low-confidence predictions

### 5. Goalie Tracking (Future)
Individual goalie features underperformed (-2.27pp) but infrastructure valuable for stats pages. Revisit when more data available.

## Files Modified

1. **src/nhl_prediction/head_to_head_features.py** - Created with data leakage fix
2. **train_v7_4_head_to_head.py** - Training script
3. **analyze_v7_3_errors.py** - Error analysis revealing H2H issues

## Conclusion

Head-to-head features seemed promising based on error analysis but failed in practice due to:
- Multicollinearity with existing rolling stats
- Weak signal-to-noise ratio
- Sample size limitations

**V7.3 at 61.38% remains our best model.** Next steps should focus on:
1. Away B2B weakness (largest identifiable gap)
2. Feature interactions (leverage existing strong features)
3. Team-specific adjustments

The 0.62pp gap to 62% is challenging. May need to accept 61.4% as near-optimal for this feature set and look at fundamental model architecture changes (ensembles, neural networks) if higher accuracy required.
