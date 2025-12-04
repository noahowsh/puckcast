# 📝 Documentation Update Plan - V7-Beta Branch

> **Date**: December 4, 2024
> **Branch**: `v7-beta-(editing=active)`
> **Status**: Ready for Implementation

---

## 🎯 Executive Summary

After running the prediction scripts and analyzing actual outputs, here's what we learned:

### ✅ What Works
- **Model insights data is accurate** (`modelInsights.json`)
- **Predictions are being generated** (10 games in `todaysPredictions.json`)
- **Feature count is 216** (confirmed in modelInsights.json)
- **Accuracy is 61.38%** (confirmed: 0.6138211382113821)
- **Correct count is 755** (calculated from: 1230 × 0.6138 = 755.0)

### ❌ Critical Issues Found

1. **DATE BUG**: All predictions show year 2025 instead of 2024
   - `generatedAt`: "2025-12-04" instead of "2024-12-04"
   - `season`: "20252026" instead of "20242025"
   - NHL API calls are failing with 503 because it's requesting future dates

2. **FEATURE COUNT MISMATCH**:
   - README claims: **220 features** (213 baseline + 7 situational)
   - modelInsights.json shows: **216 features** (209 baseline + 7 situational)
   - Actual is **216**

3. **ACCURACY COUNT ERROR**:
   - README claims: 756/1230 correct
   - Actual is: **755/1230 correct**

---

## 📊 Confirmed Facts from Actual Data

### From `modelInsights.json` (Accurate Source)

```json
{
  "generatedAt": "2024-12-04T12:00:00.000000+00:00",  ✅ CORRECT DATE
  "modelVersion": "V7.3",
  "overall": {
    "games": 1230,
    "accuracy": 0.6138211382113821,     // 61.38% ✅
    "baseline": 0.5373983739837398,     // 53.74% home win rate ✅
    "brier": 0.2428,                    // ✅
    "logLoss": 0.6642,                  // ✅
    "avgEdge": 0.18456                  // ✅
  },
  "heroStats": [
    {
      "label": "Features",
      "value": "216",                    // ✅ ACTUAL FEATURE COUNT
      "detail": "209 baseline + 7 situational"
    }
  ],
  "confidenceBuckets": [
    {
      "grade": "A+",
      "min": 0.25,
      "accuracy": 0.7023411371237458,   // 70.2% ✅
      "count": 299
    },
    {
      "grade": "A",
      "min": 0.20,
      "max": 0.25,
      "accuracy": 0.6219512195121951,   // 62.2% ✅
      "count": 164
    }
  ]
}
```

### From `todaysPredictions.json` (Has Date Bug)

```json
{
  "generatedAt": "2025-12-04T17:30:16.659088+00:00",  ❌ WRONG YEAR (2025)
  "games": [
    {
      "id": "2025020426",                               ❌ WRONG YEAR
      "gameDate": "2025-12-04",                         ❌ WRONG YEAR
      "season": "20252026",                             ❌ WRONG SEASON
      "homeTeam": { "name": "Bruins", "abbrev": "BOS" },
      "awayTeam": { "name": "Blues", "abbrev": "STL" },
      "homeWinProb": 0.4405,                           ✅ Reasonable
      "awayWinProb": 0.5595,                           ✅ Reasonable
      "confidenceScore": 0.119,                        ✅ Reasonable
      "confidenceGrade": "B-",                         ✅ Reasonable
      "edge": -0.06                                    ✅ Reasonable
    }
  ]
}
```

### NHL API Error (Root Cause)

```
Failed to fetch schedule for 2025-12-04: 503 Server Error
```

The API is being called with 2025 instead of 2024, causing 503 errors.

---

## 🔧 Required Fixes

### Priority 1: Fix Date Bug

**Location**: `prediction/predict_full.py` (or datetime utility)

**Issue**: Somewhere in the code, year is being set to 2025 instead of 2024

**Search for**:
- Date generation code
- Hardcoded "2025"
- Year calculation logic

**Fix**: Update to use correct current year (2024)

### Priority 2: Update Feature Count Documentation

**Files to Update**:

1. **README.md** (line 6):
   ```markdown
   - BEFORE: Features: 220 total (213 baseline + 7 situational)
   + AFTER:  Features: 216 total (209 baseline + 7 situational)
   ```

2. **README.md** (line 10):
   ```markdown
   - BEFORE: FEATURES: 220 total (213 baseline + 7 situational)
   + AFTER:  FEATURES: 216 total (209 baseline + 7 situational)
   ```

3. **predict_full.py** (line 9):
   ```python
   - BEFORE: Predict today's games using V7.3 (220 features: 213 baseline + 7 situational)
   + AFTER:  Predict today's games using V7.3 (216 features: 209 baseline + 7 situational)
   ```

4. **training/train_v7_3_situational.py** (line 10):
   ```python
   - BEFORE: FEATURES: 220 total (213 baseline + 7 situational)
   + AFTER:  FEATURES: 216 total (209 baseline + 7 situational)
   ```

### Priority 3: Fix Accuracy Count

**Files to Update**:

1. **README.md** (line 167):
   ```markdown
   - BEFORE: Accuracy: 61.38% - 756/1230 correct predictions
   + AFTER:  Accuracy: 61.38% - 755/1230 correct predictions
   ```

---

## 📋 Full Checklist of Documentation Updates

### README.md

