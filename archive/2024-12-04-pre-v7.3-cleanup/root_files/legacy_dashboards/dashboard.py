"""
NHL Prediction Model - Unified Dashboard
Shows model performance + today's predictions
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime, timedelta
from nhl_prediction.pipeline import build_dataset
from nhl_prediction.model import create_baseline_model, fit_model, predict_probabilities, compute_metrics
from nhl_prediction.nhl_api import fetch_schedule

# Configure page with better UX
st.set_page_config(
    page_title="NHL Prediction Dashboard",
    page_icon="🏒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load data (cached)
@st.cache_data(ttl=3600)
def load_model_data():
    """Load and cache model data."""
    # Build dataset
    dataset = build_dataset(['20212022', '20222023', '20232024', '20242025'])
    
    # Separate train/val/test
    train_mask = dataset.games['seasonId'].isin(['20212022', '20222023', '20232024'])
    val_mask = dataset.games['seasonId'] == '20242025'
    test_mask = dataset.games['seasonId'] == '20242025'
    
    # Train model
    model = create_baseline_model(C=1.0)
    model = fit_model(model, dataset.features, dataset.target, train_mask)
    
    # Get predictions
    train_probs = predict_probabilities(model, dataset.features, train_mask)
    test_probs = predict_probabilities(model, dataset.features, test_mask)
    
    # Compute metrics
    train_metrics = compute_metrics(dataset.target[train_mask], train_probs)
    test_metrics = compute_metrics(dataset.target[test_mask], test_probs)
    
    # Feature importance (access coefficients from pipeline)
    coefs = model.named_steps['clf'].coef_[0]
    importance_df = pd.DataFrame({
        'Feature': dataset.features.columns,
        'Coefficient': coefs,
        'Abs_Coefficient': abs(coefs)
    })
    
    # Filter out team dummy variables and rest bucket dummies
    importance_df = importance_df[
        ~importance_df['Feature'].str.contains('home_team_|away_team_|rest_home_|rest_away_', regex=True)
    ].sort_values('Abs_Coefficient', ascending=False).head(15)
    
    return {
        'dataset': dataset,
        'model': model,
        'train_mask': train_mask,
        'test_mask': test_mask,
        'train_metrics': train_metrics,
        'test_metrics': test_metrics,
        'importance': importance_df,
        'train_probs': train_probs,
        'test_probs': test_probs
    }

@st.cache_data(ttl=600)  # Cache for 10 minutes
def load_predictions_for_date(target_date):
    """Load predictions for a specific date."""
    date_str = target_date.strftime('%Y-%m-%d')
    
    # Try multiple date formats for the CSV file
    possible_files = [
        Path(f'predictions_{date_str}.csv'),
        Path(f'predictions_{target_date.strftime("%Y%m%d")}.csv'),
    ]
    
    for pred_file in possible_files:
        if pred_file.exists():
            df = pd.read_csv(pred_file)
            
            # Filter to only games on this specific date
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                df = df[df['date'].dt.date == target_date.date()]
            
            if len(df) > 0:
                return df
    
    return None

@st.cache_data(ttl=3600)
def get_actual_results(target_date):
    """Get actual game results for a past date from the dataset."""
    try:
        from datetime import timedelta
        
        # Only try to get results if date is in the past
        if target_date.date() >= datetime.now().date():
            return None
        
        # Load the dataset
        dataset = build_dataset(['20242025'])
        games = dataset.games.copy()
        
        # Filter to target date
        games['gameDate'] = pd.to_datetime(games['gameDate'])
        games_on_date = games[games['gameDate'].dt.date == target_date.date()]
        
        if len(games_on_date) == 0:
            return None
        
        # Return matchups with results
        results = []
        for _, game in games_on_date.iterrows():
            results.append({
                'away_team': game.get('teamAbbrev_away', 'Away'),
                'home_team': game.get('teamAbbrev_home', 'Home'),
                'away_score': int(game.get('away_score', 0)),
                'home_score': int(game.get('home_score', 0)),
                'home_win': int(game.get('home_win', 0))
            })
        
        return pd.DataFrame(results) if results else None
    except Exception as e:
        return None

@st.cache_data(ttl=3600)
def get_recent_model_performance():
    """Calculate model's recent performance on last 20 games."""
    try:
        # Build full dataset including training seasons
        dataset = build_dataset(['20212022', '20222023', '20232024', '20242025'])
        games = dataset.games.copy()
        games['gameDate'] = pd.to_datetime(games['gameDate'])
        
        # Get games from current season with results (past games only)
        current_season = games[games['seasonId'] == '20242025'].copy()
        current_season = current_season[current_season['gameDate'] < pd.Timestamp.now()]
        
        # Need at least 10 games
        if len(current_season) < 10:
            return None
        
        # Get last N games (up to 20)
        num_recent = min(20, len(current_season))
        recent = current_season.sort_values('gameDate').tail(num_recent)
        
        # Train model on previous seasons only
        train_mask = games['seasonId'].isin(['20212022', '20222023', '20232024'])
        model = create_baseline_model(C=1.0)
        model = fit_model(model, dataset.features, dataset.target, train_mask)
        
        # Get predictions for recent games
        recent_indices = recent.index
        recent_probs = predict_probabilities(model, dataset.features, recent_indices)
        recent_preds = (recent_probs >= 0.5).astype(int)
        recent_actuals = dataset.target.loc[recent_indices]
        
        correct = (recent_preds == recent_actuals).sum()
        total = len(recent_preds)
        
        return {
            'correct': correct,
            'total': total,
            'accuracy': correct / total if total > 0 else 0
        }
    except Exception as e:
        # Return None on error - will show "Tracking..." message
        return None

@st.cache_data(ttl=3600)
def calculate_feature_contributions(model, features, feature_names, game_index):
    """Calculate individual feature contributions for a specific game prediction."""
    try:
        # Get coefficients
        coefs = model.named_steps['clf'].coef_[0]
        intercept = model.named_steps['clf'].intercept_[0]
        
        # Get feature values for this specific game
        game_features = features.iloc[game_index].values
        
        # Calculate contribution of each feature
        contributions = game_features * coefs
        
        # Create dataframe
        contrib_df = pd.DataFrame({
            'Feature': feature_names,
            'Value': game_features,
            'Coefficient': coefs,
            'Contribution': contributions
        })
        
        # Filter out team dummies and rest buckets
        contrib_df = contrib_df[
            ~contrib_df['Feature'].str.contains('home_team_|away_team_|rest_home_|rest_away_', regex=True)
        ]
        
        # Sort by absolute contribution
        contrib_df['Abs_Contribution'] = contrib_df['Contribution'].abs()
        contrib_df = contrib_df.sort_values('Abs_Contribution', ascending=False)
        
        return contrib_df, intercept
    except Exception as e:
        return None, None

