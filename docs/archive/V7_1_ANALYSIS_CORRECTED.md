# V7.1 Analysis - Data Leakage Discovered & Corrected

**Date:** 2025-12-03
**Status:** ❌ REJECTED - Individual goalie features degrade performance

---

## 🚨 Critical Issue: Data Leakage Detected

### Initial Results (WITH LEAKAGE)
- Accuracy: **67.48%** ⚠️ TOO GOOD TO BE TRUE
- Log Loss: 0.6128
- A+ Confidence: 79.1%

### Root Cause
The `goalie_tracker.pkl` was built from ALL 3 seasons (2021-22, 2022-23, 2023-24), including the test set. When predicting test games, the model used goalie performance FROM THE TEST SET to predict test set outcomes.

**Example:**
- Predicting game on 2024-03-15
- Goalie "last 5 games" included: 2024-03-10, 2024-03-05, 2024-02-28, etc.
- All of these are test set games = **massive leakage**

---

## ✅ Corrected Results (NO LEAKAGE)

### Training Data
- **Goalie Tracker:** Built from 2021-22 and 2022-23 seasons ONLY
- **Games:** 2,624 training games
- **Goalies:** 136 goalies, 5,603 performances

### True V7.1 Performance

| Metric | V7.0 | V7.1 (No Leakage) | Change | Target |
|--------|------|-------------------|---------|---------|
| **Accuracy** | 60.89% | **57.72%** | -3.17pp ⬇️ | 62%+ ❌ |
| **Log Loss** | 0.6752 | **0.8345** | +0.1593 ⬇️ | ≤0.670 ❌ |
| **ROC-AUC** | 0.6363 | **0.6159** | -0.0204 ⬇️ | - |

### Confidence Ladder (V7.1 True)

| Grade | Point Range | Games | Accuracy | V7.0 Acc | Change |
|-------|-------------|-------|----------|----------|--------|
| A+ | 20+ pts | 439 | 64.0% | 69.5% | -5.5pp ⬇️ |
| A- | 15-20 pts | 75 | 54.7% | 56.1% | -1.4pp ⬇️ |
| B+ | 10-15 pts | 53 | 64.2% | 59.5% | +4.7pp ⬆️ |
| B- | 5-10 pts | 61 | 50.8% | 50.7% | +0.1pp → |
| C | 0-5 pts | 49 | 44.9% | 49.0% | -4.1pp ⬇️ |

**Conclusion:** Individual goalie features HURT overall accuracy by 3.17 percentage points and increase log-loss by 0.1593.

---

## 🔍 Why Did Individual Goalies Fail?

### Hypothesis 1: Insufficient Training Data
- Only 2 training seasons (2021-22, 2022-23)
- 5-game rolling averages require stable performance history
- Many backup goalies have <10 games total
- **Impact:** High-variance, unreliable goalie metrics

### Hypothesis 2: Goalie Performance Volatility
- Goalies are notoriously streaky (hot/cold runs)
- 5 recent games may not predict next game performance
- Situational factors (opponent strength, team defense) matter more
- **Impact:** Goalie recent form is weak signal

### Hypothesis 3: Feature Design Issues
- Using raw GSA/save% without context (home/away, opponent quality)
- Missing key factors: rest days, recent workload, team defense
- **Impact:** Features capture noise, not signal

### Hypothesis 4: Team-Level Goalie Stats Better
- V7.0 uses team-level rolling goalie metrics (rolling_gsax_5_diff, etc.)
- These aggregate over multiple goalies, reducing variance
- **Impact:** Team metrics more stable than individual starter metrics

---

## 📊 Feature Importance (V7.1)

Despite hurting overall performance, goalie features have high coefficients:

| Rank | Feature | Coefficient | Abs Importance |
|------|---------|-------------|----------------|
| 1 | `goalie_gsa_diff` | +0.4758 | 0.4758 |
| 2 | `goalie_gsa_last5_home` | +0.3546 | 0.3546 |
| 3 | `goalie_gsa_last5_away` | -0.2905 | 0.2905 |
| 4 | `goalie_quality_diff` | +0.2471 | 0.2471 |

