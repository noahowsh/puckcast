<div align="center">
  <img src="assets/logo.png" alt="Puckcast.ai Logo" width="150"/>
  
  # Puckcast.ai
  ### Data-Driven NHL Prediction Intelligence
  
  [![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Status: Production](https://img.shields.io/badge/Status-Production-brightgreen.svg)]()
</div>

---

A comprehensive machine learning system for predicting NHL game outcomes using professional-grade analytics data, advanced features, and rigorous validation.

## 🏒 Overview

**Puckcast.ai** implements an end-to-end pipeline that:
- Leverages **MoneyPuck** data with expected goals (xG) and shot quality metrics
- Engineers **141 features** capturing team strength, momentum, rest, goaltending, and matchups
- Trains using **3,690 games** from 2021-2024 seasons
- Provides an elite interactive dashboard with 7 analytical pages
- Achieves **59.2% test accuracy**, beating baseline by 6.1 percentage points
- **Future:** Evaluate model against betting markets for ROI analysis

**Key Features:**
- ✅ Professional-grade data from MoneyPuck (same source used by NHL analysts)
- ✅ Sophisticated feature engineering (rolling stats, Elo ratings, rest metrics)
- ✅ Proper temporal validation preventing data leakage
- ✅ Model comparison with hyperparameter tuning
- ✅ Comprehensive evaluation (accuracy, log loss, ROC-AUC, Brier score, calibration)
- ✅ Interactive Streamlit dashboard
- ✅ Production-ready modular codebase

## 📊 Results

**Puckcast.ai** achieves strong performance on the 2024-25 NHL season:
- **Test Accuracy:** 59.2% (baseline: 53.1% from home advantage)
- **ROC-AUC:** 0.624 (excellent discrimination)
- **Log Loss:** 0.675 (well calibrated)
- **Brier Score:** 0.241 (strong probability estimates)

**Most Important Predictive Features:**
1. **Back-to-back differential** (`is_b2b_diff`) - Fatigue impact
2. **Rolling Corsi (10 games)** - Shot attempt dominance  
3. **Elo rating differential** - Team strength
4. **High-danger shot differential** - Shot quality
5. **Goaltending save %** - Goalie performance

**Model leverages:**
- 141 engineered features
- Rolling averages (3, 5, 10 game windows)
- Advanced metrics (xG, Corsi, Fenwick, shot quality)
- Goaltending quality (Save %, GSAx)
- Rest and scheduling features

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- pip package manager
- Internet connection (for fetching NHL data)

### Installation

1. **Clone the repository:**
```bash
git clone [your-repo-url]
cd NHLpredictionmodel
```

2. **Create and activate virtual environment:**
```bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

### Running the Project

#### Option 1: Interactive Dashboard (Recommended)

Launch the Streamlit dashboard to explore predictions interactively:

```bash
streamlit run streamlit_app.py
```

Navigate to `http://localhost:8501` in your browser.

**Dashboard Features:**
- Configure training and test seasons
- Compare multiple models side-by-side
- View performance metrics (accuracy, ROC-AUC, log loss)
- Explore individual game predictions with filters
- Analyze feature importance
- Download predictions as CSV

#### Option 2: Command-Line Training

Train models and view metrics in the terminal:

```bash
# Train on default seasons (2021-22, 2022-23) and test on 2023-24
python -m nhl_prediction.train

# Custom season configuration
python -m nhl_prediction.train \
    --train-seasons 20212022 \
    --train-seasons 20222023 \
    --test-season 20232024
```

Output includes:
- Model selection and hyperparameter tuning results
- Training and test metrics
- Comparison of Logistic Regression vs Gradient Boosting

## 📁 Project Structure

```
NHLpredictionmodel/
├── README.md                      # This file
├── requirements.txt               # Python dependencies
├── streamlit_app.py              # Interactive dashboard
│
├── data/
│   └── nhl_teams.csv             # NHL team reference data
│
├── docs/
│   ├── taxonomy.md               # Data schema and feature definitions
│   ├── usage.md                  # Detailed usage instructions
│   └── group_report_2.md         # Comprehensive project report
│
├── reports/                       # Generated outputs
│   ├── calibration_curve.png     # Probability calibration plot
│   ├── confusion_matrix.png      # Classification confusion matrix
│   ├── roc_curve.png             # ROC curve with AUC
│   ├── model_comparison.png      # Model performance comparison
│   ├── feature_importance.csv    # Ranked feature coefficients
│   └── predictions_20232024.csv  # Test set predictions
│
└── src/nhl_prediction/           # Core package
    ├── __init__.py               # Package initialization
    ├── data_ingest.py           # MoneyPuck data loading
    ├── features.py              # Feature engineering logic
    ├── pipeline.py              # Dataset construction and Elo ratings
    ├── model.py                 # Model creation and utilities
    ├── train.py                 # Training CLI and model comparison
    └── report.py                # Visualization generation
```

## 🧪 How It Works

### 1. Data Ingestion (`data_ingest.py`)

Loads team game logs from MoneyPuck's comprehensive database:
```python
from nhl_prediction.data_ingest import fetch_multi_season_logs

# Fetch data for multiple seasons
logs = fetch_multi_season_logs(['20212022', '20222023', '20232024'])
```

**Data Sources:**
- **MoneyPuck** (`data/moneypuck_all_games.csv`) - Game-by-game team statistics including:
  - Expected goals (xG) for shot quality analysis
  - High/medium/low danger shot breakdowns
  - Corsi & Fenwick possession metrics
  - Advanced analytics unavailable in official NHL feeds
- Static team metadata from `data/nhl_teams.csv`

MoneyPuck provides superior data quality compared to official APIs, including shot quality and expected goals metrics used by professional analysts.

### 2. Feature Engineering (`features.py`)

Creates 129 features per game, including:

**Team Strength (Season-to-Date):**
- Win percentage, goal differential, shot margin
- Points, points percentage, points per game

**Recent Form (Rolling Windows over 3, 5, 10 games):**
- Win percentage, goal differential
- Power-play %, penalty-kill %, faceoff win %
- Shots for/against per game

**Momentum Indicators:**
- Difference between recent form and season averages
- Captures hot/cold streaks

**Rest & Scheduling:**
- Days since previous game
- Back-to-back game indicators
- Schedule congestion (games in last 3/6 days)
- Categorical rest buckets

**Elo Rating System:**
- Season-specific Elo ratings (reset each season)
- Margin-adjusted updates
- Home ice advantage (+30 Elo points)

**Matchup-Specific:**
- Special teams matchups (home PP% vs away PK%)
- Team identity (one-hot encoded)

**Differential Features:**
- Home minus away for most metrics
- Directly captures relative advantage

All features are **lagged** - computed using only information available before each game to prevent data leakage.

### 3. Model Training (`model.py`, `train.py`)

**Models Evaluated:**
1. **Logistic Regression** (baseline)
   - Linear model with L2 regularization
   - Interpretable coefficients
   - StandardScaler preprocessing

2. **Histogram Gradient Boosting** (advanced)
   - Non-linear ensemble model
   - Can capture feature interactions
   - Robust to feature scaling

**Training Strategy:**
- **Temporal split:** Train on 2021-22 + 2022-23, test on 2023-24
- **Validation:** Hold out final training season (2022-23) for hyperparameter tuning
- **Hyperparameter search:** Grid search on validation set
- **Calibration:** Isotonic regression for probability calibration
- **Threshold optimization:** Find optimal decision threshold beyond 0.5

**Evaluation Metrics:**
- Accuracy: Proportion of correct predictions
- ROC-AUC: Area under ROC curve (discrimination ability)
- Log Loss: Penalizes confident wrong predictions
- Brier Score: Mean squared error of probabilities
- Calibration: Do predicted probabilities match observed frequencies?

### 4. Interactive Dashboard (`streamlit_app.py`)

Provides a user-friendly interface for:
- Configuring train/test season splits
- Comparing model performance
- Filtering predictions by team, date, correctness
- Visualizing feature importance
- Downloading results

Built with Streamlit for rapid prototyping and easy deployment.

## 📈 Example Usage

### Python API

```python
from nhl_prediction.pipeline import build_dataset
from nhl_prediction.train import compare_models

# Build dataset for multiple seasons
seasons = ['20212022', '20222023', '20232024']
dataset = build_dataset(seasons)

# Compare models
train_seasons = ['20212022', '20222023']
test_season = '20232024'
results = compare_models(dataset, train_seasons, test_season)

# Get best model and predictions
best_model = results['best_result']['model']
test_metrics = results['best_result']['test_metrics']

print(f"Test Accuracy: {test_metrics['accuracy']:.3f}")
print(f"Test ROC-AUC: {test_metrics['roc_auc']:.3f}")
```

### Analyzing Feature Importance

```python
from nhl_prediction.model import compute_feature_effects

# Get feature importance (for Logistic Regression)
importance = compute_feature_effects(model, feature_names)
print(importance.head(10))
```

### Making Predictions

```python
from nhl_prediction.model import predict_probabilities

# Predict on new games
probs = predict_probabilities(model, features, mask)
print(f"Home win probability: {probs[0]:.2%}")
```

## 🔬 Methodology Highlights

### Preventing Data Leakage

**Critical:** All features use only information available *before* each game.

- Rolling statistics are **lagged by 1 game** (`.shift(1)`)
- Season-to-date metrics computed using **cumulative sums up to (not including) current game**
- Elo ratings updated **after** each game, pre-game ratings used as features

### Temporal Validation

Unlike random train/test splits, we use **chronological** splits:
- Train: 2021-22, 2022-23 seasons (past)
- Test: 2023-24 season (future)

This reflects real-world deployment where we predict future games, not random historical ones.

### Handling Class Imbalance

Home teams win ~55% of games (mild imbalance):
- Use probabilistic metrics (log loss, Brier score, ROC-AUC) not just accuracy
- Optimize decision threshold on validation set
- Consider both home and away predictions

### Feature Engineering Rationale

**Why these features?**
- **Faceoffs:** Control puck possession → scoring chances
- **Special teams:** PP/PK directly impact goals
- **Rest:** Fatigue affects performance (especially back-to-backs)
- **Momentum:** Recent form captures injuries, lineup changes, confidence
- **Elo:** Aggregates overall team quality in single number
- **Matchups:** Some teams match up better against others

## 📊 Visualizations

Generated visualizations in `reports/`:

### ROC Curve
Shows model's ability to discriminate between wins and losses across all decision thresholds.

### Calibration Curve
Compares predicted probabilities to observed frequencies. Well-calibrated models have points near the diagonal.

### Confusion Matrix
Breakdown of correct predictions (true positives/negatives) and errors (false positives/negatives).

### Feature Importance
Ranking of features by impact on predictions. Positive coefficients favor home team, negative favor away team.

## 🛠️ Development

### Running Tests

```bash
# (Add if you create tests)
pytest tests/
```

### Code Style

- Type hints throughout (`from __future__ import annotations`)
- Docstrings for all public functions
- PEP 8 formatting
- Modular design (separation of concerns)

### Adding New Features

1. Add feature engineering logic to `features.py`
2. Ensure features are lagged (no data leakage)
3. Update feature list in `pipeline.py`
4. Retrain models and check performance

### Adding New Models

1. Create model factory function in `model.py`
2. Add to `compare_models()` in `train.py`
3. Implement hyperparameter tuning if needed

## 📚 Documentation

- **`docs/taxonomy.md`** - Data schema, entity relationships, feature definitions
- **`docs/usage.md`** - Detailed usage instructions
- **`docs/group_report_2.md`** - Comprehensive project report with methodology, results, analysis

## 🙏 Acknowledgments

**Data Sources:**
- **MoneyPuck** (`https://moneypuck.com/`) - Game-by-game team statistics with advanced metrics
  - Expected goals (xG), shot quality, Corsi/Fenwick, and more
  - Free, publicly available hockey analytics data
  - Used by professional analysts and hockey researchers
- NHL team metadata

**Libraries:**
- pandas, NumPy - Data manipulation
- scikit-learn - Machine learning
- Streamlit - Interactive dashboard
- matplotlib, Altair - Visualization

## 📝 Citation

If you use this project, please cite:

```
[Your Name/Team Name]. (2025). NHL Game Prediction Model. 
GitHub repository: [your-repo-url]
```

## 📧 Contact

[Your Name/Team]
[Your Email]

## 📄 License

[Add license if applicable - e.g., MIT, Apache 2.0]

---

**Built with ❤️ and 🏒 by [Your Team Name]**