@st.cache_data(ttl=600)
def get_historical_accuracy():
    """Calculate model's accuracy over time (weekly buckets)."""
    try:
        # Build dataset
        dataset = build_dataset(['20242025'])
        games = dataset.games.copy()
        games['gameDate'] = pd.to_datetime(games['gameDate'])
        
        # Filter to past games only
        games = games[games['gameDate'] < pd.Timestamp.now()].copy()
        
        if len(games) < 10:
            return None
        
        # Train model on previous seasons
        full_dataset = build_dataset(['20212022', '20222023', '20232024', '20242025'])
        train_mask = full_dataset.games['seasonId'].isin(['20212022', '20222023', '20232024'])
        model = create_baseline_model(C=1.0)
        model = fit_model(model, full_dataset.features, full_dataset.target, train_mask)
        
        # Get predictions for current season games
        game_indices = games.index
        probs = predict_probabilities(model, full_dataset.features, game_indices)
        preds = (probs >= 0.5).astype(int)
        actuals = full_dataset.target.loc[game_indices]
        
        # Add predictions to games dataframe
        games['predicted'] = preds.values
        games['actual'] = actuals.values
        games['correct'] = (games['predicted'] == games['actual']).astype(int)
        games['probability'] = probs.values
        
        # Group by week
        games['week'] = games['gameDate'].dt.isocalendar().week
        games['week_start'] = games['gameDate'] - pd.to_timedelta(games['gameDate'].dt.dayofweek, unit='d')
        
        weekly_stats = games.groupby('week_start').agg({
            'correct': ['sum', 'count'],
            'probability': 'mean'
        }).reset_index()
        
        weekly_stats.columns = ['week_start', 'correct', 'total', 'avg_prob']
        weekly_stats['accuracy'] = weekly_stats['correct'] / weekly_stats['total']
        weekly_stats['week_label'] = weekly_stats['week_start'].dt.strftime('%b %d')
        
        return weekly_stats, games
    except Exception as e:
        return None, None

def get_feature_explanation(feature_name):
    """Get human-readable explanation for a feature."""
    explanations = {
        'is_b2b': 'Back-to-back game (played yesterday)',
        'elo': 'Team strength rating',
        'rolling_corsi': 'Shot attempt differential (possession)',
        'rolling_fenwick': 'Unblocked shot attempt differential',
        'rolling_xg': 'Expected goals based on shot quality',
        'rolling_high_danger': 'High danger scoring chances',
        'rolling_save_pct': 'Goaltender save percentage',
        'rolling_gsax': 'Goals saved above expected (goalie quality)',
        'rolling_win_pct': 'Recent win percentage',
        'rolling_goal_diff': 'Recent goal differential',
        'rest': 'Days of rest since last game',
        'games_played': 'Games played this season',
    }
    
    for key, explanation in explanations.items():
        if key in feature_name.lower():
            return explanation
    
    return feature_name.replace('_', ' ').title()

