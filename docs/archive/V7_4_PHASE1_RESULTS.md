# V7.4 Phase 1 Results: Enhanced Special Teams Features

**Date:** 2025-12-03
**Status:** ❌ FAILED - Performance degraded vs V7.3

---

## Results Summary

| Metric | V7.3 Baseline | **V7.4 Phase 1** | Change |
|--------|--------------|------------------|---------|
| **Test Accuracy** | 61.38% | **60.57%** | **-0.81pp** ❌ |
| **Log Loss** | 0.6698 ✓ | 0.6714 | +0.0016 ❌ |
| **ROC-AUC** | - | 0.6385 | - |
| **A+ Accuracy** | 71.1% (246 games) | 71.3% (251 games) | +0.2pp |
| **Feature Count** | 222 | 240 | +18 |

**Gap to 62% target:** 1.43pp (increased from 0.62pp)

---

## What We Tried

### Features Added (18 total)

**1. Special Teams Goal Differential (3 features)**
- `special_teams_goal_diff_rolling_home/away/diff` - (PP goals - SH goals allowed) last 10 games
- Direct goal impact measurement

**2. PP/PK Opportunities (6 features)**
- `pp_opportunities_rolling_home/away/diff` - Penalties drawn (PP chances)
- `pk_opportunities_rolling_home/away/diff` - Penalties taken (PK chances)
- Measures discipline and special teams volume

**3. Special Teams Efficiency (3 features)**
- `special_teams_efficiency_home/away/diff` - (PP goals/opps) - (SH allowed/opps)
- Conversion rate measurement

**4. Home/Away Variance (6 features)**
- `pp_home_away_variance_home/away/diff` - PP% difference home vs away
- `pk_home_away_variance_home/away/diff` - PK% difference home vs away
- **ALL ZERO COEFFICIENTS** (pruned by model)

---

## Feature Importance Analysis

### V7.4 Special Teams Features (Ranked by Abs Coefficient)

| Rank | Feature | Coefficient | Abs Value |
|------|---------|-------------|-----------|
| 1 | special_teams_goal_diff_rolling_diff | -0.0617 | 0.0617 |
| 2 | special_teams_goal_diff_rolling_away | 0.0566 | 0.0566 |
| 3 | special_teams_goal_diff_rolling_home | -0.0537 | 0.0537 |
| 4 | pp_opportunities_rolling_away | 0.0530 | 0.0530 |
| 5 | pp_opportunities_rolling_home | 0.0418 | 0.0418 |
| 6 | pk_opportunities_rolling_away | 0.0407 | 0.0407 |
| 7 | pk_opportunities_rolling_home | 0.0342 | 0.0342 |
| 8 | special_teams_efficiency_home | 0.0234 | 0.0234 |
| 9-18 | (remaining features) | <0.01 | <0.01 |

**Compare to Top Overall Features:**
- `season_goal_diff_avg_diff`: 0.2098 (**3.4x larger**)
- `rolling_gsax_3_diff`: 0.1823 (**3.0x larger**)
- `rolling_goal_diff_10_diff`: 0.1735 (**2.8x larger**)

---

## Why It Failed

### 1. **Coefficients Too Small**
- Largest special teams coefficient: 0.0617
- Top overall features: 0.17-0.21 (3-4x larger)
- Special teams features have weak predictive power

### 2. **Still Collinear with Goal Differential**
- Special teams impact ultimately shows up in goals scored/allowed
- `season_goal_diff_avg_diff` already captures this (#1 feature, 0.2098)
- Adding PP/PK details doesn't add new signal

### 3. **Home/Away Variance Features Pruned**
- All 6 variance features had ZERO coefficients
- Model found no predictive value in home/away splits for special teams

### 4. **Overfitting Risk**
- Added 18 features (+8% increase)
- But accuracy decreased by 0.81pp
- Classic sign of overfitting or noisy features

---

## Key Insights

### What Worked (Slightly)
- A+ bucket improved +0.2pp (71.1% → 71.3%)
- 251 high-confidence games vs 246 (more games identified)
- Special teams goal differential had highest coefficient (0.0617)

### What Didn't Work
- Overall accuracy degraded significantly
- Home/away variance completely ignored by model
- Efficiency metrics had minimal impact (<0.02)
- Log loss target missed again (0.6714 vs 0.670)

### Root Cause
**Special teams are fundamentally captured in goal differential.** Teams that score more goals inherently have:
- Better power play (more PP goals)
- Better penalty kill (fewer SH goals allowed)
- Better discipline (more penalties drawn)

Adding granular special teams metrics **doesn't add orthogonal information** - it's just a different view of the same underlying team quality signal that `season_goal_diff_avg_diff` already captures.

---

## Lessons Learned

### Failed Hypothesis
❌ "Special teams account for 20-25% of goals but have zero weight in model, so adding enhanced special teams features will improve accuracy"

**Reality:** The existing goal differential features already incorporate special teams impact. The reason raw PP%/PK% had zero coefficients wasn't because special teams don't matter - it's because they're already captured in more general metrics.

### Validated Findings
✅ Feature importance analysis correctly identified collinearity
✅ Model pruning (zero coefficients) is working as intended
✅ Adding more features doesn't guarantee improvement

---

## Recommendation

**KEEP V7.3 AS PRODUCTION MODEL**

V7.3 at **61.38% accuracy** with:
- 222 features (cleaner than V7.4's 240)
- Log loss target achieved (0.6698 ≤ 0.670) ✓
- A+ bucket: 71.1% on 246 games

**Next Options:**

1. **Try Phase 2: PDO Regression Features** (+0.2-0.4pp expected)
   - PDO = Shooting% + Save% (measures luck/sustainability)
   - Different signal than goal differential
   - Regression to mean is proven in hockey analytics

2. **Try Phase 3: Goalie Home/Away Splits** (+0.1-0.2pp expected)
   - Split existing goalie features by location
   - Goalie features are #2 and #4 most important

3. **Accept V7.3 as Final**
   - 61.38% is +0.49pp over V7.0 (60.89%)
   - Only 0.62pp short of 62% target
   - May have hit ceiling for this feature set

---

## Technical Details

### Implementation
- **Module:** `src/nhl_prediction/special_teams_features.py`
- **Training Script:** `train_v7_4_special_teams.py`
- **Extraction:** Processed 3,690 games play-by-play data
- **Situation Codes:** Parsed power play/shorthanded goals from NHL API

### Data Processing
- Extracted PP goals, SH goals from situation codes
- Used penalties as proxy for opportunities
- Computed rolling 10-game metrics
- Calculated home/away splits from last 20 games

### Model
- Logistic Regression with Isotonic Calibration
- C = 0.05 (L2 regularization)
- Equal season weights (decay = 1.0)
- Train: 2021-22 + 2022-23 (2,460 games)
- Test: 2023-24 (1,230 games)

---

**Conclusion:** V7.4 Phase 1 (Enhanced Special Teams) did not improve model performance. Special teams features are collinear with existing goal differential metrics. **V7.3 remains best model.**

**Status:** Phase 1 complete, ready for Phase 2 (PDO) or Phase 3 (Goalie Splits) decision.
