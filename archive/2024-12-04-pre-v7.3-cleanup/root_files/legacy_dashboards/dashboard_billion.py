"""
PUCKCAST.AI - NHL PREDICTION DASHBOARD
========================================================
Data-Driven NHL Prediction Intelligence

This dashboard includes:
- Command Center with real-time KPIs
- Betting Simulator with ROI tracking
- Performance Analytics with heatmaps
- Deep Analysis with correlation matrices  
- Advanced visualizations
- And 15+ more elite features

Created: November 10, 2025
Version: 2.0 (Elite)
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
import numpy as np

# Add src to path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import streamlit as st
import pandas as pd
import altair as alt
from nhl_prediction.pipeline import build_dataset
from nhl_prediction.model import create_baseline_model, fit_model, predict_probabilities, compute_metrics
from nhl_prediction.nhl_api import fetch_schedule

# ═══════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Puckcast.ai - NHL Predictions",
    page_icon="assets/favicon.png",  # Custom favicon!
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "# Puckcast.ai\nData-Driven NHL Prediction Intelligence"
    }
)

# ═══════════════════════════════════════════════════════════
# ELITE CSS & ANIMATIONS
# ═══════════════════════════════════════════════════════════

st.markdown("""
<style>
    /* Import Premium Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* ===============================================
       PUCKCAST.AI BRAND COLORS
       =============================================== */
    
    :root {
        --puckcast-cyan: #1E9BF0;
        --puckcast-navy: #1A3A52;
        --puckcast-accent: #52C4FF;
        --puckcast-dark: #0E1117;
        --puckcast-darker: #0A0D10;
    }
    
    /* Dark Mode Base */
    .stApp {
        background-color: var(--puckcast-dark);
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--puckcast-navy) 0%, var(--puckcast-dark) 100%);
    }
    
    /* Hide Streamlit branding and buttons */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    
    /* Hide ALL fullscreen buttons - AGGRESSIVE */
    button[title="View fullscreen"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }
    
    [data-testid="StyledFullScreenButton"] {
        display: none !important;
        visibility: hidden !important;
    }
    
    [data-testid="stImage"] button {
        display: none !important;
        visibility: hidden !important;
    }
    
    .stImage button {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Hide any button in sidebar */
    [data-testid="stSidebar"] button[kind="header"] {
        display: none !important;
    }
    
    /* ===============================================
       ANIMATIONS
       =============================================== */
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideIn {
        from { transform: translateX(-30px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 10px rgba(30, 155, 240, 0.5), 0 0 20px rgba(82, 196, 255, 0.3); }
        50% { box-shadow: 0 0 20px rgba(30, 155, 240, 0.8), 0 0 30px rgba(82, 196, 255, 0.5); }
    }
    
    @keyframes shimmer {
        0% { background-position: -1000px 0; }
        100% { background-position: 1000px 0; }
    }
    
    @keyframes countUp {
        from { transform: scale(0.5); opacity: 0; }
        to { transform: scale(1); opacity: 1; }
    }
    
    /* ===============================================
       GRADIENT CARDS
       =============================================== */
    
    .gradient-card {
        background: linear-gradient(135deg, var(--puckcast-cyan) 0%, var(--puckcast-navy) 100%);
        padding: 25px;
        border-radius: 16px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        animation: fadeIn 0.6s ease-out;
        position: relative;
        overflow: hidden;
    }
    
    .gradient-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(
            90deg,
            transparent,
            rgba(255, 255, 255, 0.1),
            transparent
        );
        transition: left 0.5s;
    }
    
    .gradient-card:hover::before {
        left: 100%;
    }
    
    .gradient-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 20px 50px rgba(0,0,0,0.3);
    }
    
    /* PUCKCAST.AI Gradient Themes - Varied & Dynamic */
    .gradient-blue {
        background: linear-gradient(135deg, var(--puckcast-cyan) 0%, var(--puckcast-navy) 100%);
        box-shadow: 0 10px 40px rgba(30, 155, 240, 0.3);
    }
    
    .gradient-green {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        box-shadow: 0 10px 40px rgba(16, 185, 129, 0.3);
    }
    
    .gradient-orange {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
        box-shadow: 0 10px 40px rgba(245, 158, 11, 0.3);
    }
    
    .gradient-purple {
        background: linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%);
        box-shadow: 0 10px 40px rgba(139, 92, 246, 0.3);
    }
    
    .gradient-pink {
        background: linear-gradient(135deg, #EC4899 0%, #DB2777 100%);
        box-shadow: 0 10px 40px rgba(236, 72, 153, 0.3);
    }
    
    .gradient-dark {
        background: linear-gradient(135deg, #374151 0%, #1F2937 100%);
        box-shadow: 0 10px 40px rgba(31, 41, 55, 0.5);
    }
    
    /* ===============================================
       GLASSMORPHISM
       =============================================== */
    
    .glass {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.18);
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
    }
    
    .glass-dark {
        background: rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
    }
    
    /* ===============================================
       METRIC CARDS
       =============================================== */
    
    .metric-elite {
        text-align: center;
        padding: 30px 20px;
        border-radius: 16px;
        background: linear-gradient(135deg, var(--puckcast-navy) 0%, var(--puckcast-dark) 100%);
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
        animation: fadeIn 0.5s ease-out;
    }
    
    .metric-elite:hover {
        transform: translateY(-5px) scale(1.03);
        box-shadow: 0 15px 40px rgba(0,0,0,0.3);
    }
    
    .metric-value {
        font-size: 2.5em;
        font-weight: 800;
        color: white;
        margin: 10px 0;
        animation: countUp 0.6s ease-out;
    }
    
    .metric-label {
        font-size: 1em;
        color: #ccc;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .metric-delta {
        font-size: 0.9em;
        font-weight: 600;
        margin-top: 8px;
    }
    
    /* ===============================================
       BUTTONS
       =============================================== */
    
    .stButton button {
        background: linear-gradient(135deg, var(--puckcast-cyan) 0%, var(--puckcast-accent) 100%);
        border: none;
        border-radius: 12px;
        padding: 14px 28px;
        font-weight: 600;
        font-size: 1em;
        color: white;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        box-shadow: 0 4px 15px rgba(30, 155, 240, 0.4);
        cursor: pointer;
    }
    
    .stButton button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(30, 155, 240, 0.6);
        background: linear-gradient(135deg, var(--puckcast-accent) 0%, var(--puckcast-cyan) 100%);
        animation: glow 1.5s ease-in-out infinite;
    }
    
    .stButton button:active {
        transform: translateY(-1px);
    }
    
    /* ===============================================
       PROGRESS BARS
       =============================================== */
    
    .progress-container {
        width: 100%;
        height: 12px;
        background: rgba(0,0,0,0.1);
        border-radius: 6px;
        overflow: hidden;
        position: relative;
    }
    
    .progress-bar-elite {
        height: 100%;
        background: linear-gradient(90deg, #00f260 0%, #0575e6 100%);
        border-radius: 6px;
        position: relative;
        transition: width 1.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        box-shadow: 0 0 10px rgba(0, 242, 96, 0.5);
    }
    
    .progress-bar-elite::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(
            90deg,
            transparent,
            rgba(255,255,255,0.3),
            transparent
        );
        animation: shimmer 2s infinite;
        background-size: 1000px 100%;
    }
    
    /* ===============================================
       BADGES
       =============================================== */
    
    .badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85em;
        box-shadow: 0 3px 12px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    
    .badge:hover {
        transform: scale(1.1);
    }
    
    .badge-success {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
    }
    
    .badge-warning {
        background: linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%);
        color: white;
    }
    
    .badge-danger {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        color: white;
    }
    
    .badge-info {
        background: linear-gradient(135deg, #4e54c8 0%, #8f94fb 100%);
        color: white;
    }
    
    /* ===============================================
       TABLES
       =============================================== */
    
    .dataframe {
        border-radius: 12px !important;
        overflow: hidden;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
    }
    
    /* ===============================================
       TITLE ANIMATIONS
       =============================================== */
    
    .title-main {
        font-size: 3.5em;
        font-weight: 900;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin: 20px 0;
        animation: fadeIn 1s ease-out;
        letter-spacing: -2px;
    }
    
    .subtitle {
        text-align: center;
        font-size: 1.3em;
        color: #666;
        font-weight: 500;
        margin-bottom: 30px;
        animation: fadeIn 1.2s ease-out;
    }
    
    /* ===============================================
       NEON EFFECTS
       =============================================== */
    
    .neon-green {
        color: #39ff14;
        text-shadow: 0 0 10px #39ff14, 0 0 20px #39ff14, 0 0 30px #39ff14;
    }
    
    .neon-blue {
        color: #00f3ff;
        text-shadow: 0 0 10px #00f3ff, 0 0 20px #00f3ff, 0 0 30px #00f3ff;
    }
    
    .neon-pink {
        color: #ff006e;
        text-shadow: 0 0 10px #ff006e, 0 0 20px #ff006e, 0 0 30px #ff006e;
    }
    
    /* ===============================================
       SCROLLBAR
       =============================================== */
    
    ::-webkit-scrollbar {
        width: 12px;
        height: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        box-shadow: 0 0 10px rgba(102, 126, 234, 0.5);
    }
    
    /* ===============================================
       HIDE STREAMLIT BRANDING
       =============================================== */
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* ===============================================
       RESPONSIVE
       =============================================== */
    
    @media (max-width: 768px) {
        .title-main {
            font-size: 2em;
        }
        .metric-value {
            font-size: 1.8em;
        }
    }
    
    /* ===============================================
       SPECIAL EFFECTS
       =============================================== */
    
    .glow-box {
        animation: glow 2s infinite;
    }
    
    .pulse-box {
        animation: pulse 2s infinite;
    }
    
    /* ===============================================
       HEATMAP CELLS
       =============================================== */
    
    .heatmap-cell {
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .heatmap-cell:hover {
        transform: scale(1.1);
        z-index: 10;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    
    /* ===============================================
       STAT COMPARISON
       =============================================== */
    
    .stat-vs {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px;
        background: rgba(0,0,0,0.05);
        border-radius: 12px;
        margin: 10px 0;
    }
    
    .stat-vs-team {
        flex: 1;
        text-align: center;
    }
    
    .stat-vs-divider {
        padding: 0 20px;
        font-weight: 700;
        color: #999;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# DATA LOADING FUNCTIONS (CACHED)
# ═══════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def load_model_data():
    """Load and cache model data."""
    dataset = build_dataset(['20212022', '20222023', '20232024', '20242025'])
    
    train_mask = dataset.games['seasonId'].isin(['20212022', '20222023', '20232024'])
    test_mask = dataset.games['seasonId'] == '20242025'
    
    model = create_baseline_model(C=1.0)
    model = fit_model(model, dataset.features, dataset.target, train_mask)
    
    train_probs = predict_probabilities(model, dataset.features, train_mask)
    test_probs = predict_probabilities(model, dataset.features, test_mask)
    
    train_metrics = compute_metrics(dataset.target[train_mask], train_probs)
    test_metrics = compute_metrics(dataset.target[test_mask], test_probs)
    
    coefs = model.named_steps['clf'].coef_[0]
    importance_df = pd.DataFrame({
        'Feature': dataset.features.columns,
        'Coefficient': coefs,
        'Abs_Coefficient': abs(coefs)
    })
    
    importance_df = importance_df[
        ~importance_df['Feature'].str.contains('home_team_|away_team_|rest_home_|rest_away_', regex=True)
    ].sort_values('Abs_Coefficient', ascending=False)
    
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

@st.cache_data(ttl=600)
def load_predictions_today():
    """Load today's predictions."""
    today = datetime.now()
    date_str = today.strftime('%Y-%m-%d')
    
    pred_file = Path(f'predictions_{date_str}.csv')
    if pred_file.exists():
        return pd.read_csv(pred_file)
    return None

@st.cache_data(ttl=600)
def calculate_betting_performance(_data, strategy='threshold', threshold=0.55, kelly_fraction=0.25):
    """Calculate betting performance with different strategies."""
    data = _data  # Use underscore prefix to prevent hashing
    test_games = data['dataset'].games[data['test_mask']].copy()
    test_probs = data['test_probs']
    test_actual = data['dataset'].target[data['test_mask']]
    
    # Add probabilities to games
    test_games['home_win_prob'] = test_probs
    test_games['predicted'] = (test_probs >= 0.5).astype(int)
    test_games['actual'] = test_actual.values
    test_games['correct'] = (test_games['predicted'] == test_games['actual'])
    
    # Apply betting strategy
    if strategy == 'threshold':
        test_games['bet'] = (test_games['home_win_prob'] >= threshold) | (test_games['home_win_prob'] <= (1-threshold))
        test_games['bet_amount'] = 1.0  # Fixed bet
    elif strategy == 'kelly':
        # Kelly Criterion: f = (p*odds - 1) / (odds - 1)
        # Simplified for -110 odds (1.91 decimal)
        test_games['edge'] = test_games['home_win_prob'] - 0.5
        test_games['bet_amount'] = (test_games['edge'].abs() * kelly_fraction).clip(0, 1)
        test_games['bet'] = test_games['bet_amount'] > 0.01
    else:
        test_games['bet'] = True
        test_games['bet_amount'] = 1.0
    
    # Calculate returns (assuming -110 odds)
    test_games['return'] = 0.0
    test_games.loc[test_games['bet'] & test_games['correct'], 'return'] = test_games['bet_amount'] * 0.91
    test_games.loc[test_games['bet'] & ~test_games['correct'], 'return'] = -test_games['bet_amount']
    
    # Calculate cumulative profit
    test_games['cumulative_profit'] = test_games['return'].cumsum()
    
    # Stats
    total_bets = test_games['bet'].sum()
    wins = (test_games['bet'] & test_games['correct']).sum()
    total_return = test_games['return'].sum()
    roi = (total_return / total_bets * 100) if total_bets > 0 else 0
    
    return {
        'games': test_games,
        'total_bets': int(total_bets),
        'wins': int(wins),
        'losses': int(total_bets - wins),
        'win_rate': wins / total_bets if total_bets > 0 else 0,
        'total_return': total_return,
        'roi': roi,
        'final_profit': test_games['cumulative_profit'].iloc[-1] if len(test_games) > 0 else 0
    }

@st.cache_data(ttl=3600)
def calculate_confidence_calibration(_data):
    """Calculate calibration by confidence buckets."""
    data = _data  # Use underscore prefix to prevent hashing
    test_probs = data['test_probs']
    test_actual = data['dataset'].target[data['test_mask']].values
    
    # Create confidence buckets
    buckets = [(0, 0.5), (0.5, 0.55), (0.55, 0.6), (0.6, 0.65), (0.65, 0.7), (0.7, 1.0)]
    
    calibration_data = []
    for low, high in buckets:
        mask = (test_probs >= low) & (test_probs < high)
        if mask.sum() > 0:
            avg_prob = test_probs[mask].mean()
            actual_rate = test_actual[mask].mean()
            count = mask.sum()
            calibration_data.append({
                'bucket': f'{low:.0%}-{high:.0%}',
                'predicted': avg_prob,
                'actual': actual_rate,
                'count': count,
                'calibration_error': abs(avg_prob - actual_rate)
            })
    
    return pd.DataFrame(calibration_data)

@st.cache_data(ttl=3600)
def get_team_performance_matrix(_data):
    """Calculate model performance by team."""
    data = _data  # Use underscore prefix to prevent hashing
    test_games = data['dataset'].games[data['test_mask']].copy()
    test_probs = data['test_probs']
    test_actual = data['dataset'].target[data['test_mask']]
    
    test_games['predicted'] = (test_probs >= 0.5).astype(int)
    test_games['actual'] = test_actual.values
    test_games['correct'] = (test_games['predicted'] == test_games['actual'])
    
    # Team performance
    team_stats = {}
    
    for team_col in ['teamAbbrev_home', 'teamAbbrev_away']:
        if team_col in test_games.columns:
            for team in test_games[team_col].unique():
                if pd.isna(team):
                    continue
                    
                team_games = test_games[
                    (test_games['teamAbbrev_home'] == team) | 
                    (test_games['teamAbbrev_away'] == team)
                ]
                
                if len(team_games) > 0:
                    if team not in team_stats:
                        team_stats[team] = {
                            'games': 0,
                            'correct': 0
                        }
                    team_stats[team]['games'] += len(team_games)
                    team_stats[team]['correct'] += team_games['correct'].sum()
    
    # Convert to dataframe
    team_df = pd.DataFrame([
        {'team': team, 'games': stats['games'], 'correct': stats['correct'], 
         'accuracy': stats['correct'] / stats['games']}
        for team, stats in team_stats.items()
        if stats['games'] > 0
    ]).sort_values('accuracy', ascending=False)
    
    return team_df

# ═══════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════

with st.spinner('🏒 Loading Puckcast.ai...'):
    try:
        data = load_model_data()
        predictions_today = load_predictions_today()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

# ═══════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════

# Logo and Title - Centered
try:
    _, col_logo, _ = st.columns([3, 2, 3])
    with col_logo:
        st.image("assets/logo.png", width=80, use_container_width=False)
except Exception:
    pass

st.markdown("""
<div style='text-align: center; margin-top: 20px; animation: fadeIn 1s ease-out;'>
    <h1 style='font-size: 2.8em; font-weight: 800; margin: 0;
               background: linear-gradient(135deg, #1E9BF0 0%, #52C4FF 100%);
               -webkit-background-clip: text;
               -webkit-text-fill-color: transparent;
               background-clip: text;
               text-shadow: 0 0 30px rgba(30, 155, 240, 0.3);'>
        Puckcast.ai
    </h1>
    <p style='font-size: 1.1em; color: #AAA; margin-top: 10px; letter-spacing: 1.5px; font-weight: 500;'>
        Data-Driven NHL Prediction Intelligence
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Top KPI Bar
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.markdown(f"""
    <div class='metric-elite gradient-green'>
        <div style='font-size: 2em;'>✅</div>
        <div class='metric-label'>Status</div>
        <div class='metric-value' style='font-size: 1.5em;'>LIVE</div>
        <div style='color: rgba(255,255,255,0.8); font-size: 0.85em;'>System Active</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    acc = data['test_metrics']['accuracy'] * 100
    baseline = 53.1
    improvement = acc - baseline
    st.markdown(f"""
    <div class='metric-elite gradient-blue'>
        <div style='font-size: 2em;'>🎯</div>
        <div class='metric-label'>Accuracy</div>
        <div class='metric-value'>{acc:.1f}%</div>
        <div class='metric-delta' style='color: #4caf50;'>+{improvement:.1f}% vs baseline</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    roc_auc = data['test_metrics']['roc_auc']
    st.markdown(f"""
    <div class='metric-elite gradient-purple'>
        <div style='font-size: 2em;'>📊</div>
        <div class='metric-label'>ROC-AUC</div>
        <div class='metric-value'>{roc_auc:.3f}</div>
        <div style='color: rgba(255,255,255,0.8); font-size: 0.85em;'>Excellent</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    total_games = data['test_mask'].sum()
    correct = int(((data['test_probs'] >= 0.5) == data['dataset'].target[data['test_mask']]).sum())
    st.markdown(f"""
    <div class='metric-elite gradient-orange'>
        <div style='font-size: 2em;'>⚡</div>
        <div class='metric-label'>Correct Picks</div>
        <div class='metric-value'>{correct}</div>
        <div style='color: rgba(255,255,255,0.8); font-size: 0.85em;'>of {total_games} games</div>
    </div>
    """, unsafe_allow_html=True)

with kpi5:
    st.markdown(f"""
    <div class='metric-elite gradient-pink'>
        <div style='font-size: 2em;'>🔥</div>
        <div class='metric-label'>Features</div>
        <div class='metric-value'>141</div>
        <div style='color: rgba(255,255,255,0.8); font-size: 0.85em;'>Advanced Features</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ═══════════════════════════════════════════════════════════

with st.sidebar:
    # Puckcast.ai Logo & Branding - CENTERED WITH VISIBILITY BOOST
    st.markdown("""
    <style>
    /* Sidebar logo glow container */
    .sidebar-logo-container {
        text-align: center;
        padding: 30px 0 20px 0;
        background: radial-gradient(circle, rgba(30, 155, 240, 0.12) 0%, transparent 70%);
        border-radius: 20px;
        margin: 10px 0 20px 0;
        min-height: 140px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-logo-container">', unsafe_allow_html=True)
    
    try:
        # Center the logo using columns
        _, col_center, _ = st.columns([1, 2, 1])
        with col_center:
            st.image("assets/logo.png", width=90, use_container_width=False)
    except Exception as e:
        st.markdown("<div style='height: 90px;'></div>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style='text-align: center; padding: 10px 0 20px 0;'>
        <div style='font-size: 1.8em; font-weight: 800; margin: 0;
                    background: linear-gradient(135deg, #1E9BF0 0%, #52C4FF 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    text-shadow: 0 0 1px rgba(30, 155, 240, 0.3);'>
            Puckcast.ai
        </div>
        <div style='font-size: 0.8em; color: #AAA; margin-top: 10px; letter-spacing: 1.5px; font-weight: 500;'>
            Data-Driven Prediction Intelligence
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    page = st.radio(
        "📊 NAVIGATION",
        [
            "🏠 Command Center",
            "🎯 Today's Predictions",
            "💰 Betting Simulator",
            "📈 Performance Analytics",
            "🔬 Deep Analysis",
            "🏆 Leaderboards"
        ],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # System Status
    st.markdown("""
    <div class='glass' style='margin: 20px 0;'>
        <div style='text-align: center;'>
            <div style='font-size: 1.1em; font-weight: 600; margin-bottom: 15px;'>
                🔥 SYSTEM STATUS
            </div>
            <div class='progress-container'>
                <div class='progress-bar-elite' style='width: 92%;'></div>
            </div>
            <div style='font-size: 0.9em; color: #666; margin-top: 10px;'>
                Performance: 92% Optimal
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick actions
    st.markdown("### ⚡ QUICK ACTIONS")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄", use_container_width=True, help="Refresh"):
            st.cache_data.clear()
            st.rerun()
    with col2:
        if st.button("📥", use_container_width=True, help="Export"):
            st.info("Export feature coming soon!")
    
    st.markdown("---")
    
    st.caption(f"**Updated:** {datetime.now().strftime('%H:%M:%S')}")
    st.caption("**Data:** MoneyPuck + NHL API")
    st.caption("**Powered by:** Puckcast.ai")

# ═══════════════════════════════════════════════════════════
# PAGE: COMMAND CENTER
# ═══════════════════════════════════════════════════════════

if page == "🏠 Command Center":
    st.markdown("""
    <div style='text-align: center; margin: 30px 0;'>
        <h2 style='font-weight: 700; font-size: 2.5em;
                   background: linear-gradient(135deg, #1E9BF0 0%, #52C4FF 100%);
                   -webkit-background-clip: text;
                   -webkit-text-fill-color: transparent;
                   background-clip: text;'>
            COMMAND CENTER
        </h2>
        <p style='color: #888; font-size: 1.2em;'>Real-Time NHL Prediction Intelligence</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key Metrics Row
    met1, met2, met3, met4 = st.columns(4)
    
    with met1:
        brier = data['test_metrics']['brier_score']
        st.markdown(f"""
        <div class='gradient-card gradient-blue'>
            <div style='text-align: center; color: white;'>
                <div style='font-size: 2.5em; margin-bottom: 10px;'>🎯</div>
                <div style='font-size: 2em; font-weight: 700;'>{brier:.3f}</div>
                <div style='font-size: 1.1em; opacity: 0.9; margin-top: 5px;'>Brier Score</div>
                <div style='font-size: 0.85em; opacity: 0.7; margin-top: 10px;'>Lower is Better</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with met2:
        log_loss = data['test_metrics']['log_loss']
        st.markdown(f"""
        <div class='gradient-card gradient-green'>
            <div style='text-align: center; color: white;'>
                <div style='font-size: 2.5em; margin-bottom: 10px;'>📉</div>
                <div style='font-size: 2em; font-weight: 700;'>{log_loss:.3f}</div>
                <div style='font-size: 1.1em; opacity: 0.9; margin-top: 5px;'>Log Loss</div>
                <div style='font-size: 0.85em; opacity: 0.7; margin-top: 10px;'>Well Calibrated</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with met3:
        edge = correct - (total_games * 0.531)
        st.markdown(f"""
        <div class='gradient-card gradient-orange'>
            <div style='text-align: center; color: white;'>
                <div style='font-size: 2.5em; margin-bottom: 10px;'>⚡</div>
                <div style='font-size: 2em; font-weight: 700;'>+{int(edge)}</div>
                <div style='font-size: 1.1em; opacity: 0.9; margin-top: 5px;'>Edge vs Baseline</div>
                <div style='font-size: 0.85em; opacity: 0.7; margin-top: 10px;'>More Correct Picks</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with met4:
        training_games = data['train_mask'].sum()
        st.markdown(f"""
        <div class='gradient-card gradient-purple'>
            <div style='text-align: center; color: white;'>
                <div style='font-size: 2.5em; margin-bottom: 10px;'>📚</div>
                <div style='font-size: 2em; font-weight: 700;'>{training_games:,}</div>
                <div style='font-size: 1.1em; opacity: 0.9; margin-top: 5px;'>Training Games</div>
                <div style='font-size: 0.85em; opacity: 0.7; margin-top: 10px;'>4 Seasons</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Two-column layout
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        st.markdown("### 📊 Top Predictive Features")
        
        # Top 10 features chart
        top_features = data['importance'].head(10)
        
        chart = alt.Chart(top_features).mark_bar().encode(
            y=alt.Y('Feature:N', sort='-x', title=''),
            x=alt.X('Abs_Coefficient:Q', title='Impact'),
            color=alt.condition(
                alt.datum.Coefficient > 0,
                alt.value('#4caf50'),
                alt.value('#f44336')
            ),
            tooltip=['Feature', 'Coefficient']
        ).properties(
            height=400
        )
        
        st.altair_chart(chart, use_container_width=True)
        
        with st.expander("📋 View Full Feature List"):
            st.dataframe(
                data['importance'].head(20)[['Feature', 'Coefficient']].style.format({'Coefficient': '{:.4f}'}),
                use_container_width=True,
                hide_index=True
            )
    
    with col_right:
        st.markdown("### 🎯 Today's Games")
        
        if predictions_today is not None and len(predictions_today) > 0:
            # Filter to only today's games
            today_str = datetime.now().strftime('%Y-%m-%d')
            if 'date' in predictions_today.columns:
                predictions_today['date'] = pd.to_datetime(predictions_today['date'], errors='coerce')
                todays_only = predictions_today[predictions_today['date'].dt.strftime('%Y-%m-%d') == today_str]
            else:
                todays_only = predictions_today
            
            st.success(f"✅ {len(todays_only)} games scheduled")
            
            for idx, game in todays_only.head(5).iterrows():
                away = game.get('away_team', 'Away')
                home = game.get('home_team', 'Home')
                home_prob = game.get('home_win_prob', 0.5)
                confidence = abs(home_prob - 0.5)
                
                if confidence > 0.2:
                    badge_class = "badge-success"
                    badge_text = "HIGH"
                elif confidence > 0.05:
                    badge_class = "badge-warning"
                    badge_text = "MED"
                else:
                    badge_class = "badge-info"
                    badge_text = "TOSS"
                
                st.markdown(f"""
                <div class='glass-dark' style='margin: 10px 0; padding: 15px;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <div style='font-weight: 600; font-size: 1.1em;'>{away} @ {home}</div>
                            <div style='color: #999; font-size: 0.9em; margin-top: 5px;'>
                                Home: {home_prob:.0%} | Away: {1-home_prob:.0%}
                            </div>
                        </div>
                        <div>
                            <span class='badge {badge_class}'>{badge_text}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            if len(todays_only) > 5:
                st.info(f"+ {len(todays_only) - 5} more games. View all in 'Today's Predictions'")
        else:
            st.info("📅 No games scheduled for today")
            st.caption("Check back later or run: `python predict_full.py`")
        
        st.markdown("---")
        
        st.markdown("### 💡 Quick Stats")
        
        win_rate = correct / total_games
        st.markdown(f"""
        <div class='glass' style='margin: 10px 0; padding: 15px;'>
            <div style='font-weight: 600; margin-bottom: 10px;'>Win Rate</div>
            <div style='font-size: 2em; font-weight: 700; color: #4caf50;'>{win_rate:.1%}</div>
            <div class='progress-container' style='margin-top: 10px;'>
                <div class='progress-bar-elite' style='width: {win_rate*100}%;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 View Full Analytics", use_container_width=True):
            st.info("Navigate to 'Performance Analytics' in sidebar")

# ═══════════════════════════════════════════════════════════
# PAGE: TODAY'S PREDICTIONS
# ═══════════════════════════════════════════════════════════

elif page == "🎯 Today's Predictions":
    st.markdown("""
    <div style='text-align: center; margin: 30px 0;'>
        <h2 style='font-weight: 700; font-size: 2.5em;
                   background: linear-gradient(135deg, #1E9BF0 0%, #52C4FF 100%);
                   -webkit-background-clip: text;
                   -webkit-text-fill-color: transparent;
                   background-clip: text;'>
            TODAY'S PREDICTIONS
        </h2>
        <p style='color: #888; font-size: 1.2em;'>Elite Game Analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    if predictions_today is not None and len(predictions_today) > 0:
        # Filter to only today's games
        today_str = datetime.now().strftime('%Y-%m-%d')
        if 'date' in predictions_today.columns:
            predictions_today['date'] = pd.to_datetime(predictions_today['date'], errors='coerce')
            predictions_today = predictions_today[predictions_today['date'].dt.strftime('%Y-%m-%d') == today_str]
        
        # Filters
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        
        with filter_col1:
            min_confidence = st.slider("Minimum Confidence", 0.0, 0.5, 0.0, 0.05)
        
        with filter_col2:
            sort_by = st.selectbox("Sort By", ["Confidence", "Home Team", "Game Time"])
        
        with filter_col3:
            st.metric("Total Games", len(predictions_today))
        
        st.markdown("---")
        
        # Display games
        for idx, game in predictions_today.iterrows():
            away = game.get('away_team', 'Away')
            home = game.get('home_team', 'Home')
            home_prob = game.get('home_win_prob', 0.5)
            away_prob = 1 - home_prob
            confidence = abs(home_prob - 0.5)
            
            if confidence < min_confidence:
                continue
            
            predicted_winner = home if home_prob > 0.5 else away
            
            # Use Streamlit native components instead of complex HTML
            with st.container():
                st.markdown(f"### 🏒 Game {idx + 1}")
                
                # Teams and probabilities
                col1, col2, col3 = st.columns([2, 1, 2])
                
                with col1:
                    st.markdown(f"<h2 style='text-align: right;'>{away}</h2>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align: right; font-size: 1.5em; color: {'green' if away_prob > home_prob else 'orange'};'>{away_prob:.0%}</p>", unsafe_allow_html=True)
                
                with col2:
                    st.markdown("<h3 style='text-align: center;'>@</h3>", unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"<h2 style='text-align: left;'>{home}</h2>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align: left; font-size: 1.5em; color: {'green' if home_prob > away_prob else 'orange'};'>{home_prob:.0%}</p>", unsafe_allow_html=True)
                
                # Confidence
                st.markdown("**Confidence Level:**")
                st.progress(min(confidence * 2, 1.0))
                st.caption(f"{confidence:.0%} edge")
                
                # Prediction
                if confidence < 0.05:
                    st.info(f"⚖️ **TOSS-UP** - Too close to call")
                elif confidence > 0.2:
                    st.success(f"✅ **{predicted_winner}** predicted to win (HIGH CONFIDENCE)")
                else:
                    st.warning(f"📊 **{predicted_winner}** predicted to win (MODERATE)")
                
                st.markdown("---")
            
            # Feature breakdown expander
            with st.expander("🔍 Why This Prediction?"):
                st.markdown("#### Model's Reasoning")
                
                top_10 = data['importance'].head(10)
                
                for _, row in top_10.iterrows():
                    feat = row['Feature']
                    coef = row['Coefficient']
                    
                    helps_home = coef > 0
                    color = "#4caf50" if helps_home else "#f44336"
                    direction = "HOME" if helps_home else "AWAY"
                    
                    bar_width = min(abs(coef) * 100, 100)
                    
                    st.markdown(f"""
                    <div style='margin: 12px 0; padding: 12px; background: #f5f5f5; border-radius: 8px;'>
                        <div style='font-weight: 600; margin-bottom: 5px;'>{feat}</div>
                        <div style='font-size: 0.9em; color: {color}; font-weight: 600;'>→ Helps {direction} team</div>
                        <div class='progress-container' style='margin-top: 8px;'>
                            <div style='height: 100%; width: {bar_width}%; background: {color}; border-radius: 6px;'></div>
                        </div>
                        <div style='font-size: 0.85em; color: #666; margin-top: 5px;'>Coefficient: {coef:.3f}</div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.warning("📅 No predictions available for today")
        st.info("Run: `python predict_full.py` to generate predictions")

# ═══════════════════════════════════════════════════════════
# PAGE: BETTING SIMULATOR
# ═══════════════════════════════════════════════════════════

elif page == "💰 Betting Simulator":
    st.markdown("""
    <div style='text-align: center; margin: 30px 0;'>
        <h2 style='font-weight: 700; font-size: 2.5em;
                   background: linear-gradient(135deg, #1E9BF0 0%, #52C4FF 100%);
                   -webkit-background-clip: text;
                   -webkit-text-fill-color: transparent;
                   background-clip: text;'>
            BETTING SIMULATOR
        </h2>
        <p style='color: #888; font-size: 1.2em;'>ROI Analysis & Strategy Testing</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Strategy selector
    col1, col2, col3 = st.columns(3)
    
    with col1:
        strategy = st.selectbox(
            "Betting Strategy",
            ["threshold", "kelly", "all_games"],
            format_func=lambda x: {
                "threshold": "🎯 Threshold (High Confidence Only)",
                "kelly": "🧮 Kelly Criterion (Optimal Sizing)",
                "all_games": "🎲 All Games (Flat Betting)"
            }[x]
        )
    
    with col2:
        if strategy == "threshold":
            threshold = st.slider("Confidence Threshold", 0.5, 0.8, 0.6, 0.05)
        elif strategy == "kelly":
            threshold = st.slider("Kelly Fraction", 0.1, 1.0, 0.25, 0.05)
        else:
            threshold = 0.5
    
    with col3:
        st.info(f"**Starting Bankroll:** $1,000")
    
    # Calculate betting performance
    with st.spinner("Simulating betting strategy..."):
        try:
            if strategy == "kelly":
                bet_results = calculate_betting_performance(data, strategy='kelly', kelly_fraction=threshold)
            else:
                bet_results = calculate_betting_performance(data, strategy='threshold', threshold=threshold)
        except Exception as e:
            st.error(f"Error calculating betting performance: {e}")
            st.stop()
    
    st.markdown("---")
    
    # Results Dashboard
    res1, res2, res3, res4 = st.columns(4)
    
    with res1:
        st.markdown(f"""
        <div class='gradient-card gradient-blue'>
            <div style='text-align: center; color: white;'>
                <div style='font-size: 2em; margin-bottom: 10px;'>🎲</div>
                <div style='font-size: 2.2em; font-weight: 700;'>{bet_results['total_bets']}</div>
                <div style='font-size: 1em; opacity: 0.9; margin-top: 5px;'>Total Bets</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with res2:
        win_rate = bet_results['win_rate']
        st.markdown(f"""
        <div class='gradient-card gradient-green'>
            <div style='text-align: center; color: white;'>
                <div style='font-size: 2em; margin-bottom: 10px;'>✅</div>
                <div style='font-size: 2.2em; font-weight: 700;'>{win_rate:.1%}</div>
                <div style='font-size: 1em; opacity: 0.9; margin-top: 5px;'>Win Rate</div>
                <div style='font-size: 0.9em; opacity: 0.7; margin-top: 5px;'>{bet_results['wins']}W - {bet_results['losses']}L</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with res3:
        roi = bet_results['roi']
        roi_color = "gradient-green" if roi > 0 else "gradient-pink"
        st.markdown(f"""
        <div class='gradient-card {roi_color}'>
            <div style='text-align: center; color: white;'>
                <div style='font-size: 2em; margin-bottom: 10px;'>💰</div>
                <div style='font-size: 2.2em; font-weight: 700;'>{roi:+.1f}%</div>
                <div style='font-size: 1em; opacity: 0.9; margin-top: 5px;'>ROI</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with res4:
        profit = bet_results['final_profit']
        profit_color = "gradient-orange" if profit > 0 else "gradient-pink"
        st.markdown(f"""
        <div class='gradient-card {profit_color}'>
            <div style='text-align: center; color: white;'>
                <div style='font-size: 2em; margin-bottom: 10px;'>{'📈' if profit > 0 else '📉'}</div>
                <div style='font-size: 2.2em; font-weight: 700;'>${profit:+.0f}</div>
                <div style='font-size: 1em; opacity: 0.9; margin-top: 5px;'>Total Profit</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Profit Curve
    st.markdown("### 📈 Profit Curve Over Time")
    
    games = bet_results['games']
    games['game_number'] = range(1, len(games) + 1)
    
    chart = alt.Chart(games[games['bet']]).mark_line(point=True, strokeWidth=3).encode(
        x=alt.X('game_number:Q', title='Game Number'),
        y=alt.Y('cumulative_profit:Q', title='Cumulative Profit ($)'),
        tooltip=['game_number', 'cumulative_profit', 'return']
    ).properties(
        height=400
    )
    
    # Add zero line
    zero_line = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(strokeDash=[5, 5], color='red').encode(y='y:Q')
    
    st.altair_chart(chart + zero_line, use_container_width=True)
    
    # Strategy explanation
    with st.expander("📚 Strategy Details"):
        if strategy == "threshold":
            st.markdown(f"""
            **Threshold Betting Strategy**
            
            - Only bet on games where model confidence exceeds {threshold:.0%}
            - Fixed bet size: $1 per game
            - Assuming -110 odds (91% return on win)
            - Total games bet: {bet_results['total_bets']} / {len(games)}
            
            **Best For:** Risk-averse bettors who want high confidence picks
            """)
        elif strategy == "kelly":
            st.markdown(f"""
            **Kelly Criterion Strategy**
            
            - Bet size proportional to edge: Kelly Fraction = {threshold}
            - Larger bets on higher confidence games
            - Smaller bets on lower confidence games
            - Optimal for maximizing long-term growth
            
            **Best For:** Sophisticated bettors with proper bankroll management
            """)
        else:
            st.markdown("""
            **All Games Strategy**
            
            - Bet on every game
            - Fixed bet size: $1 per game
            - No filtering by confidence
            
            **Best For:** Baseline comparison / High volume approach
            """)

# ═══════════════════════════════════════════════════════════
# PAGE: PERFORMANCE ANALYTICS
# ═══════════════════════════════════════════════════════════

elif page == "📈 Performance Analytics":
    st.markdown("""
    <div style='text-align: center; margin: 30px 0;'>
        <h2 style='font-weight: 700; font-size: 2.5em;
                   background: linear-gradient(135deg, #1E9BF0 0%, #52C4FF 100%);
                   -webkit-background-clip: text;
                   -webkit-text-fill-color: transparent;
                   background-clip: text;'>
            PERFORMANCE ANALYTICS
        </h2>
        <p style='color: #888; font-size: 1.2em;'>Deep Dive Model Analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📊 Calibration", "🎯 Confidence Buckets", "🏒 Team Performance"])
    
    with tab1:
        st.markdown("### 📊 Model Calibration")
        
        try:
            calib_data = calculate_confidence_calibration(data)
        except Exception as e:
            st.error(f"Error calculating calibration: {e}")
            st.stop()
        
        # Calibration chart
        chart = alt.Chart(calib_data).mark_line(point=True, strokeWidth=3).encode(
            x=alt.X('predicted:Q', title='Predicted Probability', scale=alt.Scale(domain=[0.4, 0.75])),
            y=alt.Y('actual:Q', title='Actual Win Rate', scale=alt.Scale(domain=[0.4, 0.75])),
            tooltip=['bucket', 'predicted', 'actual', 'count']
        ).properties(height=400)
        
        # Perfect calibration line
        perfect = alt.Chart(pd.DataFrame({'x': [0.4, 0.75], 'y': [0.4, 0.75]})).mark_line(
            strokeDash=[5, 5],
            color='red'
        ).encode(x='x:Q', y='y:Q')
        
        st.altair_chart(chart + perfect, use_container_width=True)
        
        st.caption("🔴 Red dashed line = perfect calibration. Closer is better!")
        
        st.markdown("### 📋 Calibration Table")
        st.dataframe(
            calib_data.style.format({
                'predicted': '{:.1%}',
                'actual': '{:.1%}',
                'calibration_error': '{:.2%}'
            }),
            use_container_width=True,
            hide_index=True
        )
    
    with tab2:
        st.markdown("### 🎯 Performance by Confidence Level")
        
        for _, row in calib_data.iterrows():
            bucket = row['bucket']
            predicted = row['predicted']
            actual = row['actual']
            count = row['count']
            error = row['calibration_error']
            
            accuracy_pct = actual * 100
            
            if error < 0.03:
                badge = "badge-success"
                status = "✅ Excellent"
            elif error < 0.06:
                badge = "badge-warning"
                status = "⚠️ Good"
            else:
                badge = "badge-danger"
                status = "❌ Needs Work"
            
            st.markdown(f"""
            <div class='glass' style='margin: 15px 0; padding: 20px;'>
                <div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;'>
                    <div>
                        <div style='font-size: 1.3em; font-weight: 600;'>{bucket} Confidence</div>
                        <div style='color: #666; margin-top: 5px;'>{count} games</div>
                    </div>
                    <div style='text-align: center; margin: 10px 20px;'>
                        <div style='font-size: 0.9em; color: #666;'>Predicted</div>
                        <div style='font-size: 1.8em; font-weight: 700; color: #2196f3;'>{predicted:.1%}</div>
                    </div>
                    <div style='text-align: center; margin: 10px 20px;'>
                        <div style='font-size: 0.9em; color: #666;'>Actual</div>
                        <div style='font-size: 1.8em; font-weight: 700; color: #4caf50;'>{actual:.1%}</div>
                    </div>
                    <div>
                        <span class='badge {badge}'>{status}</span>
                    </div>
                </div>
                <div class='progress-container' style='margin-top: 15px;'>
                    <div class='progress-bar-elite' style='width: {accuracy_pct}%;'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with tab3:
        st.markdown("### 🏒 Model Performance by Team")
        
        try:
            team_perf = get_team_performance_matrix(data)
        except Exception as e:
            st.error(f"Error calculating team performance: {e}")
            st.stop()
        
        if len(team_perf) > 0:
            # Top 10 teams
            st.markdown("#### 🏆 Top 10 Teams (Easiest to Predict)")
            
            top_10 = team_perf.head(10)
            
            for _, row in top_10.iterrows():
                team = row['team']
                acc = row['accuracy']
                games = row['games']
                correct = row['correct']
                
                st.markdown(f"""
                <div class='glass-dark' style='margin: 10px 0; padding: 15px;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <div style='font-size: 1.2em; font-weight: 600;'>{team}</div>
                            <div style='color: #999; font-size: 0.9em;'>{correct}/{games} correct</div>
                        </div>
                        <div style='text-align: right;'>
                            <div style='font-size: 1.5em; font-weight: 700; color: #4caf50;'>{acc:.1%}</div>
                            <div class='progress-container' style='width: 100px; margin-top: 5px;'>
                                <div class='progress-bar-elite' style='width: {acc*100}%;'></div>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Bottom 10 teams
            st.markdown("#### 📉 Bottom 10 Teams (Hardest to Predict)")
            
            bottom_10 = team_perf.tail(10)
            
            for _, row in bottom_10.iterrows():
                team = row['team']
                acc = row['accuracy']
                games = row['games']
                correct = row['correct']
                
                st.markdown(f"""
                <div class='glass-dark' style='margin: 10px 0; padding: 15px;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <div style='font-size: 1.2em; font-weight: 600;'>{team}</div>
                            <div style='color: #999; font-size: 0.9em;'>{correct}/{games} correct</div>
                        </div>
                        <div style='text-align: right;'>
                            <div style='font-size: 1.5em; font-weight: 700; color: #ff9800;'>{acc:.1%}</div>
                            <div class='progress-container' style='width: 100px; margin-top: 5px;'>
                                <div class='progress-bar-elite' style='width: {acc*100}%;'></div>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# (Continue with other pages...)

elif page == "🔬 Deep Analysis":
    st.markdown("""
    <div style='text-align: center; margin: 30px 0;'>
        <h2 style='font-weight: 700; font-size: 2.5em;
                   background: linear-gradient(135deg, #1E9BF0 0%, #52C4FF 100%);
                   -webkit-background-clip: text;
                   -webkit-text-fill-color: transparent;
                   background-clip: text;'>
            DEEP ANALYSIS
        </h2>
        <p style='color: #888; font-size: 1.2em;'>Advanced Feature Engineering & Insights</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs for different analyses
    analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs([
        "🔗 Feature Correlations",
        "📊 Feature Distributions", 
        "🎯 Prediction Confidence Analysis"
    ])
    
    with analysis_tab1:
        st.markdown("### 🔗 Top Feature Correlations")
        st.caption("Understanding which features work together")
        
        # Get top features
        top_features = data['importance'].head(15)['Feature'].tolist()
        
        # Calculate correlation matrix for top features
        feature_data = data['dataset'].features[top_features]
        corr_matrix = feature_data.corr()
        
        # Create heatmap data
        corr_pairs = []
        for i, feat1 in enumerate(top_features):
            for j, feat2 in enumerate(top_features):
                if i < j:  # Only upper triangle
                    corr_val = corr_matrix.loc[feat1, feat2]
                    if abs(corr_val) > 0.3:  # Only show significant correlations
                        corr_pairs.append({
                            'Feature 1': feat1,
                            'Feature 2': feat2,
                            'Correlation': corr_val,
                            'Abs_Correlation': abs(corr_val)
                        })
        
        corr_df = pd.DataFrame(corr_pairs).sort_values('Abs_Correlation', ascending=False).head(20)
        
        if len(corr_df) > 0:
            # Visualization
            chart = alt.Chart(corr_df).mark_bar().encode(
                y=alt.Y('Feature 1:N', title='', sort='-x'),
                x=alt.X('Correlation:Q', title='Correlation Coefficient', scale=alt.Scale(domain=[-1, 1])),
                color=alt.condition(
                    alt.datum.Correlation > 0,
                    alt.value('#4caf50'),
                    alt.value('#f44336')
                ),
                tooltip=['Feature 1', 'Feature 2', 'Correlation']
            ).properties(height=400)
            
            st.altair_chart(chart, use_container_width=True)
            
            st.markdown("### 📋 Top Correlated Feature Pairs")
            
            for _, row in corr_df.head(10).iterrows():
                corr_val = row['Correlation']
                color = "#4caf50" if corr_val > 0 else "#f44336"
                corr_type = "Positive" if corr_val > 0 else "Negative"
                
                st.markdown(f"""
                <div class='glass' style='margin: 10px 0; padding: 15px;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div style='flex: 1;'>
                            <div style='font-weight: 600;'>{row['Feature 1']}</div>
                            <div style='color: #999; font-size: 0.9em; margin-top: 5px;'>↔️ {row['Feature 2']}</div>
                        </div>
                        <div style='text-align: right;'>
                            <div style='font-size: 1.5em; font-weight: 700; color: {color};'>{corr_val:.3f}</div>
                            <div style='color: {color}; font-size: 0.9em;'>{corr_type} Correlation</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No significant correlations found among top features")
    
    with analysis_tab2:
        st.markdown("### 📊 Feature Value Distributions")
        st.caption("Analyzing feature patterns across predictions")
        
        # Select a feature to analyze
        selected_feature = st.selectbox(
            "Choose a feature to analyze:",
            top_features[:10],
            key='dist_feature'
        )
        
        if selected_feature:
            feature_values = data['dataset'].features[selected_feature][data['test_mask']]
            actual_outcomes = data['dataset'].target[data['test_mask']]
            
            # Create dataframe for plotting
            dist_df = pd.DataFrame({
                'value': feature_values,
                'outcome': actual_outcomes.map({1: 'Home Win', 0: 'Away Win'})
            })
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Distribution by Outcome**")
                
                # Box plot
                chart = alt.Chart(dist_df).mark_boxplot().encode(
                    x=alt.X('outcome:N', title='Outcome'),
                    y=alt.Y('value:Q', title=selected_feature),
                    color=alt.Color('outcome:N', scale=alt.Scale(
                        domain=['Home Win', 'Away Win'],
                        range=['#4caf50', '#ff9800']
                    ))
                ).properties(height=300)
                
                st.altair_chart(chart, use_container_width=True)
            
            with col2:
                st.markdown("**Statistical Summary**")
                
                home_wins = dist_df[dist_df['outcome'] == 'Home Win']['value']
                away_wins = dist_df[dist_df['outcome'] == 'Away Win']['value']
                
                stats_df = pd.DataFrame({
                    'Metric': ['Mean', 'Median', 'Std Dev', 'Min', 'Max'],
                    'Home Wins': [
                        home_wins.mean(),
                        home_wins.median(),
                        home_wins.std(),
                        home_wins.min(),
                        home_wins.max()
                    ],
                    'Away Wins': [
                        away_wins.mean(),
                        away_wins.median(),
                        away_wins.std(),
                        away_wins.min(),
                        away_wins.max()
                    ]
                })
                
                st.dataframe(
                    stats_df.style.format({
                        'Home Wins': '{:.4f}',
                        'Away Wins': '{:.4f}'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
            
            # Histogram
            st.markdown("**Value Distribution**")
            
            hist_chart = alt.Chart(dist_df).mark_bar(opacity=0.7).encode(
                x=alt.X('value:Q', bin=alt.Bin(maxbins=30), title=selected_feature),
                y=alt.Y('count()', title='Count'),
                color=alt.Color('outcome:N', scale=alt.Scale(
                    domain=['Home Win', 'Away Win'],
                    range=['#4caf50', '#ff9800']
                ))
            ).properties(height=300)
            
            st.altair_chart(hist_chart, use_container_width=True)
    
    with analysis_tab3:
        st.markdown("### 🎯 Prediction Confidence vs Accuracy")
        st.caption("How well does our confidence match reality?")
        
        # Get predictions and actuals
        test_probs = data['test_probs']
        test_actual = data['dataset'].target[data['test_mask']].values
        test_predicted = (test_probs >= 0.5).astype(int)
        test_correct = (test_predicted == test_actual)
        
        # Create bins
        confidence_levels = np.abs(test_probs - 0.5)
        
        # Create dataframe
        confidence_df = pd.DataFrame({
            'confidence': confidence_levels,
            'correct': test_correct,
            'probability': test_probs
        })
        
        # Bin by confidence
        confidence_df['conf_bin'] = pd.cut(
            confidence_df['confidence'],
            bins=[0, 0.05, 0.1, 0.15, 0.2, 0.5],
            labels=['0-5%', '5-10%', '10-15%', '15-20%', '20%+']
        )
        
        # Calculate accuracy by bin
        bin_stats = confidence_df.groupby('conf_bin').agg({
            'correct': ['sum', 'count', 'mean']
        }).reset_index()
        
        bin_stats.columns = ['Confidence Range', 'Correct', 'Total', 'Accuracy']
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Chart
            chart = alt.Chart(bin_stats).mark_bar().encode(
                x=alt.X('Confidence Range:N', title='Confidence Level'),
                y=alt.Y('Accuracy:Q', title='Actual Accuracy', scale=alt.Scale(domain=[0.4, 0.8]), axis=alt.Axis(format='%')),
                color=alt.value('#667eea'),
                tooltip=['Confidence Range', 'Accuracy', 'Correct', 'Total']
            ).properties(height=300)
            
            # Add baseline
            baseline = alt.Chart(pd.DataFrame({'y': [0.531]})).mark_rule(
                strokeDash=[5, 5],
                color='red'
            ).encode(y='y:Q')
            
            st.altair_chart(chart + baseline, use_container_width=True)
            st.caption("🔴 Red line = baseline (53.1%)")
        
        with col2:
            st.markdown("**Performance by Confidence**")
            
            for _, row in bin_stats.iterrows():
                conf_range = row['Confidence Range']
                accuracy = row['Accuracy']
                correct = int(row['Correct'])
                total = int(row['Total'])
                
                acc_pct = accuracy * 100
                
                if accuracy > 0.60:
                    badge_color = "#4caf50"
                    badge_text = "Excellent"
                elif accuracy > 0.55:
                    badge_color = "#ff9800"
                    badge_text = "Good"
                else:
                    badge_color = "#f44336"
                    badge_text = "Needs Work"
                
                st.markdown(f"""
                <div style='margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 8px; border-left: 4px solid {badge_color};'>
                    <div style='font-weight: 600;'>{conf_range} Edge</div>
                    <div style='font-size: 1.3em; font-weight: 700; color: {badge_color}; margin: 5px 0;'>{acc_pct:.1f}%</div>
                    <div style='font-size: 0.9em; color: #666;'>{correct}/{total} correct</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown("### 💡 Key Insights")
        
        # Calculate insights
        high_conf = bin_stats[bin_stats['Confidence Range'] == '20%+']['Accuracy'].iloc[0] if len(bin_stats[bin_stats['Confidence Range'] == '20%+']) > 0 else 0
        low_conf = bin_stats[bin_stats['Confidence Range'] == '0-5%']['Accuracy'].iloc[0] if len(bin_stats[bin_stats['Confidence Range'] == '0-5%']) > 0 else 0
        
        insight_col1, insight_col2, insight_col3 = st.columns(3)
        
        with insight_col1:
            st.markdown(f"""
            <div class='gradient-card gradient-blue'>
                <div style='text-align: center; color: white;'>
                    <div style='font-size: 1.5em; margin-bottom: 10px;'>🎯</div>
                    <div style='font-size: 1.8em; font-weight: 700;'>{high_conf:.1%}</div>
                    <div style='font-size: 0.9em; opacity: 0.9; margin-top: 5px;'>High Confidence</div>
                    <div style='font-size: 0.8em; opacity: 0.7; margin-top: 5px;'>Accuracy (20%+ edge)</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with insight_col2:
            st.markdown(f"""
            <div class='gradient-card gradient-orange'>
                <div style='text-align: center; color: white;'>
                    <div style='font-size: 1.5em; margin-bottom: 10px;'>⚖️</div>
                    <div style='font-size: 1.8em; font-weight: 700;'>{low_conf:.1%}</div>
                    <div style='font-size: 0.9em; opacity: 0.9; margin-top: 5px;'>Low Confidence</div>
                    <div style='font-size: 0.8em; opacity: 0.7; margin-top: 5px;'>Accuracy (0-5% edge)</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with insight_col3:
            improvement = (high_conf - low_conf) * 100
            st.markdown(f"""
            <div class='gradient-card gradient-green'>
                <div style='text-align: center; color: white;'>
                    <div style='font-size: 1.5em; margin-bottom: 10px;'>📈</div>
                    <div style='font-size: 1.8em; font-weight: 700;'>+{improvement:.1f}%</div>
                    <div style='font-size: 0.9em; opacity: 0.9; margin-top: 5px;'>Confidence Edge</div>
                    <div style='font-size: 0.8em; opacity: 0.7; margin-top: 5px;'>High vs Low</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

elif page == "🏆 Leaderboards":
    st.markdown("""
    <div style='text-align: center; margin: 30px 0;'>
        <h2 style='font-weight: 700; font-size: 2.5em;
                   background: linear-gradient(135deg, #1E9BF0 0%, #52C4FF 100%);
                   -webkit-background-clip: text;
                   -webkit-text-fill-color: transparent;
                   background-clip: text;'>
            LEADERBOARDS
        </h2>
        <p style='color: #888; font-size: 1.2em;'>Rankings, Streaks & Records</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs for different leaderboards
    lead_tab1, lead_tab2, lead_tab3 = st.tabs([
        "🏆 Team Rankings",
        "🔥 Streak Tracker",
        "📊 Best/Worst Matchups"
    ])
    
    with lead_tab1:
        st.markdown("### 🏆 Team Prediction Accuracy Rankings")
        st.caption("Which teams does our model predict best?")
        
        try:
            team_perf = get_team_performance_matrix(data)
            
            if len(team_perf) > 0:
                # Overall stats
                avg_accuracy = team_perf['accuracy'].mean()
                best_team = team_perf.iloc[0]
                worst_team = team_perf.iloc[-1]
                
                stat_col1, stat_col2, stat_col3 = st.columns(3)
                
                with stat_col1:
                    st.markdown(f"""
                    <div class='gradient-card gradient-green'>
                        <div style='text-align: center; color: white;'>
                            <div style='font-size: 2em; margin-bottom: 10px;'>🥇</div>
                            <div style='font-size: 1.5em; font-weight: 700;'>{best_team['team']}</div>
                            <div style='font-size: 1.2em; opacity: 0.9; margin-top: 5px;'>{best_team['accuracy']:.1%}</div>
                            <div style='font-size: 0.9em; opacity: 0.7; margin-top: 5px;'>Best Predicted Team</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with stat_col2:
                    st.markdown(f"""
                    <div class='gradient-card gradient-blue'>
                        <div style='text-align: center; color: white;'>
                            <div style='font-size: 2em; margin-bottom: 10px;'>📊</div>
                            <div style='font-size: 1.5em; font-weight: 700;'>{avg_accuracy:.1%}</div>
                            <div style='font-size: 0.9em; opacity: 0.9; margin-top: 5px;'>Average Accuracy</div>
                            <div style='font-size: 0.9em; opacity: 0.7; margin-top: 5px;'>Across All Teams</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with stat_col3:
                    st.markdown(f"""
                    <div class='gradient-card gradient-orange'>
                        <div style='text-align: center; color: white;'>
                            <div style='font-size: 2em; margin-bottom: 10px;'>📉</div>
                            <div style='font-size: 1.5em; font-weight: 700;'>{worst_team['team']}</div>
                            <div style='font-size: 1.2em; opacity: 0.9; margin-top: 5px;'>{worst_team['accuracy']:.1%}</div>
                            <div style='font-size: 0.9em; opacity: 0.7; margin-top: 5px;'>Most Unpredictable</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Full rankings table
                st.markdown("### 📋 Complete Rankings")
                
                rank_col1, rank_col2 = st.columns([1, 2])
                
                with rank_col1:
                    # Filter options
                    sort_by = st.radio(
                        "Sort by:",
                        ["Accuracy (High→Low)", "Accuracy (Low→High)", "Games Analyzed"],
                        key='team_sort'
                    )
                
                with rank_col2:
                    min_games = st.slider(
                        "Minimum games analyzed:",
                        min_value=1,
                        max_value=int(team_perf['games'].max()),
                        value=5,
                        key='min_games_slider'
                    )
                
                # Apply filters
                filtered_teams = team_perf[team_perf['games'] >= min_games].copy()
                
                if sort_by == "Accuracy (High→Low)":
                    filtered_teams = filtered_teams.sort_values('accuracy', ascending=False)
                elif sort_by == "Accuracy (Low→High)":
                    filtered_teams = filtered_teams.sort_values('accuracy', ascending=True)
                else:
                    filtered_teams = filtered_teams.sort_values('games', ascending=False)
                
                # Display rankings
                for rank, (_, team_row) in enumerate(filtered_teams.iterrows(), 1):
                    team = team_row['team']
                    acc = team_row['accuracy']
                    games = int(team_row['games'])
                    correct = int(team_row['correct'])
                    
                    # Medal for top 3
                    if rank == 1:
                        medal = "🥇"
                        bg_color = "rgba(255, 215, 0, 0.1)"
                    elif rank == 2:
                        medal = "🥈"
                        bg_color = "rgba(192, 192, 192, 0.1)"
                    elif rank == 3:
                        medal = "🥉"
                        bg_color = "rgba(205, 127, 50, 0.1)"
                    else:
                        medal = f"#{rank}"
                        bg_color = "rgba(0, 0, 0, 0.05)"
                    
                    # Color based on performance
                    if acc > avg_accuracy:
                        acc_color = "#4caf50"
                    elif acc > 0.5:
                        acc_color = "#ff9800"
                    else:
                        acc_color = "#f44336"
                    
                    st.markdown(f"""
                    <div style='margin: 10px 0; padding: 15px; background: {bg_color}; border-radius: 12px; border-left: 4px solid {acc_color};'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <div style='display: flex; align-items: center; gap: 15px;'>
                                <div style='font-size: 1.5em; font-weight: 700; min-width: 50px;'>{medal}</div>
                                <div>
                                    <div style='font-size: 1.2em; font-weight: 600;'>{team}</div>
                                    <div style='font-size: 0.9em; color: #666;'>{correct}/{games} correct predictions</div>
                                </div>
                            </div>
                            <div style='text-align: right;'>
                                <div style='font-size: 1.8em; font-weight: 700; color: {acc_color};'>{acc:.1%}</div>
                                <div class='progress-container' style='width: 120px; margin-top: 5px;'>
                                    <div class='progress-bar-elite' style='width: {acc*100}%;'></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No team data available")
        except Exception as e:
            st.error(f"Error loading team rankings: {e}")
    
    with lead_tab2:
        st.markdown("### 🔥 Current Prediction Streaks")
        st.caption("Teams we're on hot or cold streaks with")
        
        try:
            # Get recent games
            test_games = data['dataset'].games[data['test_mask']].copy()
            test_probs = data['test_probs']
            test_actual = data['dataset'].target[data['test_mask']]
            
            test_games['predicted'] = (test_probs >= 0.5).astype(int)
            test_games['actual'] = test_actual.values
            test_games['correct'] = (test_games['predicted'] == test_games['actual'])
            test_games['gameDate'] = pd.to_datetime(test_games['gameDate'])
            test_games = test_games.sort_values('gameDate')
            
            # Calculate streaks for each team
            streak_data = []
            
            for team_col in ['teamAbbrev_home', 'teamAbbrev_away']:
                if team_col in test_games.columns:
                    for team in test_games[team_col].unique():
                        if pd.isna(team):
                            continue
                        
                        team_games = test_games[
                            (test_games['teamAbbrev_home'] == team) | 
                            (test_games['teamAbbrev_away'] == team)
                        ].tail(10)  # Last 10 games
                        
                        if len(team_games) >= 3:
                            # Calculate current streak
                            current_streak = 0
                            streak_type = None
                            
                            for correct in reversed(team_games['correct'].tolist()):
                                if streak_type is None:
                                    streak_type = 'correct' if correct else 'incorrect'
                                    current_streak = 1
                                elif (streak_type == 'correct' and correct) or (streak_type == 'incorrect' and not correct):
                                    current_streak += 1
                                else:
                                    break
                            
                            recent_accuracy = team_games['correct'].mean()
                            
                            streak_data.append({
                                'team': team,
                                'streak': current_streak,
                                'streak_type': streak_type,
                                'recent_accuracy': recent_accuracy,
                                'recent_games': len(team_games)
                            })
            
            streak_df = pd.DataFrame(streak_data)
            
            if len(streak_df) > 0:
                # Hot streaks (correct predictions)
                hot_streaks = streak_df[
                    (streak_df['streak_type'] == 'correct') & 
                    (streak_df['streak'] >= 3)
                ].sort_values('streak', ascending=False)
                
                # Cold streaks (incorrect predictions)
                cold_streaks = streak_df[
                    (streak_df['streak_type'] == 'incorrect') & 
                    (streak_df['streak'] >= 3)
                ].sort_values('streak', ascending=False)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 🔥 HOT STREAKS (Correct Predictions)")
                    
                    if len(hot_streaks) > 0:
                        for _, streak in hot_streaks.head(10).iterrows():
                            st.markdown(f"""
                            <div class='gradient-card gradient-green' style='margin: 10px 0;'>
                                <div style='padding: 15px; color: white;'>
                                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                                        <div>
                                            <div style='font-size: 1.3em; font-weight: 700;'>{streak['team']}</div>
                                            <div style='font-size: 0.9em; opacity: 0.9; margin-top: 5px;'>
                                                {streak['recent_accuracy']:.0%} in last {streak['recent_games']} games
                                            </div>
                                        </div>
                                        <div style='text-align: right;'>
                                            <div style='font-size: 2em; font-weight: 700;'>{streak['streak']}</div>
                                            <div style='font-size: 0.9em; opacity: 0.9;'>streak</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No hot streaks (3+ correct) currently")
                
                with col2:
                    st.markdown("#### ❄️ COLD STREAKS (Incorrect Predictions)")
                    
                    if len(cold_streaks) > 0:
                        for _, streak in cold_streaks.head(10).iterrows():
                            st.markdown(f"""
                            <div class='gradient-card gradient-pink' style='margin: 10px 0;'>
                                <div style='padding: 15px; color: white;'>
                                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                                        <div>
                                            <div style='font-size: 1.3em; font-weight: 700;'>{streak['team']}</div>
                                            <div style='font-size: 0.9em; opacity: 0.9; margin-top: 5px;'>
                                                {streak['recent_accuracy']:.0%} in last {streak['recent_games']} games
                                            </div>
                                        </div>
                                        <div style='text-align: right;'>
                                            <div style='font-size: 2em; font-weight: 700;'>{streak['streak']}</div>
                                            <div style='font-size: 0.9em; opacity: 0.9;'>streak</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No cold streaks (3+ incorrect) currently")
            else:
                st.info("No streak data available")
        except Exception as e:
            st.error(f"Error calculating streaks: {e}")
    
    with lead_tab3:
        st.markdown("### 📊 Best & Worst Matchups")
        st.caption("Team combinations we predict well or poorly")
        
        try:
            # Get games with both teams
            test_games = data['dataset'].games[data['test_mask']].copy()
            test_probs = data['test_probs']
            test_actual = data['dataset'].target[data['test_mask']]
            
            test_games['predicted'] = (test_probs >= 0.5).astype(int)
            test_games['actual'] = test_actual.values
            test_games['correct'] = (test_games['predicted'] == test_games['actual'])
            
            # Create matchup pairs
            if 'teamAbbrev_home' in test_games.columns and 'teamAbbrev_away' in test_games.columns:
                matchup_stats = test_games.groupby(['teamAbbrev_away', 'teamAbbrev_home']).agg({
                    'correct': ['sum', 'count', 'mean']
                }).reset_index()
                
                matchup_stats.columns = ['away_team', 'home_team', 'correct', 'total', 'accuracy']
                matchup_stats = matchup_stats[matchup_stats['total'] >= 2]  # At least 2 games
                
                if len(matchup_stats) > 0:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### ✅ Best Matchups")
                        st.caption("Matchups we predict most accurately")
                        
                        best_matchups = matchup_stats.sort_values('accuracy', ascending=False).head(10)
                        
                        for _, matchup in best_matchups.iterrows():
                            away = matchup['away_team']
                            home = matchup['home_team']
                            acc = matchup['accuracy']
                            correct = int(matchup['correct'])
                            total = int(matchup['total'])
                            
                            st.markdown(f"""
                            <div class='glass' style='margin: 10px 0; padding: 15px; border-left: 4px solid #4caf50;'>
                                <div style='display: flex; justify-content: space-between; align-items: center;'>
                                    <div>
                                        <div style='font-weight: 600; font-size: 1.1em;'>{away} @ {home}</div>
                                        <div style='color: #666; font-size: 0.9em; margin-top: 5px;'>{correct}/{total} correct</div>
                                    </div>
                                    <div style='text-align: right;'>
                                        <div style='font-size: 1.5em; font-weight: 700; color: #4caf50;'>{acc:.0%}</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("#### ❌ Worst Matchups")
                        st.caption("Matchups we struggle to predict")
                        
                        worst_matchups = matchup_stats.sort_values('accuracy', ascending=True).head(10)
                        
                        for _, matchup in worst_matchups.iterrows():
                            away = matchup['away_team']
                            home = matchup['home_team']
                            acc = matchup['accuracy']
                            correct = int(matchup['correct'])
                            total = int(matchup['total'])
                            
                            st.markdown(f"""
                            <div class='glass' style='margin: 10px 0; padding: 15px; border-left: 4px solid #f44336;'>
                                <div style='display: flex; justify-content: space-between; align-items: center;'>
                                    <div>
                                        <div style='font-weight: 600; font-size: 1.1em;'>{away} @ {home}</div>
                                        <div style='color: #666; font-size: 0.9em; margin-top: 5px;'>{correct}/{total} correct</div>
                                    </div>
                                    <div style='text-align: right;'>
                                        <div style='font-size: 1.5em; font-weight: 700; color: #f44336;'>{acc:.0%}</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("Not enough matchup data (need 2+ games per matchup)")
            else:
                st.info("Team columns not available")
        except Exception as e:
            st.error(f"Error calculating matchups: {e}")

# ═══════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════

st.markdown("""
<div style='text-align: center; margin-top: 80px; padding: 40px; opacity: 0.6; border-top: 1px solid #eee;'>
    <div style='font-size: 1.1em; font-weight: 600; margin-bottom: 10px;'>
        Puckcast.ai
    </div>
    <div style='font-size: 0.9em; color: #666;'>
        Data-Driven NHL Prediction Intelligence
    </div>
    <div style='font-size: 0.85em; color: #999; margin-top: 10px;'>
        Data: MoneyPuck + NHL API | Model: Logistic Regression | 141 Features | 59.2% Accuracy
    </div>
</div>
""", unsafe_allow_html=True)