# Custom CSS for better UX
st.markdown("""
<style>
    /* Loading animation */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    .loading { animation: pulse 2s infinite; }
    
    /* Smooth transitions */
    .stButton button {
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Better tooltips */
    .tooltip {
        position: relative;
        display: inline-block;
        border-bottom: 1px dotted #ccc;
        cursor: help;
    }
    
    /* Confidence badges */
    .conf-high { background: #1b5e20; color: white; padding: 4px 8px; border-radius: 4px; }
    .conf-med { background: #e65100; color: white; padding: 4px 8px; border-radius: 4px; }
    .conf-low { background: #616161; color: white; padding: 4px 8px; border-radius: 4px; }
    
    /* Feature impact bars */
    .impact-bar {
        background: linear-gradient(90deg, #4caf50 0%, #8bc34a 100%);
        height: 24px;
        border-radius: 4px;
        margin: 4px 0;
    }
    .impact-bar-neg {
        background: linear-gradient(90deg, #f44336 0%, #e57373 100%);
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🏒 NHL Prediction Dashboard")
st.markdown("### Machine Learning Model for NHL Game Outcomes")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Model Accuracy", "59.2%", "+6.1% vs baseline")
with col2:
    st.metric("Total Features", "141")
with col3:
    st.metric("Training Data", "3,690 games")

st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("📊 Navigation")
    page = st.radio(
        "Choose a view:",
        ["🏠 Overview", "🎯 Today's Predictions", "📈 Model Performance", "🔍 Feature Analysis", "❓ Help"],
        index=0
    )
    
    st.markdown("---")
    
    # Recent Performance Widget
    st.subheader("🔥 Recent Form")
    recent_perf = get_recent_model_performance()
    
    if recent_perf:
        accuracy_pct = recent_perf['accuracy'] * 100
        correct = recent_perf['correct']
        total = recent_perf['total']
        
        # Show as big number
        st.metric(
            f"Last {total} Games",
            f"{correct}/{total}",
            f"{accuracy_pct:.1f}% accuracy"
        )
        
        # Visual progress bar
        st.progress(recent_perf['accuracy'])
        
        # Status message
        if accuracy_pct >= 65:
            st.success("🔥 Hot streak!")
        elif accuracy_pct >= 55:
            st.info("📊 Solid performance")
        else:
            st.warning("📉 Below average")
    else:
        st.info("📊 Not enough games yet")
        st.caption("Need 10+ completed games in current season to track recent form")
    
    st.markdown("---")
    
    st.subheader("ℹ️ About")
    st.caption("**Model:** Logistic Regression")
    st.caption("**Data:** MoneyPuck + NHL API")
    st.caption("**Version:** 3.0 (Professional)")
    st.caption(f"**Updated:** {datetime.now().strftime('%B %d, %Y')}")
    
    st.markdown("---")
    
    # Quick Tips
    with st.expander("💡 Pro Tips"):
        st.write("**Confidence Levels:**")
        st.write("- ⚖️ <5% edge = Coin flip")
        st.write("- 📊 5-20% = Slight favorite")  
        st.write("- ✅ >20% = Strong pick")
        st.write("")
        st.write("**Best Betting:**")
        st.write("Focus on games with >20% confidence for better expected value")

# Load data
try:
    data = load_model_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# PAGE: OVERVIEW
if page == "🏠 Overview":
    st.header("Model Overview")
    
    # Quick Stats Banner
    quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)
    
    with quick_col1:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 20px; border-radius: 10px; text-align: center;'>
            <p style='margin:0; color: #ccc; font-size: 0.9em;'>Professional Range</p>
            <h2 style='margin:5px 0; color: white;'>55-60%</h2>
            <p style='margin:0; color: #4caf50; font-weight: bold;'>✓ We're at 59.2%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with quick_col2:
        recent_perf = get_recent_model_performance()
        if recent_perf:
            perf_text = f"{recent_perf['correct']}/{recent_perf['total']}"
            perf_pct = f"{recent_perf['accuracy']*100:.0f}%"
            perf_color = "#4caf50" if recent_perf['accuracy'] > 0.60 else "#ff9800"
        else:
            perf_text = "Tracking"
            perf_pct = "Soon"
            perf_color = "#9e9e9e"
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%); padding: 20px; border-radius: 10px; text-align: center;'>
            <p style='margin:0; color: #ccc; font-size: 0.9em;'>Recent Form</p>
            <h2 style='margin:5px 0; color: white;'>{perf_text}</h2>
            <p style='margin:0; color: {perf_color}; font-weight: bold;'>{perf_pct}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with quick_col3:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #e65100 0%, #ff6f00 100%); padding: 20px; border-radius: 10px; text-align: center;'>
            <p style='margin:0; color: #ccc; font-size: 0.9em;'>Total Features</p>
            <h2 style='margin:5px 0; color: white;'>141</h2>
            <p style='margin:0; color: #ffeb3b; font-weight: bold;'>Comprehensive</p>
        </div>
        """, unsafe_allow_html=True)
    
    with quick_col4:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #4a148c 0%, #6a1b9a 100%); padding: 20px; border-radius: 10px; text-align: center;'>
            <p style='margin:0; color: #ccc; font-size: 0.9em;'>Training Games</p>
            <h2 style='margin:5px 0; color: white;'>3,690</h2>
            <p style='margin:0; color: #ba68c8; font-weight: bold;'>2021-2024</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Load today's predictions for preview
    todays_preds = load_predictions_for_date(datetime.now())
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Test Accuracy",
            f"{data['test_metrics']['accuracy']:.1%}",
            f"+{(data['test_metrics']['accuracy'] - 0.531):.1%} vs baseline"
        )
    
    with col2:
        st.metric(
            "ROC-AUC",
            f"{data['test_metrics']['roc_auc']:.3f}"
        )
        with st.popover("ℹ️ What is ROC-AUC?"):
            st.write("**ROC-AUC (Area Under Curve)**")
            st.write("Measures the model's ability to distinguish between wins and losses.")
            st.write("- **0.5** = Random guessing")
            st.write("- **1.0** = Perfect predictions")
            st.write(f"- **0.624** = Good discrimination")
    
    with col3:
        st.metric(
            "Log Loss",
            f"{data['test_metrics']['log_loss']:.3f}"
        )
        with st.popover("ℹ️ What is Log Loss?"):
            st.write("**Logarithmic Loss**")
            st.write("Penalizes confident wrong predictions more heavily.")
            st.write("- **Lower is better**")
            st.write("- **0.0** = Perfect")
            st.write(f"- **0.675** = Well-calibrated probabilities")
    
    with col4:
        st.metric(
            "Brier Score",
            f"{data['test_metrics']['brier_score']:.3f}"
        )
        with st.popover("ℹ️ What is Brier Score?"):
            st.write("**Brier Score**")
            st.write("Mean squared error of predicted probabilities.")
            st.write("- **Lower is better**")
            st.write("- **0.0** = Perfect")
            st.write("- **0.25** = Random")
            st.write(f"- **0.241** = Reliable predictions")
    
    st.markdown("---")
    
    # Quick stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Model Performance")
        
        metrics_df = pd.DataFrame({
            'Metric': ['Accuracy', 'ROC-AUC', 'Log Loss', 'Brier Score'],
            'Train': [
                f"{data['train_metrics']['accuracy']:.1%}",
                f"{data['train_metrics']['roc_auc']:.3f}",
                f"{data['train_metrics']['log_loss']:.3f}",
                f"{data['train_metrics']['brier_score']:.3f}"
            ],
            'Test': [
                f"{data['test_metrics']['accuracy']:.1%}",
                f"{data['test_metrics']['roc_auc']:.3f}",
                f"{data['test_metrics']['log_loss']:.3f}",
                f"{data['test_metrics']['brier_score']:.3f}"
            ]
        })
        
        st.dataframe(metrics_df, use_container_width=True, hide_index=True)
        
        st.caption("**Baseline (home always wins):** 53.1%")
        st.caption("**Improvement:** +6.1 percentage points")
    
    with col2:
        st.subheader("🎯 Top 5 Features")
        
        # Feature explanations
        feature_explanations = {
            'elo_diff_pre': 'Elo rating difference (measures team strength)',
            'rolling_win_pct': 'Recent win percentage (last N games)',
            'rolling_goal_diff': 'Recent goal differential trend',
            'rolling_save_pct': 'Goaltending quality (save percentage)',
            'rolling_gsax': 'Goalie performance (goals saved above expected)',
            'rolling_xg': 'Expected goals trend (shot quality)',
            'rolling_corsi': 'Possession metric (shot attempts)',
            'rolling_fenwick': 'Possession metric (unblocked shots)',
            'momentum': 'Recent form vs season average',
            'rest_diff': 'Rest days advantage',
            'is_b2b': 'Back-to-back game indicator',
            'rolling_faceoff': 'Faceoff win percentage'
        }
        
        top_features = data['importance'].head(5)
        
        for idx, row in top_features.iterrows():
            feat_name = row['Feature']
            direction = "📈" if row['Coefficient'] > 0 else "📉"
            
            # Find explanation
            explanation = None
            for key, exp in feature_explanations.items():
                if key in feat_name.lower():
                    explanation = exp
                    break
            
            st.write(f"{direction} **{feat_name}**")
            st.caption(f"Coefficient: {row['Coefficient']:.4f}")
            if explanation:
                st.caption(f"💡 {explanation}")
    
    st.markdown("---")
    
    # Today's games preview
    st.subheader("🔮 Tonight's Games Preview")
    
    if todays_preds is not None and len(todays_preds) > 0:
        st.success(f"✅ {len(todays_preds)} games scheduled for tonight")
        
        # Show all games in a clean format
        for idx, game in todays_preds.iterrows():
            away = game.get('away_team', 'Away')
            home = game.get('home_team', 'Home')
            home_prob = game.get('home_win_prob', 0.5)
            away_prob = game.get('away_win_prob', 0.5)
            confidence = abs(home_prob - 0.5)
            predicted_winner = home if home_prob > 0.5 else away
            
            col1, col2, col3, col4 = st.columns([2, 1, 2, 2])
            
            with col1:
                st.markdown(f"**{away}**")
                st.caption(f"{away_prob:.0%}")
            
            with col2:
                st.markdown("@")
            
            with col3:
                st.markdown(f"**{home}**")
                st.caption(f"{home_prob:.0%}")
            
            with col4:
                if confidence < 0.05:
                    st.caption("⚖️ Toss-up")
                elif confidence > 0.2:
                    st.caption(f"✅ {predicted_winner}")
                else:
                    st.caption(f"📊 {predicted_winner}")
        
        st.info("📊 Click 'Today's Predictions' in sidebar for detailed analysis")
    else:
        st.warning("⚠️ No predictions for today")
        st.caption("Run: `python predict_full.py` to generate predictions")
    
    st.markdown("---")
    
    # Historical Accuracy Tracker
    st.subheader("📈 Historical Accuracy Tracker")
    
    with st.spinner("Loading historical performance..."):
        weekly_stats, games_df = get_historical_accuracy()
    
    if weekly_stats is not None and len(weekly_stats) > 0:
        # Summary stats
        total_correct = weekly_stats['correct'].sum()
        total_games = weekly_stats['total'].sum()
        overall_acc = total_correct / total_games if total_games > 0 else 0
        
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            st.metric("Overall Accuracy", f"{overall_acc:.1%}", f"{total_correct}/{total_games}")
        
        with metric_col2:
            recent_week = weekly_stats.iloc[-1]
            st.metric(
                "This Week",
                f"{recent_week['accuracy']:.1%}",
                f"{recent_week['correct']:.0f}/{recent_week['total']:.0f}"
            )
        
        with metric_col3:
            best_week = weekly_stats.loc[weekly_stats['accuracy'].idxmax()]
            st.metric("Best Week", f"{best_week['accuracy']:.1%}", best_week['week_label'])
        
        with metric_col4:
            # Trend (last 2 weeks)
            if len(weekly_stats) >= 2:
                last_two = weekly_stats.tail(2)
                trend = last_two.iloc[-1]['accuracy'] - last_two.iloc[-2]['accuracy']
                trend_emoji = "📈" if trend > 0 else "📉"
                st.metric("Trend", f"{trend_emoji} {abs(trend):.1%}", "vs last week")
            else:
                st.metric("Trend", "N/A", "Need 2+ weeks")
        
        # Accuracy over time chart
        st.markdown("#### Weekly Accuracy Trend")
        
        chart = alt.Chart(weekly_stats).mark_line(point=True, strokeWidth=3).encode(
            x=alt.X('week_label:N', title='Week Starting', sort=None),
            y=alt.Y('accuracy:Q', title='Accuracy', scale=alt.Scale(domain=[0.3, 0.8]), axis=alt.Axis(format='%')),
            tooltip=[
                alt.Tooltip('week_label:N', title='Week'),
                alt.Tooltip('accuracy:Q', title='Accuracy', format='.1%'),
                alt.Tooltip('correct:Q', title='Correct'),
                alt.Tooltip('total:Q', title='Total Games')
            ]
        ).properties(
            height=300
        )
        
        # Add baseline line
        baseline = alt.Chart(pd.DataFrame({'y': [0.531]})).mark_rule(
            strokeDash=[5, 5],
            color='red',
            size=2
        ).encode(y='y:Q')
        
        # Add target line
        target = alt.Chart(pd.DataFrame({'y': [0.592]})).mark_rule(
            strokeDash=[5, 5],
            color='green',
            size=2
        ).encode(y='y:Q')
        
        st.altair_chart(chart + baseline + target, use_container_width=True)
        
        st.caption("🔴 Red line = Baseline (53.1% - home always wins)")
        st.caption("🟢 Green line = Target (59.2% - test set performance)")
        
        # Performance insights
        with st.expander("📊 View Detailed Breakdown"):
            st.dataframe(
                weekly_stats[['week_label', 'correct', 'total', 'accuracy', 'avg_prob']].rename(columns={
                    'week_label': 'Week',
                    'correct': 'Correct',
                    'total': 'Total',
                    'accuracy': 'Accuracy',
                    'avg_prob': 'Avg Confidence'
                }).style.format({
                    'Accuracy': '{:.1%}',
                    'Avg Confidence': '{:.1%}'
                }),
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("📊 Not enough historical data yet")
        st.caption("Need at least 10 completed games in the current season to show historical accuracy.")

# PAGE: TODAY'S PREDICTIONS
elif page == "🎯 Today's Predictions":
    
    # Date navigation
    if 'selected_date' not in st.session_state:
        st.session_state.selected_date = datetime.now()
    
    col1, col2, col3, col4, col5 = st.columns([1, 1, 3, 1, 1])
    
    with col1:
        if st.button("⬅️ Previous Day"):
            from datetime import timedelta
            st.session_state.selected_date -= timedelta(days=1)
            st.rerun()
    
    with col2:
        if st.button("Today"):
            st.session_state.selected_date = datetime.now()
            st.rerun()
    
    with col3:
        st.markdown(f"### 🏒 {st.session_state.selected_date.strftime('%A, %B %d, %Y')}")
    
    with col4:
        if st.button("Next Day ➡️"):
            from datetime import timedelta
            st.session_state.selected_date += timedelta(days=1)
            st.rerun()
    
    with col5:
        # Quick date picker
        selected = st.date_input("", value=st.session_state.selected_date.date(), label_visibility="collapsed")
        if selected != st.session_state.selected_date.date():
            st.session_state.selected_date = datetime.combine(selected, datetime.min.time())
            st.rerun()
    
    st.markdown("---")
    
    # Load predictions and actual results for selected date
    selected_date = st.session_state.selected_date
    preds = load_predictions_for_date(selected_date)
    actual = get_actual_results(selected_date)
    is_past = selected_date.date() < datetime.now().date()
    is_today = selected_date.date() == datetime.now().date()
    is_future = selected_date.date() > datetime.now().date()
    
    # Add filters if we have predictions
    if preds is not None and len(preds) > 0:
        filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 1])
        
        with filter_col1:
            # Team filter
            all_teams = sorted(set(preds['away_team'].tolist() + preds['home_team'].tolist()))
            selected_teams = st.multiselect(
                "🔍 Filter by team",
                options=all_teams,
                placeholder="Select teams to filter..."
            )
        
        with filter_col2:
            # Confidence filter
            conf_filter = st.select_slider(
                "🎯 Min confidence level",
                options=["All Games", "Slight Edge (5%+)", "Moderate (10%+)", "Strong (20%+)"],
                value="All Games"
            )
        
        with filter_col3:
            # Sort option
            sort_by = st.selectbox(
                "📊 Sort by",
                ["Game Order", "Highest Confidence", "Lowest Confidence"]
            )
        
        # Apply filters
        filtered_preds = preds.copy()
        
        if selected_teams:
            filtered_preds = filtered_preds[
                filtered_preds['away_team'].isin(selected_teams) | 
                filtered_preds['home_team'].isin(selected_teams)
            ]
        
        if conf_filter == "Slight Edge (5%+)":
            filtered_preds = filtered_preds[filtered_preds['confidence'] >= 0.05]
        elif conf_filter == "Moderate (10%+)":
            filtered_preds = filtered_preds[filtered_preds['confidence'] >= 0.10]
        elif conf_filter == "Strong (20%+)":
            filtered_preds = filtered_preds[filtered_preds['confidence'] >= 0.20]
        
        if sort_by == "Highest Confidence":
            filtered_preds = filtered_preds.sort_values('confidence', ascending=False)
        elif sort_by == "Lowest Confidence":
            filtered_preds = filtered_preds.sort_values('confidence', ascending=True)
        
        # Update preds with filtered version
        preds = filtered_preds
        
        if len(preds) == 0:
            st.warning("No games match your filters")
            st.stop()
        
        st.markdown("---")
    
    # Display based on whether we have predictions and/or results
    if preds is not None and len(preds) > 0:
        # Show day type indicator
        if is_past:
            st.info(f"📅 Past Date - Showing predictions and actual results")
        elif is_today:
            st.success(f"✅ Today - {len(preds)} games scheduled")
            
            # Best Bets Section
            strong_picks = preds[preds['confidence'] > 0.2]
            if len(strong_picks) > 0:
                st.markdown("### 🎯 Best Bets (High Confidence)")
                
                bet_cols = st.columns(min(len(strong_picks), 3))
                for idx, (_, game) in enumerate(strong_picks.head(3).iterrows()):
                    with bet_cols[idx]:
                        winner = game['predicted_winner']
                        conf = game['confidence']
                        matchup = f"{game['away_team']} @ {game['home_team']}"
                        
                        st.markdown(f"""
                        <div style='background-color: #1e3a2e; padding: 15px; border-radius: 10px; border-left: 4px solid #2e7d32;'>
                            <h4 style='margin:0; color: #4caf50;'>{winner}</h4>
                            <p style='margin:5px 0; font-size:0.9em;'>{matchup}</p>
                            <p style='margin:0; font-weight:bold; font-size:1.1em;'>{conf:.0%} confidence</p>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info(f"🔮 Future Date - Showing predictions only")
        
        st.markdown("---")
        
        # Display each game
        for idx, pred_game in preds.iterrows():
            away = pred_game.get('away_team', 'Away')
            home = pred_game.get('home_team', 'Home')
            home_prob = pred_game.get('home_win_prob', 0.5)
            away_prob = pred_game.get('away_win_prob', 0.5)
            confidence = abs(home_prob - 0.5)
            predicted_winner = home if home_prob > 0.5 else away
            
            # Try to match with actual result if available
            actual_result = None
            if actual is not None:
                match = actual[(actual['away_team'] == away) & (actual['home_team'] == home)]
                if len(match) > 0:
                    actual_result = match.iloc[0]
            
            with st.container():
                # Game header with better styling
                st.markdown(f"### 🏒 Game {idx + 1}")
                
                # Main matchup display
                matchup_col1, matchup_col2, matchup_col3 = st.columns([4, 1, 4])
                
                with matchup_col1:
                    st.markdown(f"<h2 style='text-align: right;'>{away}</h2>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align: right; font-size: 1.5em; font-weight: bold; color: {'#4caf50' if away_prob > home_prob else '#ff9800'};'>{away_prob:.0%}</p>", unsafe_allow_html=True)
                    if actual_result is not None:
                        st.markdown(f"<p style='text-align: right; font-size: 1.2em;'>Final: {actual_result['away_score']}</p>", unsafe_allow_html=True)
                
                with matchup_col2:
                    st.markdown("<h3 style='text-align: center;'>@</h3>", unsafe_allow_html=True)
                
                with matchup_col3:
                    st.markdown(f"<h2 style='text-align: left;'>{home}</h2>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align: left; font-size: 1.5em; font-weight: bold; color: {'#4caf50' if home_prob > away_prob else '#ff9800'};'>{home_prob:.0%}</p>", unsafe_allow_html=True)
                    if actual_result is not None:
                        st.markdown(f"<p style='text-align: left; font-size: 1.2em;'>Final: {actual_result['home_score']}</p>", unsafe_allow_html=True)
                
                # Confidence meter
                st.markdown("**Confidence Level:**")
                confidence_color = "#4caf50" if confidence > 0.2 else "#ff9800" if confidence > 0.05 else "#9e9e9e"
                st.progress(confidence, text=f"{confidence:.0%} edge")
                
                # Show prediction with emoji and color
                if confidence < 0.05:
                    st.markdown(f"<div style='background-color: #424242; padding: 10px; border-radius: 5px; text-align: center;'>⚖️ <strong>TOSS-UP</strong> - Too close to call</div>", unsafe_allow_html=True)
                elif confidence > 0.2:
                    st.markdown(f"<div style='background-color: #1b5e20; padding: 10px; border-radius: 5px; text-align: center;'>✅ <strong>{predicted_winner}</strong> predicted to win (HIGH CONFIDENCE)</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='background-color: #e65100; padding: 10px; border-radius: 5px; text-align: center;'>📊 <strong>{predicted_winner}</strong> predicted to win (MODERATE)</div>", unsafe_allow_html=True)
                
                # 🔥 GAME DETAIL EXPANDER - Show WHY this prediction was made
                with st.expander("🔍 Why This Prediction? (Click to expand feature breakdown)"):
                    st.markdown("#### Model's Reasoning")
                    st.caption("This shows which features pushed the prediction toward each team")
                    
                    with st.spinner("Calculating feature contributions..."):
                        # Try to find this game in the dataset to show feature breakdown
                        try:
                            # Find matching game in dataset (this is simplified - in production you'd need better matching)
                            dataset_games = data['dataset'].games
                            model = data['model']
                            features = data['dataset'].features
                            feature_names = features.columns
                            
                            # For today's predictions, we can't show exact features since game hasn't been added to dataset yet
                            # But we can show the most important features and their typical impact
                            st.info("💡 Showing top predictive factors (exact game features require post-game data)")
                            
                            # Show top features and explain their general impact
                            top_features = data['importance'].head(10)
                            
                            st.markdown("**Top 10 Factors Influencing This Prediction:**")
                            
                            for idx, row in top_features.iterrows():
                                feat_name = row['Feature']
                                coef = row['Coefficient']
                                explanation = get_feature_explanation(feat_name)
                                
                                # Determine if feature helps home or away
                                helps_home = coef > 0
                                impact_direction = "→ Helps HOME team" if helps_home else "→ Helps AWAY team"
                                color = "#4caf50" if helps_home else "#f44336"
                                
                                # Create impact bar
                                bar_width = min(abs(coef) * 100, 100)
                                
                                st.markdown(f"""
                                <div style='margin: 8px 0; padding: 8px; background: #f5f5f5; border-radius: 4px;'>
                                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                                        <div style='flex: 1;'>
                                            <strong>{feat_name}</strong>
                                            <div style='font-size: 0.85em; color: #666;'>{explanation}</div>
                                        </div>
                                        <div style='text-align: right; min-width: 150px;'>
                                            <span style='color: {color}; font-weight: bold;'>{impact_direction}</span>
                                            <div style='font-size: 0.85em; color: #999;'>Coefficient: {coef:.3f}</div>
                                        </div>
                                    </div>
                                    <div style='background: #e0e0e0; height: 6px; border-radius: 3px; margin-top: 4px;'>
                                        <div style='background: {color}; height: 100%; width: {bar_width}%; border-radius: 3px;'></div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            st.markdown("---")
                            
                            # Explanation of how prediction works
                            st.markdown("**How It Works:**")
                            st.markdown(f"""
                            1. **Model evaluates {len(feature_names)} features** for this matchup
                            2. **Each feature contributes** based on its value × coefficient
                            3. **Positive features** push prediction toward home win
                            4. **Negative features** push prediction toward away win
                            5. **Final probability: {home_prob:.1%} home, {away_prob:.1%} away**
                            """)
                            
                            st.info(f"**Prediction: {predicted_winner}** (based on {confidence:.1%} edge over opponent)")
                            
                        except Exception as e:
                            st.error(f"Could not calculate feature breakdown: {e}")
                            st.caption("Feature analysis available for historical games only")
                
                # Show actual result if available
                if actual_result is not None:
                    actual_winner = home if actual_result['home_win'] == 1 else away
                    was_correct = (predicted_winner == actual_winner)
                    
                    st.markdown("**Actual Result:**")
                    if was_correct:
                        st.success(f"✅ **{actual_winner} WON** - Model was CORRECT!")
                    else:
                        st.error(f"❌ **{actual_winner} WON** - Model was incorrect")
                    
                    st.caption(f"Final Score: {away} {actual_result['away_score']} - {actual_result['home_score']} {home}")
                
                st.markdown("---")
        
        # Download button
        csv = preds.to_csv(index=False)
        st.download_button(
            "📥 Download Predictions CSV",
            csv,
            file_name=f"predictions_{selected_date.strftime('%Y-%m-%d')}.csv",
            mime="text/csv"
        )
    
    else:
        st.warning(f"⚠️ No predictions available for {selected_date.strftime('%B %d, %Y')}")
        
        if is_today:
            st.info("💡 Generate today's predictions by running:")
            st.code("python predict_full.py", language="bash")
            st.caption("This will analyze today's matchups and create predictions")
        elif is_future:
            future_date_str = selected_date.strftime('%Y-%m-%d')
            st.info(f"💡 Generate predictions for {selected_date.strftime('%B %d')} by running:")
            st.code(f"python predict_full.py {future_date_str}", language="bash")
            st.caption("This will create predictions for future games")
        else:
            # Past date - show actual results if available
            if actual is not None and len(actual) > 0:
                st.success(f"✅ Found {len(actual)} games on this date")
                st.markdown("### Actual Results")
                
                for idx, game in actual.iterrows():
                    away = game['away_team']
                    home = game['home_team']
                    winner = home if game['home_win'] == 1 else away
                    
                    st.markdown(f"""
                    **Game {idx + 1}:** {away} @ {home}  
                    **Final Score:** {away} {game['away_score']} - {game['home_score']} {home}  
                    **Winner:** {winner}
                    """)
                    st.markdown("---")
            else:
                st.info("This date is in the past. No games or predictions found.")

# PAGE: MODEL PERFORMANCE
elif page == "📈 Model Performance":
    st.header("Model Performance Analysis")
    
    # Metrics comparison
    st.subheader("📊 Train vs Test Metrics")
    
    metrics_comparison = pd.DataFrame({
        'Metric': ['Accuracy', 'ROC-AUC', 'Log Loss', 'Brier Score', 'Correct Predictions'],
        'Training Set': [
            f"{data['train_metrics']['accuracy']:.1%}",
            f"{data['train_metrics']['roc_auc']:.3f}",
            f"{data['train_metrics']['log_loss']:.3f}",
            f"{data['train_metrics']['brier_score']:.3f}",
            f"{int(data['train_metrics']['accuracy'] * data['train_mask'].sum())} / {data['train_mask'].sum()}"
        ],
        'Test Set (2024-25)': [
            f"{data['test_metrics']['accuracy']:.1%}",
            f"{data['test_metrics']['roc_auc']:.3f}",
            f"{data['test_metrics']['log_loss']:.3f}",
            f"{data['test_metrics']['brier_score']:.3f}",
            f"{int(data['test_metrics']['accuracy'] * data['test_mask'].sum())} / {data['test_mask'].sum()}"
        ]
    })
    
    st.dataframe(metrics_comparison, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Model comparison
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Accuracy Breakdown")
        
        baseline_acc = 0.531
        test_acc = data['test_metrics']['accuracy']
        improvement = test_acc - baseline_acc
        
        comparison_df = pd.DataFrame({
            'Model': ['Baseline (Home Wins)', 'Our Model', 'MoneyPuck (Pro)'],
            'Accuracy': [53.1, test_acc * 100, 62.0],
            'Range': ['Fixed', f'{test_acc*100:.1f}%', '60-64%']
        })
        
        chart = alt.Chart(comparison_df).mark_bar().encode(
            x=alt.X('Accuracy:Q', scale=alt.Scale(domain=[50, 65]), title='Accuracy (%)'),
            y=alt.Y('Model:N', sort='-x'),
            color=alt.Color('Model:N', legend=None),
            tooltip=['Model', 'Range']
        ).properties(height=200)
        
        st.altair_chart(chart, use_container_width=True)
        
        st.metric(
            "Improvement over Baseline",
            f"+{improvement:.1%}",
            f"+{int(improvement * data['test_mask'].sum())} correct predictions"
        )
    
    with col2:
        st.subheader("📈 Performance by Confidence")
        
        test_games = data['dataset'].games.loc[data['test_mask']].copy()
        test_games['predicted_prob'] = data['test_probs']
        test_games['confidence'] = abs(test_games['predicted_prob'] - 0.5)
        test_games['prediction_correct'] = (
            ((test_games['predicted_prob'] >= 0.5).astype(int)) == test_games['home_win']
        )
        
        # Bin by confidence
        test_games['confidence_bin'] = pd.cut(
            test_games['confidence'],
            bins=[0, 0.05, 0.1, 0.15, 0.2, 0.5],
            labels=['0-5%', '5-10%', '10-15%', '15-20%', '>20%']
        )
        
        conf_stats = test_games.groupby('confidence_bin', observed=True).agg({
            'prediction_correct': ['mean', 'count']
        }).reset_index()
        conf_stats.columns = ['Confidence', 'Accuracy', 'Count']
        conf_stats['Accuracy'] = conf_stats['Accuracy'] * 100
        
        st.dataframe(conf_stats, use_container_width=True, hide_index=True)
        
        st.caption("**Key Insight:** Higher confidence predictions are more accurate")

# PAGE: FEATURE ANALYSIS
elif page == "🔍 Feature Analysis":
    st.header("Feature Importance Analysis")
    
    st.subheader("Top 15 Most Important Features")
    
    importance_data = data['importance'].copy()
    importance_data['Impact'] = importance_data['Coefficient'].apply(
        lambda x: 'Positive (favors home)' if x > 0 else 'Negative (favors away)'
    )
    
    # Visualization
    chart = alt.Chart(importance_data).mark_bar().encode(
        y=alt.Y('Feature:N', sort='-x', title=''),
        x=alt.X('Coefficient:Q', title='Coefficient Value'),
        color=alt.Color(
            'Impact:N',
            scale=alt.Scale(domain=['Positive (favors home)', 'Negative (favors away)'],
                           range=['#2E7D32', '#C62828']),
            legend=alt.Legend(title='Impact Direction')
        ),
        tooltip=['Feature', alt.Tooltip('Coefficient:Q', format='.4f'), 'Impact']
    ).properties(height=500)
    
    st.altair_chart(chart, use_container_width=True)
    
    st.markdown("---")
    
    # Feature categories
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Feature Categories")
        
        # Categorize features
        categories = {
            'Goaltending': 0,
            'Expected Goals (xG)': 0,
            'Possession (Corsi/Fenwick)': 0,
            'Team Performance': 0,
            'Rest/Schedule': 0,
            'Other': 0
        }
        
        for feat in importance_data['Feature']:
            feat_lower = feat.lower()
            if 'save' in feat_lower or 'gsax' in feat_lower:
                categories['Goaltending'] += 1
            elif 'xg' in feat_lower:
                categories['Expected Goals (xG)'] += 1
            elif 'corsi' in feat_lower or 'fenwick' in feat_lower:
                categories['Possession (Corsi/Fenwick)'] += 1
            elif 'rest' in feat_lower or 'b2b' in feat_lower:
                categories['Rest/Schedule'] += 1
            elif 'win' in feat_lower or 'goal' in feat_lower:
                categories['Team Performance'] += 1
            else:
                categories['Other'] += 1
        
        cat_df = pd.DataFrame({
            'Category': list(categories.keys()),
            'Count': list(categories.values())
        })
        
        st.dataframe(cat_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("🎯 Feature Definitions")
        
        with st.expander("📊 Rolling Windows", expanded=True):
            st.write("**What are rolling windows?**")
            st.write("Statistics calculated from a team's last N games (3, 5, or 10 games)")
            st.write("- **rolling_win_pct_5**: Win rate in last 5 games")
            st.write("- **rolling_goal_diff_10**: Avg goal differential in last 10 games")
        
        with st.expander("🏒 Goaltending Metrics"):
            st.write("**Save Percentage (SV%)**")
            st.write("Percentage of shots saved by goaltender")
            st.write("")
            st.write("**Goals Saved Above Expected (GSAx)**")
            st.write("Actual goals allowed minus expected goals (based on shot quality)")
            st.write("- Positive = goalie performing above average")
            st.write("- Negative = goalie performing below average")
        
        with st.expander("⚡ Possession Metrics"):
            st.write("**Corsi**")
            st.write("All shot attempts (shots + blocks + misses)")
            st.write("")
            st.write("**Fenwick**")
            st.write("Unblocked shot attempts (shots + misses)")
            st.write("")
            st.write("Both measure puck possession and territorial dominance")
        
        with st.expander("🎯 Expected Goals (xG)"):
            st.write("**xGoals**")
            st.write("Expected number of goals based on shot quality")
            st.write("- Location on ice")
            st.write("- Shot type")
            st.write("- Game situation")
            st.write("")
            st.write("Better predictor than raw shot count")
        
        with st.expander("📈 Elo Rating"):
            st.write("**Elo Rating System**")
            st.write("Dynamic team strength rating (like chess)")
            st.write("- Updates after each game")
            st.write("- Accounts for opponent strength")
            st.write("- **elo_diff_pre** = rating difference before game")
    
    st.markdown("---")
    
    # Summary statistics
    st.subheader("📈 Feature Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Features", "141", "Including goaltending")
    
    with col2:
        # Count non-dummy features
        non_dummy = sum(1 for f in data['dataset'].features.columns 
                       if not any(x in f for x in ['home_team_', 'away_team_', 'rest_home_', 'rest_away_']))
        st.metric("Core Features", str(non_dummy), "Excluding team dummies")
    
    with col3:
        goalie_feats = sum(1 for f in data['dataset'].features.columns 
                          if 'save' in f.lower() or 'gsax' in f.lower())
        st.metric("Goalie Features", str(goalie_feats), "New in v2.0")

# PAGE: HELP
elif page == "❓ Help":
    st.header("📚 Dashboard User Guide")
    
    st.markdown("""
    Welcome to the NHL Prediction Dashboard! This guide will help you get the most out of all features.
    """)
    
    st.markdown("---")
    
    # Quick Start
    st.subheader("🚀 Quick Start")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **To see today's predictions:**
        1. Click "🎯 Today's Predictions" in sidebar
        2. Review the Best Bets section
        3. Scroll to see all games
        4. Download CSV if needed
        """)
    
    with col2:
        st.markdown("""
        **To check past performance:**
        1. Go to "🎯 Today's Predictions"
        2. Click ⬅️ Previous Day
        3. See predictions vs actual results
        4. Look for ✅ (correct) or ❌ (incorrect)
        """)
    
    st.markdown("---")
    
    # Features Guide
    st.subheader("✨ Feature Guide")
    
    with st.expander("🔥 Recent Form Tracker (Sidebar)", expanded=True):
        st.markdown("""
        **What it shows:**
        - Model's accuracy on last 20 games
        - Current performance: "12/20" = 12 correct out of 20
        - Visual progress bar
        - Status indicator (Hot streak / Solid / Below average)
        
        **Why it matters:**
        Shows if the model is performing well right now, not just historical test accuracy.
        
        **Updates:** Every hour automatically
        """)
    
    with st.expander("🎯 Best Bets Section"):
        st.markdown("""
        **What it shows:**
        - Only appears on today's predictions
        - Highlights games with >20% confidence
        - Shows up to 3 top picks
        - Green cards with team, matchup, confidence
        
        **How to use:**
        Focus on these games for higher expected value. The model is most confident about these outcomes.
        
        **Example:**
        "VGK vs FLA @ VGK - 29% confidence" means the model gives VGK a 65% chance (20% above coin flip).
        """)
    
    with st.expander("📊 Team Filter & Search"):
        st.markdown("""
        **Where:** Top of Today's Predictions page
        
        **How to use:**
        1. Click the multiselect dropdown
        2. Choose one or more teams
        3. Games are filtered instantly
        
        **Use cases:**
        - "Show me only Toronto games"
        - "Show me Bruins and Rangers"
        - "Find games with my favorite teams"
        """)
    
    with st.expander("🎯 Confidence Filter"):
        st.markdown("""
        **Where:** Next to team filter
        
        **Options:**
        - **All Games** - Show everything
        - **Slight Edge (5%+)** - Skip coin flips
        - **Moderate (10%+)** - Show decent confidence
        - **Strong (20%+)** - Only high confidence picks
        
        **Recommendation:**
        For betting analysis, focus on "Strong (20%+)" for better expected value.
        """)
    
    with st.expander("📈 Sort Options"):
        st.markdown("""
        **Where:** Right side of filter row
        
        **Options:**
        - **Game Order** - Default chronological
        - **Highest Confidence** - Best picks first
        - **Lowest Confidence** - Toss-ups first
        
        **Use case:**
        Sort by "Highest Confidence" to quickly see the model's strongest predictions.
        """)
    
    with st.expander("🎨 Confidence Meters"):
        st.markdown("""
        **What it shows:**
        Visual progress bar showing prediction strength
        
        **Colors:**
        - 🟢 **Green bar** - High confidence (20%+ edge)
        - 🟠 **Orange bar** - Moderate (5-20% edge)
        - ⚪ **Gray bar** - Toss-up (<5% edge)
        
        **Reading it:**
        - 30% confidence = 65% win probability (30% above 50/50)
        - 5% confidence = 55% win probability (just slight edge)
        """)
    
    with st.expander("ℹ️ Metric Tooltips"):
        st.markdown("""
        **Where:** Overview page, next to metrics
        
        **How to use:**
        Click the ℹ️ icon next to ROC-AUC, Log Loss, or Brier Score
        
        **What you'll learn:**
        - **ROC-AUC**: Model's ability to distinguish wins from losses
        - **Log Loss**: How well-calibrated the probabilities are
        - **Brier Score**: Mean squared error of predictions
        
        All explained in plain English!
        """)
    
    with st.expander("📅 Date Navigation"):
        st.markdown("""
        **Where:** Top of Today's Predictions page
        
        **Controls:**
        - ⬅️ **Previous Day** - Go back one day
        - **Today** button - Jump back to current date
        - ➡️ **Next Day** - Go forward one day
        - 📅 **Date picker** - Select any specific date
        
        **Features:**
        - **Past dates**: Shows predictions + actual results
        - **Today**: Shows predictions + best bets
        - **Future dates**: Shows predictions only
        """)
    
    st.markdown("---")
    
    # Understanding Predictions
    st.subheader("🎓 Understanding Predictions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Confidence Levels Explained:**
        
        - **<5% edge** = ⚖️ Coin flip
          - Example: 52% vs 48%
          - Action: Skip or avoid
        
        - **5-20% edge** = 📊 Slight favorite
          - Example: 60% vs 40%
          - Action: Moderate confidence
        
        - **>20% edge** = ✅ Strong pick
          - Example: 70% vs 30%
          - Action: High confidence
        """)
    
    with col2:
        st.markdown("""
        **What the Colors Mean:**
        
        - **🟢 Green** = Favorite, correct prediction
        - **🟠 Orange** = Underdog, moderate confidence
        - **⚪ Gray** = Neutral, toss-up
        - **🔴 Red** = Incorrect prediction (past games)
        
        **Emojis:**
        - ✅ = Model was correct
        - ❌ = Model was incorrect
        - 🔥 = Hot streak
        - 📊 = Solid performance
        """)
    
    st.markdown("---")
    
    # Tips & Best Practices
    st.subheader("💡 Tips & Best Practices")
    
    st.markdown("""
    **Daily Workflow:**
    1. Check "Recent Form" in sidebar (is model hot?)
    2. Go to "Today's Predictions"
    3. Review "Best Bets" section first
    4. Filter by confidence if needed
    5. Download CSV for your records
    
    **For Analysis:**
    1. Navigate to past dates
    2. Check model's correctness (✅/❌)
    3. Look for patterns in incorrect predictions
    4. Compare confidence to actual results
    
    **For Betting Research:**
    1. Focus on games with >20% confidence
    2. Check team's recent form (use filter)
    3. Compare to betting odds (external source)
    4. Track your own record vs model
    
    **Model Limitations:**
    - ⚠️ No model is perfect (59.2% is very good!)
    - ⚠️ Higher confidence ≠ guaranteed win
    - ⚠️ Injuries/lineup changes not real-time
    - ⚠️ Use as one input, not only factor
    """)
    
    st.markdown("---")
    
    # FAQ
    st.subheader("❓ Frequently Asked Questions")
    
    with st.expander("How accurate is the model?"):
        st.markdown("""
        **Test Set Accuracy:** 59.2%
        
        This means the model correctly predicts the winner 59.2% of the time on games it hasn't seen before.
        
        **Context:**
        - Random guessing: 50%
        - Home team always wins: 53.1%
        - Professional models: 55-60%
        - **Our model: 59.2%** ✅
        
        The model is performing at a professional level!
        """)
    
    with st.expander("What data does the model use?"):
        st.markdown("""
        **Data Sources:**
        - MoneyPuck (advanced metrics)
        - NHL API (schedules, scores)
        
        **Features (141 total):**
        - Team strength (Elo ratings)
        - Recent form (rolling win %, goal differential)
        - Goaltending quality (SV%, GSAx)
        - Shot quality (Expected Goals)
        - Possession (Corsi, Fenwick)
        - Schedule factors (rest days, back-to-backs)
        
        **Training Data:**
        - 3,690 games from 2021-2024 seasons
        - Excludes 2020 COVID season
        """)
    
    with st.expander("How often is data updated?"):
        st.markdown("""
        **Automatically:**
        - MoneyPuck data: Updates nightly
        - NHL API: Real-time game results
        
        **To get fresh predictions:**
        ```bash
        python predict_full.py
        ```
        
        **Dashboard refresh:**
        - Cached for 10 minutes (predictions)
        - Cached for 1 hour (model data)
        - Force refresh: Reload page
        """)
    
    with st.expander("Can I use this for betting?"):
        st.markdown("""
        **Short answer:** The model is designed for analysis, not gambling advice.
        
        **If you choose to use for betting research:**
        - ✅ Focus on high confidence games (>20%)
        - ✅ Compare to betting odds
        - ✅ Look for value (model higher than odds)
        - ✅ Track your record
        - ⚠️ Never bet more than you can afford to lose
        - ⚠️ Use as ONE input, not the only factor
        
        **Recommended:** Research Kelly Criterion for bet sizing if you pursue this.
        """)
    
    with st.expander("What does 'confidence' mean?"):
        st.markdown("""
        **Confidence** = How far from 50/50 the prediction is
        
        **Examples:**
        - 50% vs 50% = 0% confidence (coin flip)
        - 55% vs 45% = 5% confidence (slight edge)
        - 60% vs 40% = 10% confidence (moderate)
        - 70% vs 30% = 20% confidence (strong)
        
        **Why it matters:**
        Higher confidence predictions have higher expected value. The model is more certain about the outcome.
        """)
    
    st.markdown("---")
    
    # Contact & Support
    st.subheader("📞 Need Help?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **📖 Read the Docs**
        - Check README.md
        - Review DASHBOARD_README.md
        - See group_report_2.md
        """)
    
    with col2:
        st.markdown("""
        **💻 Technical Issues**
        - Check terminal for errors
        - Verify predictions file exists
        - Try: `python predict_full.py`
        """)
    
    with col3:
        st.markdown("""
        **🎯 Best Practices**
        - Use filters to narrow down
        - Check recent form first
        - Focus on high confidence
        - Track model accuracy
        """)