**Why high coefficients but worse performance?**
- Features have strong relationships in training data
- But relationships don't generalize to test set
- Classic overfitting: model learns training-specific patterns that don't transfer

---

## 🎯 Revised Target Achievement

| Metric | Target | Best Model | Status |
|--------|--------|------------|---------|
| **Accuracy** | ≥62% | V7.0: 60.89% | ❌ **Gap: 1.11pp** |
| **Log Loss** | ≤0.670 | V7.0: 0.6752 | ❌ **Gap: 0.0052** |

**Current Best Model:** **V7.0 at 60.89% accuracy**

---

## 🚀 Next Steps to Reach 62%+

### Option A: Improve Goalie Features (Low Priority)
1. **More training data:** Add 2020-21 season (+1,300 games)
2. **Better features:**
   - Home/away goalie split performance
   - Goalie vs opponent historical matchups
   - Rest days / recent workload
   - Team defensive support metrics
3. **Feature selection:** Use only high-confidence goalie assignments (starters with 10+ recent games)

**Expected Impact:** +0.2-0.5% (uncertain, risky)

### Option B: Model Architecture Upgrade (Medium Priority)
Switch from Logistic Regression to **LightGBM** or **XGBoost**:
- Captures non-linear interactions between features
- Handles feature correlations better
- More robust to noisy features

**Expected Impact:** +0.5-0.8% (more reliable)

### Option C: Advanced Shot Quality Features (High Priority)
Beyond current xG model:
- Shot distance variance (not just average)
- Shot angle distributions by zone
- Rebound rate (shots within 5 seconds)
- Traffic in front of net (screens, deflections)

**Expected Impact:** +0.3-0.6% (proven in literature)

### Option D: Situational Context Features (High Priority)
Game situations that affect outcomes:
- 3rd period performance when leading/trailing
- Performance in back-to-back games (fatigue effects)
- Post-bye-week performance
- Divisional vs conference vs inter-conference games

**Expected Impact:** +0.2-0.4% (solid improvements)

---

## 📝 Key Learnings

### What Went Wrong
1. **Data Leakage** - Initial 67.48% result was pure leakage
2. **Individual Goalies Failed** - Actually degraded performance by 3.17pp
3. **Insufficient Training Data** - 2 seasons not enough for reliable goalie metrics
4. **Overfit to Training Set** - High coefficients don't mean good generalization

### What Worked
1. **Detecting Leakage** - User correctly identified "too good to be true" result
2. **Proper Train/Test Split** - Rebuilt goalie tracker with training data only
3. **V7.0 Stability** - 60.89% accuracy remains solid baseline

### Best Practices Validated
- ✅ Always suspect results that seem too good
- ✅ Verify training data doesn't include test information
- ✅ Compare leaked vs true performance to understand feature value
- ✅ Simple features (team-level) often beat complex ones (individual-level)

---

## ✅ Recommendation

**DEPLOY V7.0 AS PRODUCTION MODEL**

- **Accuracy:** 60.89%
- **Log Loss:** 0.6752 (close to target)
- **A+ Confidence:** 69.5% on 436 games
- **Status:** Stable, proven, no leakage

**DO NOT deploy V7.1** - individual goalie features degrade performance.

**Next priority:** Pursue Option C (Advanced Shot Quality) + Option D (Situational Context) to close the 1.11pp gap to 62% target.

---

## 📊 Final Comparison

| Version | Accuracy | Log Loss | A+ Acc | Status | Notes |
|---------|----------|----------|---------|--------|-------|
| V6.3 | 59.92% | - | - | Baseline | NHL API only |
| V7.0 | **60.89%** | **0.6752** | **69.5%** | ✅ **PRODUCTION** | Best model |
| V7.1 (leaked) | 67.48% | 0.6128 | 79.1% | ❌ INVALID | Data leakage |
| V7.1 (true) | 57.72% | 0.8345 | 64.0% | ❌ REJECTED | Degrades performance |

---

*Generated: 2025-12-03*
*Branch: claude/v7-beta-01111xrERXjGtBfF6RaMBsNr*
*Status: V7.0 remains production model*