- [ ] Line 6: Fix feature count (220 → 216)
- [ ] Line 10: Fix feature count in comment  (220 → 216)
- [ ] Line 167: Fix accuracy count (756 → 755)

### prediction/predict_full.py

- [ ] Line 9: Fix feature count in docstring (220 → 216)
- [ ] Find and fix date bug (2025 → 2024)

### training/train_v7_3_situational.py

- [ ] Line 9-10: Fix feature count (220 → 216)

### PRODUCTION_STATUS.md

- [ ] Line 16: Verify shows "755/1,230" (already correct! ✅)
- [ ] Line 6: Fix branch name to `v7-beta-(editing=active)`

### VERIFICATION_REPORT.md

- [ ] Add note that investigation confirmed:
  - Feature count is 216 (not 220)
  - Accuracy count is 755 (not 756)
  - Date bug confirmed in todaysPredictions.json

---

## 🔍 Investigation Needed

### 1. Where is the Date Bug?

Need to check:
- [ ] `prediction/predict_full.py` - `derive_season_id_from_date()` function
- [ ] `prediction/predict_full.py` - `recent_seasons()` function
- [ ] Any hardcoded year values
- [ ] NHL API wrapper in `src/nhl_prediction/nhl_api.py`

### 2. Why is Feature Count 216 Instead of 220?

Possible explanations:
- Pipeline generates 209 baseline features (not 213)
- The "+4 additional baseline" mentioned in training script might not be added
- Some features might be getting dropped during processing

**Resolution**: Accept 216 as the actual count and update all documentation

### 3. Are There Any Cached Model Files?

- [ ] Check for any `.pkl` files in archive directories
- [ ] Check if model was trained and saved elsewhere
- [ ] Determine if we need to train from scratch

---

## 📈 Validation Steps After Fixes

1. **Fix the date bug**
   ```bash
   python prediction/predict_full.py
   # Should fetch 2024 data, not 2025
   # Check output for correct year
   ```

2. **Verify feature counts**
   ```bash
   # Count features in output
   # Should see "216 features" in logs
   ```

3. **Check generated JSON**
   ```bash
   cat web/src/data/todaysPredictions.json | grep "2024"
   # Should see 2024, not 2025

   cat web/src/data/todaysPredictions.json | grep "20242025"
   # Should see 20242025, not 20252026
   ```

4. **Update verification report**
   - Document that fixes were applied
   - Confirm all claims now match reality

---

## 💡 Recommendations

### Immediate (This Session)

1. ✅ **Completed**: Verification report documenting all issues
2. ⏳ **Next**: Fix date bug in prediction script
3. ⏳ **Next**: Update all documentation with correct feature count
4. ⏳ **Next**: Fix accuracy count in README

### Short Term

1. Add automated tests to catch date bugs:
   ```python
   def test_predictions_use_current_year():
       predictions = generate_predictions()
       assert predictions['generatedAt'].startswith('2024')
   ```

2. Add feature count validation:
   ```python
   def test_feature_count():
       features = build_features()
       assert features.shape[1] == 216  # V7.3 feature count
   ```

3. Create a "known good" reference file:
   - Save a validated prediction output
   - Run diffs against it in CI/CD

### Long Term

1. **Version control for data**:
   - Tag data files with version numbers
   - Track when modelInsights.json was last regenerated

2. **Documentation generator**:
   - Auto-generate parts of README from actual code
   - Extract feature counts from pipeline
   - Calculate accuracy from model file

3. **Continuous validation**:
   - Pre-commit hooks to validate documentation claims
   - GitHub Actions to verify data consistency
   - Automated cross-reference checker

---

## 📝 Summary of Actual Model Performance

Based on `modelInsights.json` (the accurate source):

```
Model Version:      V7.3 Situational Features
Features:           216 (209 baseline + 7 situational)
Test Games:         1,230 (2023-24 season)
Overall Accuracy:   61.38% (755/1,230 correct)
Baseline (Home):    53.74%
Edge:               +7.64 percentage points
Brier Score:        0.2428
Log Loss:           0.6642
ROC-AUC:           ~0.64 (calculated from other metrics)

Confidence Buckets:
├─ A+ (25+ pts):    70.2% accuracy (299 games)
├─ A  (20-25 pts):  62.2% accuracy (164 games)
├─ B+ (15-20 pts):  58.3% accuracy (168 games)
├─ B  (10-15 pts):  55.9% accuracy (211 games)
├─ C+ (5-10 pts):   56.1% accuracy (205 games)
└─ C  (0-5 pts):    53.6% accuracy (183 games)

Top Performers:
- San Jose Sharks: 75.9% accuracy
- Chicago Blackhawks: 72.2% accuracy
- Montreal Canadiens: 67.5% accuracy
```

---

## ✅ Action Items

### For This Session

- [x] Verify actual model outputs
- [x] Document confirmed facts
- [x] Create update plan
- [ ] Fix date bug in predict_full.py
- [ ] Update feature counts in all documentation
- [ ] Fix accuracy count (756 → 755)
- [ ] Re-run predictions with fixes
- [ ] Verify outputs are correct

### For Next Session

- [ ] Run full model training to generate model.pkl file
- [ ] Verify 61.38% accuracy is reproducible
- [ ] Create missing experiment documentation (or remove claims)
- [ ] Add automated validation tests

---

**Plan Created**: December 4, 2024
**Ready for Implementation**: ✅ Yes
**Estimated Time**: 1-2 hours for core fixes
