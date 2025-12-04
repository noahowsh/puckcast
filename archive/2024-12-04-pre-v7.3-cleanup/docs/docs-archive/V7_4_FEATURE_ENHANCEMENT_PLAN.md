# V7.4 Feature Enhancement Plan

**Current Status:** V7.3 at 61.38% accuracy (0.62pp short of 62% target)

---

## 🔍 Analysis: What's Missing?

### Critical Discovery: Special Teams Features Are ZEROED OUT

All 16 special teams features (PP%, PK%, rolling averages) have **0.0 coefficients** in V7.0 and were pruned!

```
powerPlayPct_diff: 0.0
penaltyKillPct_diff: 0.0
rolling_powerPlayPct_5_diff: 0.0
rolling_penaltyKillPct_5_diff: 0.0
... (all 16 special teams features = 0.0)
```

**Why This Matters:**
- Special teams are HUGE in hockey (20-25% of goals scored on PP/PK)
- Elite PP (25%+) vs weak PK (75%) is a major advantage
- Current model ignores this completely

**Why They're Zero:**
- Likely **collinear** with goal differential (teams that score more have better PP)
- **Raw percentages** don't capture the right signal
- Need **enhanced special teams features** that add new information

---

## 🎯 V7.4 Enhancement Strategy

### Focus on 3 High-Value Feature Sets

### **1. Enhanced Special Teams Features** ⭐ **HIGHEST PRIORITY**

**Problem:** Raw PP%/PK% are collinear with goal differential

**Solution:** Create features that capture special teams **impact** and **opportunities**

**New Features to Add (6):**
1. `special_teams_goal_diff_rolling` - (PP goals - SH goals against) last 10 games
   - Direct goal impact, not just percentage

2. `pp_opportunities_rolling` - Power play chances last 10 games
   - Measures discipline/drawing penalties

3. `pk_opportunities_rolling` - Times shorthanded last 10 games
   - Measures taking penalties

4. `special_teams_efficiency_diff` - (PP goals/PP chances) - (PK goals allowed/PK chances)
   - Efficiency vs opportunity count

5. `pp_pct_home_away_variance` - Difference in PP% home vs away
   - Some teams much better at home

6. `pk_pct_home_away_variance` - Difference in PK% home vs away

**Expected Impact:** +0.3-0.5pp accuracy

---

### **2. PDO Regression Features** ⭐ **HIGH PRIORITY**

**Concept:** PDO = Shooting% + Save% (normally ~100)
- Teams with PDO > 102 are "lucky" (regress down)
- Teams with PDO < 98 are "unlucky" (regress up)

**Why This Matters:**
- Unsustainable high shooting% leads to losses
- Unsustainable low save% leads to wins
- **Regression to mean** is predictive

**New Features to Add (4):**
1. `pdo_rolling_10` - PDO over last 10 games
2. `pdo_deviation` - Distance from 100 (extreme values regress)
3. `shooting_pct_sustainability` - Likelihood current SH% continues
   - Based on shot quality (xG vs actual goals)
4. `save_pct_sustainability` - Likelihood current SV% continues
   - Based on shots against quality

**Expected Impact:** +0.2-0.4pp accuracy

---

### **3. Enhanced Goalie Home/Away Splits** ⭐ **MEDIUM PRIORITY**

**Observation:** Goalie metrics are #2 and #4 in importance
- `rolling_gsax_3_diff`: 0.1788 (2nd)
- `rolling_gsax_5_diff`: -0.1747 (4th)

**Opportunity:** These don't differentiate home vs away performance

**New Features to Add (4):**
1. `rolling_gsax_5_home_diff` - Home goalie performance home vs away
2. `rolling_gsax_5_away_diff` - Away goalie performance away vs home
3. `save_pct_home_advantage` - Save% boost at home
4. `goalie_quality_variance` - Consistency metric (hot/cold streaks)

**Expected Impact:** +0.1-0.2pp accuracy

---

## 📊 Feature Count Summary

| Feature Set | New Features | Expected Gain |
|-------------|--------------|---------------|
| Special Teams Enhanced | 6 | +0.3-0.5pp |
| PDO Regression | 4 | +0.2-0.4pp |
| Goalie Home/Away | 4 | +0.1-0.2pp |
| **Total** | **14** | **+0.6-1.1pp** |

**Conservative Estimate (50% of expected):** +0.3-0.55pp
**Target Needed:** 0.62pp to reach 62%

---

## 🚀 Implementation Plan

### Phase 1: Special Teams Enhancement (3-4 hours)
1. Extract PP goals, SH goals, PP opportunities from game data
2. Create 6 enhanced special teams features
3. Add to V7.4 feature pipeline
4. Train and evaluate

**Decision Point:** If this gets us to 61.7%+, proceed to Phase 2

### Phase 2: PDO Regression (2-3 hours)
1. Calculate PDO (SH% + SV%) rolling windows
2. Create sustainability metrics
3. Add 4 PDO features
4. Train and evaluate

**Decision Point:** If combined gets us to 62%+, DONE!

### Phase 3: Goalie Splits (2-3 hours, if needed)
1. Split goalie metrics by home/away
2. Calculate home advantage
3. Add 4 goalie split features
4. Train and evaluate

**Total Time:** 7-10 hours across 3 phases

---

## 💡 Why This Will Work

1. **Filling Gaps:** Special teams are completely missing from current model
2. **Proven in Literature:** PDO regression is well-established in hockey analytics
3. **Enhancing Strengths:** Goalie features already work (#2, #4), make them better
4. **Additive:** These features provide NEW information, not collinear with existing

---

## 🎯 Success Criteria

**Minimum Acceptable (V7.4):**
- Accuracy: ≥61.7% (+0.3pp over V7.3)
- Shows progress toward 62%

**Target (V7.4):**
- Accuracy: ≥62.0% (✅ target achieved)
- Log Loss: ≤0.670 (already achieved in V7.3)

**Stretch (V7.4):**
- Accuracy: ≥62.5% (beyond target)
- A+ Confidence: ≥72%

---

## 📋 Recommendation

**Start with Phase 1: Enhanced Special Teams**

This is the biggest gap in the current model. Special teams account for 20-25% of goals but have zero weight in our model. This alone could close the 0.62pp gap.

**Should I implement Phase 1 (Enhanced Special Teams features) now?**
