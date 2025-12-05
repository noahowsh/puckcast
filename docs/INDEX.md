# 📚 Puckcast Documentation Index

> **Last Updated**: December 4, 2024  
> **Branch**: `claude/v7-beta-01111xrERXjGtBfF6RaMBsNr`  
> **Production Model**: V7.3 Situational Features (61.38%)

---

## 🎯 Quick Start

**New to the project?** Start here:
1. **[../README.md](../README.md)** - Project overview and quick start
2. **[current/V7.3_PRODUCTION_MODEL.md](current/V7.3_PRODUCTION_MODEL.md)** - Production model guide  
3. **[current/CLOSING_GAP_ANALYSIS.md](current/CLOSING_GAP_ANALYSIS.md)** - Why we can't reach 62%

---

## 📁 Documentation Structure

```
docs/
├── INDEX.md                      # ← You are here
├── current/                      # Current Model Documentation
│   ├── V7.3_PRODUCTION_MODEL.md
│   ├── CLOSING_GAP_ANALYSIS.md
│   └── PROJECT_STATUS.md
├── experiments/                  # Experiment Documentation  
│   ├── V7.4_HEAD_TO_HEAD.md
│   ├── V7.5_INTERACTIONS.md
│   ├── V7.6_TEAM_CALIBRATION.md
│   ├── V7.7_CONFIDENCE_FILTERING.md
│   └── GOALIE_TRACKING.md
└── archive/                      # Historical Documentation
```

---

## 📊 Current Model (V7.3)

### [current/V7.3_PRODUCTION_MODEL.md](current/V7.3_PRODUCTION_MODEL.md)
✅ **Status**: Production  
📅 **Created**: Dec 3, 2024 | **Updated**: Dec 4, 2024

Complete production model guide with features, metrics, training instructions.

**Key Metrics**: 61.38% accuracy, 216 features, ROC-AUC 0.6432

---

### [current/CLOSING_GAP_ANALYSIS.md](current/CLOSING_GAP_ANALYSIS.md)  
📅 **Created**: Dec 4, 2024

Comprehensive analysis of why we couldn't reach 62%:
- All 4 failed attempts (V7.4-7.7) explained
- Root cause analysis  
- Recommendations for exceeding 62%

---

### [current/PROJECT_STATUS.md](current/PROJECT_STATUS.md)
📅 **Created**: Dec 4, 2024

Current project state, next steps, decision framework.

---

## 🧪 Experiments

### [experiments/V7.4_HEAD_TO_HEAD.md](experiments/V7.4_HEAD_TO_HEAD.md)
❌ **Failed** - 60.00% (-1.38pp)  
📅 Dec 4, 2024

H2H matchup features. Data leakage bug found and fixed. Multi collinearity killed performance.

---

### [experiments/V7.5_INTERACTIONS.md](experiments/V7.5_INTERACTIONS.md)
❌ **Failed** - 60.08% (-1.30pp)  
📅 Dec 4, 2024

Feature interaction terms. Overfitting without new signal.

---

### [experiments/V7.6_TEAM_CALIBRATION.md](experiments/V7.6_TEAM_CALIBRATION.md)
❌ **Failed** - 60.73% (-0.65pp)  
📅 Dec 4, 2024

Team-specific bias adjustments. Weak signal, already captured.

---

### [experiments/V7.7_CONFIDENCE_FILTERING.md](experiments/V7.7_CONFIDENCE_FILTERING.md)
⚠️ **Partial** - 62.71% (69% coverage)  
📅 Dec 4, 2024

Calibration analysis. Can hit 62.71% by excluding 31% of games.

---

### [experiments/GOALIE_TRACKING.md](experiments/GOALIE_TRACKING.md)
❌ **Failed** - 58.62% (-2.76pp) | ✅ **Infrastructure Valuable**  
📅 Dec 3, 2024 | **Updated**: Dec 4, 2024

Individual goalie tracking. Infrastructure ready for stats pages.

---

## 📦 Archive

Historical docs from earlier development stages in `archive/` directory.

---

## 📈 Version History

| Version | Accuracy | Date | Status | Documentation |
|---------|----------|------|--------|---------------|
| V7.0 | 60.89% | Dec 2 | Superseded | Baseline |
| V7.1 | 58.62% | Dec 3 | Failed | [GOALIE_TRACKING.md](experiments/GOALIE_TRACKING.md) |
| **V7.3** | **61.38%** | **Dec 3** | **✅ PRODUCTION** | **[V7.3_PRODUCTION_MODEL.md](current/V7.3_PRODUCTION_MODEL.md)** |
| V7.4 | 60.00% | Dec 4 | Failed | [V7.4_HEAD_TO_HEAD.md](experiments/V7.4_HEAD_TO_HEAD.md) |
| V7.5 | 60.08% | Dec 4 | Failed | [V7.5_INTERACTIONS.md](experiments/V7.5_INTERACTIONS.md) |
| V7.6 | 60.73% | Dec 4 | Failed | [V7.6_TEAM_CALIBRATION.md](experiments/V7.6_TEAM_CALIBRATION.md) |
| V7.7 | 62.71%* | Dec 4 | Partial | [V7.7_CONFIDENCE_FILTERING.md](experiments/V7.7_CONFIDENCE_FILTERING.md) |

*Requires excluding 31% of games

---

**Last Updated**: Dec 4, 2024 by Claude Agent SDK
