"""
Create Beautiful Visualizations for NHL Prediction Model
=========================================================
This script generates a variety of insightful and visually appealing charts
for the NHL prediction model project.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Create output directory
output_dir = Path("reports/visualizations")
output_dir.mkdir(parents=True, exist_ok=True)

# Load data
print("Loading data...")
predictions_df = pd.read_csv("reports/predictions_20232024.csv")
moneypuck_df = pd.read_csv("data/moneypuck_all_games.csv")

# Convert date columns
predictions_df['gameDate'] = pd.to_datetime(predictions_df['gameDate'])
moneypuck_df['gameDate'] = pd.to_datetime(moneypuck_df['gameDate'])

print(f"Loaded {len(predictions_df)} predictions")
print(f"Loaded {len(moneypuck_df)} MoneyPuck records\n")

# ============================================================================
# 1. PREDICTION CONFIDENCE VS ACCURACY ANALYSIS
# ============================================================================
print("Creating Visualization 1: Prediction Confidence vs Accuracy...")

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Model Confidence Analysis', fontsize=20, fontweight='bold', y=0.995)

# Confidence distribution
ax1 = axes[0, 0]
confidence = predictions_df['home_win_probability'].apply(lambda x: abs(x - 0.5) * 2)
ax1.hist(confidence, bins=50, alpha=0.7, color='#2E86AB', edgecolor='black')
ax1.axvline(confidence.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {confidence.mean():.3f}')
ax1.set_xlabel('Model Confidence', fontsize=12, fontweight='bold')
ax1.set_ylabel('Frequency', fontsize=12, fontweight='bold')
ax1.set_title('Distribution of Model Confidence', fontsize=14, fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Binned confidence vs accuracy
ax2 = axes[0, 1]
confidence_bins = pd.cut(confidence, bins=10)
bin_accuracy = predictions_df.groupby(confidence_bins)['correct'].mean()
bin_centers = [interval.mid for interval in bin_accuracy.index]
colors = plt.cm.RdYlGn(bin_accuracy.values)
ax2.bar(range(len(bin_accuracy)), bin_accuracy.values, color=colors, edgecolor='black', linewidth=1.5)
ax2.axhline(0.5, color='gray', linestyle='--', alpha=0.5, label='Random Baseline')
ax2.set_xlabel('Confidence Bin', fontsize=12, fontweight='bold')
ax2.set_ylabel('Accuracy', fontsize=12, fontweight='bold')
ax2.set_title('Accuracy by Confidence Level', fontsize=14, fontweight='bold')
ax2.set_ylim(0, 1)
ax2.set_xticks(range(len(bin_accuracy)))
ax2.set_xticklabels([f'{x:.2f}' for x in bin_centers], rotation=45)
ax2.legend()
ax2.grid(True, alpha=0.3, axis='y')

# Win probability calibration
ax3 = axes[1, 0]
prob_bins = pd.cut(predictions_df['home_win_probability'], bins=10)
actual_win_rate = predictions_df.groupby(prob_bins)['home_win'].mean()
predicted_win_rate = predictions_df.groupby(prob_bins)['home_win_probability'].mean()
bin_labels = [f'{interval.mid:.2f}' for interval in actual_win_rate.index]
x = np.arange(len(actual_win_rate))
width = 0.35
ax3.bar(x - width/2, actual_win_rate.values, width, label='Actual', alpha=0.8, color='#A23B72', edgecolor='black')
ax3.bar(x + width/2, predicted_win_rate.values, width, label='Predicted', alpha=0.8, color='#F18F01', edgecolor='black')
ax3.plot(x, predicted_win_rate.values, 'k--', alpha=0.5, linewidth=2)
ax3.set_xlabel('Predicted Win Probability Bin', fontsize=12, fontweight='bold')
ax3.set_ylabel('Win Rate', fontsize=12, fontweight='bold')
ax3.set_title('Calibration: Predicted vs Actual Win Rates', fontsize=14, fontweight='bold')
ax3.set_xticks(x)
ax3.set_xticklabels(bin_labels, rotation=45)
ax3.legend()
ax3.grid(True, alpha=0.3, axis='y')

# Prediction margin analysis
ax4 = axes[1, 1]
predictions_df['win_margin'] = predictions_df.apply(
    lambda row: max(row['home_win_probability'], 1 - row['home_win_probability']) - 0.5,
    axis=1
)
margin_bins = pd.cut(predictions_df['win_margin'], bins=10)
margin_accuracy = predictions_df.groupby(margin_bins)['correct'].mean()
margin_count = predictions_df.groupby(margin_bins).size()
margin_labels = [f'{interval.mid:.2f}' for interval in margin_accuracy.index]
ax4_2 = ax4.twinx()
ax4.bar(range(len(margin_accuracy)), margin_accuracy.values, alpha=0.7, color='#06A77D', edgecolor='black', label='Accuracy')
ax4_2.plot(range(len(margin_count)), margin_count.values, 'ro-', linewidth=2, markersize=8, label='Sample Size')
ax4.set_xlabel('Win Probability Margin', fontsize=12, fontweight='bold')
ax4.set_ylabel('Accuracy', fontsize=12, fontweight='bold', color='#06A77D')
ax4_2.set_ylabel('Number of Games', fontsize=12, fontweight='bold', color='red')
ax4.set_title('Accuracy vs Prediction Margin', fontsize=14, fontweight='bold')
ax4.set_xticks(range(len(margin_accuracy)))
ax4.set_xticklabels(margin_labels, rotation=45)
ax4.tick_params(axis='y', labelcolor='#06A77D')
ax4_2.tick_params(axis='y', labelcolor='red')
ax4.grid(True, alpha=0.3)
ax4.legend(loc='upper left')
ax4_2.legend(loc='upper right')

plt.tight_layout()
plt.savefig(output_dir / "1_confidence_analysis.png", dpi=300, bbox_inches='tight')
print(f"✓ Saved: {output_dir / '1_confidence_analysis.png'}\n")
plt.close()

# ============================================================================
# 2. EXPECTED GOALS ANALYSIS
# ============================================================================
print("Creating Visualization 2: Expected Goals Analysis...")

# Aggregate team-level xGoals data
team_xgoals = moneypuck_df[moneypuck_df['situation'] == 'all'].copy()
team_xgoals = team_xgoals.groupby(['team', 'season']).agg({
    'xGoalsFor': 'sum',
    'xGoalsAgainst': 'sum',
    'goalsFor': 'sum',
    'goalsAgainst': 'sum',
    'gameId': 'count'
}).reset_index()
team_xgoals.columns = ['team', 'season', 'xGF', 'xGA', 'GF', 'GA', 'games']

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Expected Goals (xGoals) Analysis', fontsize=20, fontweight='bold', y=0.995)

# xGoals For vs Actual Goals For
ax1 = axes[0, 0]
ax1.scatter(team_xgoals['xGF'], team_xgoals['GF'], alpha=0.6, s=100, c=team_xgoals['season'], cmap='viridis', edgecolors='black')
z = np.polyfit(team_xgoals['xGF'], team_xgoals['GF'], 1)
p = np.poly1d(z)
x_line = np.linspace(team_xgoals['xGF'].min(), team_xgoals['xGF'].max(), 100)
ax1.plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2, label=f'Fit: y={z[0]:.2f}x+{z[1]:.1f}')
ax1.plot(x_line, x_line, "k-", alpha=0.3, linewidth=2, label='Perfect Prediction')
ax1.set_xlabel('Expected Goals For (xGF)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Actual Goals For (GF)', fontsize=12, fontweight='bold')
ax1.set_title('Expected vs Actual Goals Scored', fontsize=14, fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)

# xGoals Against vs Actual Goals Against
ax2 = axes[0, 1]
ax2.scatter(team_xgoals['xGA'], team_xgoals['GA'], alpha=0.6, s=100, c=team_xgoals['season'], cmap='plasma', edgecolors='black')
z2 = np.polyfit(team_xgoals['xGA'], team_xgoals['GA'], 1)
p2 = np.poly1d(z2)
x_line2 = np.linspace(team_xgoals['xGA'].min(), team_xgoals['xGA'].max(), 100)
ax2.plot(x_line2, p2(x_line2), "r--", alpha=0.8, linewidth=2, label=f'Fit: y={z2[0]:.2f}x+{z2[1]:.1f}')
ax2.plot(x_line2, x_line2, "k-", alpha=0.3, linewidth=2, label='Perfect Prediction')
ax2.set_xlabel('Expected Goals Against (xGA)', fontsize=12, fontweight='bold')
ax2.set_ylabel('Actual Goals Against (GA)', fontsize=12, fontweight='bold')
ax2.set_title('Expected vs Actual Goals Allowed', fontsize=14, fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Goal differential: xGoals vs Actual
ax3 = axes[1, 0]
team_xgoals['xGD'] = team_xgoals['xGF'] - team_xgoals['xGA']
team_xgoals['GD'] = team_xgoals['GF'] - team_xgoals['GA']
colors = ['red' if gd < 0 else 'green' for gd in team_xgoals['GD']]
ax3.scatter(team_xgoals['xGD'], team_xgoals['GD'], alpha=0.6, s=100, c=colors, edgecolors='black')
z3 = np.polyfit(team_xgoals['xGD'], team_xgoals['GD'], 1)
p3 = np.poly1d(z3)
x_line3 = np.linspace(team_xgoals['xGD'].min(), team_xgoals['xGD'].max(), 100)
ax3.plot(x_line3, p3(x_line3), "b--", alpha=0.8, linewidth=2, label=f'Fit: y={z3[0]:.2f}x+{z3[1]:.1f}')
ax3.plot(x_line3, x_line3, "k-", alpha=0.3, linewidth=2, label='Perfect Match')
ax3.axhline(0, color='gray', linestyle='--', alpha=0.5)
ax3.axvline(0, color='gray', linestyle='--', alpha=0.5)
ax3.set_xlabel('Expected Goal Differential (xGD)', fontsize=12, fontweight='bold')
ax3.set_ylabel('Actual Goal Differential (GD)', fontsize=12, fontweight='bold')
ax3.set_title('Goal Differential: Expected vs Actual', fontsize=14, fontweight='bold')
ax3.legend()
ax3.grid(True, alpha=0.3)

# Over/Under Performance
ax4 = axes[1, 1]
team_xgoals['over_under'] = team_xgoals['GF'] - team_xgoals['xGF']
team_xgoals_sorted = team_xgoals.nlargest(15, 'over_under')
colors_ou = ['#06A77D' if x > 0 else '#D62839' for x in team_xgoals_sorted['over_under']]
ax4.barh(range(len(team_xgoals_sorted)), team_xgoals_sorted['over_under'], color=colors_ou, edgecolor='black', linewidth=1.5)
ax4.axvline(0, color='black', linestyle='-', linewidth=2)
ax4.set_yticks(range(len(team_xgoals_sorted)))
ax4.set_yticklabels([f"{row['team']} ({row['season']})" for _, row in team_xgoals_sorted.iterrows()], fontsize=10)
ax4.set_xlabel('Goals Over/Under xGoals', fontsize=12, fontweight='bold')
ax4.set_title('Top 15 Teams: Actual Goals vs Expected Goals', fontsize=14, fontweight='bold')
ax4.grid(True, alpha=0.3, axis='x')

plt.tight_layout()
plt.savefig(output_dir / "2_xgoals_analysis.png", dpi=300, bbox_inches='tight')
print(f"✓ Saved: {output_dir / '2_xgoals_analysis.png'}\n")
plt.close()

# ============================================================================
# 3. MODEL PERFORMANCE OVER TIME
# ============================================================================
print("Creating Visualization 3: Model Performance Over Time...")

# Calculate rolling metrics
predictions_df = predictions_df.sort_values('gameDate')
predictions_df['game_number'] = range(len(predictions_df))
window = 50

predictions_df['rolling_accuracy'] = predictions_df['correct'].rolling(window=window, min_periods=1).mean()
predictions_df['rolling_home_accuracy'] = predictions_df['home_win'].rolling(window=window, min_periods=1).mean()

# Calculate Brier score
predictions_df['brier_score'] = (predictions_df['home_win_probability'] - predictions_df['home_win']) ** 2
predictions_df['rolling_brier'] = predictions_df['brier_score'].rolling(window=window, min_periods=1).mean()

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Model Performance Evolution Through Season', fontsize=20, fontweight='bold', y=0.995)

# Accuracy over time
ax1 = axes[0, 0]
ax1.plot(predictions_df['game_number'], predictions_df['rolling_accuracy'], linewidth=2, color='#2E86AB', label='Model Accuracy')
ax1.axhline(0.5, color='red', linestyle='--', alpha=0.5, linewidth=2, label='Random Baseline')
ax1.axhline(predictions_df['correct'].mean(), color='green', linestyle='--', alpha=0.5, linewidth=2, label=f"Season Avg: {predictions_df['correct'].mean():.3f}")
ax1.fill_between(predictions_df['game_number'], 0.5, predictions_df['rolling_accuracy'], 
                  where=(predictions_df['rolling_accuracy'] > 0.5), alpha=0.3, color='green')
ax1.fill_between(predictions_df['game_number'], 0.5, predictions_df['rolling_accuracy'], 
                  where=(predictions_df['rolling_accuracy'] <= 0.5), alpha=0.3, color='red')
ax1.set_xlabel('Game Number', fontsize=12, fontweight='bold')
ax1.set_ylabel('Accuracy', fontsize=12, fontweight='bold')
ax1.set_title(f'Rolling Accuracy (Window={window} games)', fontsize=14, fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.set_ylim(0.3, 0.8)

# Brier score over time
ax2 = axes[0, 1]
ax2.plot(predictions_df['game_number'], predictions_df['rolling_brier'], linewidth=2, color='#A23B72')
ax2.axhline(0.25, color='red', linestyle='--', alpha=0.5, linewidth=2, label='Random Baseline (0.25)')
ax2.axhline(predictions_df['brier_score'].mean(), color='green', linestyle='--', alpha=0.5, linewidth=2, label=f"Season Avg: {predictions_df['brier_score'].mean():.3f}")
ax2.fill_between(predictions_df['game_number'], predictions_df['rolling_brier'], 0.25, 
                  where=(predictions_df['rolling_brier'] < 0.25), alpha=0.3, color='green')
ax2.set_xlabel('Game Number', fontsize=12, fontweight='bold')
ax2.set_ylabel('Brier Score', fontsize=12, fontweight='bold')
ax2.set_title(f'Rolling Brier Score (Window={window} games)', fontsize=14, fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Monthly accuracy
ax3 = axes[1, 0]
predictions_df['month'] = predictions_df['gameDate'].dt.month
monthly_accuracy = predictions_df.groupby('month')['correct'].agg(['mean', 'count'])
monthly_accuracy = monthly_accuracy[monthly_accuracy['count'] > 10]  # Filter months with enough games
month_names = {10: 'Oct', 11: 'Nov', 12: 'Dec', 1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun'}
month_labels = [month_names.get(m, str(m)) for m in monthly_accuracy.index]
colors_monthly = plt.cm.RdYlGn(monthly_accuracy['mean'].values)
bars = ax3.bar(range(len(monthly_accuracy)), monthly_accuracy['mean'], color=colors_monthly, edgecolor='black', linewidth=1.5)
ax3.axhline(predictions_df['correct'].mean(), color='blue', linestyle='--', alpha=0.5, linewidth=2, label='Season Avg')
ax3.set_xlabel('Month', fontsize=12, fontweight='bold')
ax3.set_ylabel('Accuracy', fontsize=12, fontweight='bold')
ax3.set_title('Model Accuracy by Month', fontsize=14, fontweight='bold')
ax3.set_xticks(range(len(monthly_accuracy)))
ax3.set_xticklabels(month_labels)
ax3.set_ylim(0, 1)
ax3.legend()
ax3.grid(True, alpha=0.3, axis='y')
# Add value labels on bars
for i, (idx, row) in enumerate(monthly_accuracy.iterrows()):
    ax3.text(i, row['mean'] + 0.02, f"{row['mean']:.3f}\n(n={int(row['count'])})", 
             ha='center', va='bottom', fontsize=9, fontweight='bold')

# Cumulative performance metrics
ax4 = axes[1, 1]
predictions_df['cumulative_accuracy'] = predictions_df['correct'].expanding().mean()
predictions_df['cumulative_brier'] = predictions_df['brier_score'].expanding().mean()
ax4_2 = ax4.twinx()
ax4.plot(predictions_df['game_number'], predictions_df['cumulative_accuracy'], 
         linewidth=2.5, color='#06A77D', label='Cumulative Accuracy')
ax4_2.plot(predictions_df['game_number'], predictions_df['cumulative_brier'], 
           linewidth=2.5, color='#F18F01', label='Cumulative Brier Score')
ax4.axhline(0.5, color='gray', linestyle='--', alpha=0.3)
ax4.set_xlabel('Game Number', fontsize=12, fontweight='bold')
ax4.set_ylabel('Cumulative Accuracy', fontsize=12, fontweight='bold', color='#06A77D')
ax4_2.set_ylabel('Cumulative Brier Score', fontsize=12, fontweight='bold', color='#F18F01')
ax4.set_title('Cumulative Performance Metrics', fontsize=14, fontweight='bold')
ax4.tick_params(axis='y', labelcolor='#06A77D')
ax4_2.tick_params(axis='y', labelcolor='#F18F01')
ax4.legend(loc='upper left')
ax4_2.legend(loc='upper right')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / "3_performance_over_time.png", dpi=300, bbox_inches='tight')
print(f"✓ Saved: {output_dir / '3_performance_over_time.png'}\n")
plt.close()

# ============================================================================
# 4. TEAM PERFORMANCE HEATMAP
# ============================================================================
print("Creating Visualization 4: Team Performance Heatmap...")

# Calculate team-specific metrics
team_metrics_home = predictions_df.groupby('teamFullName_home').agg({
    'home_win_probability': 'mean',
    'home_win': 'mean',
    'correct': 'mean',
    'gameId': 'count'
}).rename(columns={'home_win_probability': 'avg_pred_prob', 'home_win': 'actual_win_rate', 
                   'correct': 'model_accuracy', 'gameId': 'games'})

team_metrics_away = predictions_df.groupby('teamFullName_away').agg({
    'home_win_probability': lambda x: (1 - x).mean(),
    'home_win': lambda x: (1 - x).mean(),
    'correct': 'mean',
    'gameId': 'count'
}).rename(columns={'home_win_probability': 'avg_pred_prob', 'home_win': 'actual_win_rate', 
                   'correct': 'model_accuracy', 'gameId': 'games'})

# Combine home and away
team_metrics = pd.DataFrame({
    'avg_pred_prob': (team_metrics_home['avg_pred_prob'] * team_metrics_home['games'] + 
                      team_metrics_away['avg_pred_prob'] * team_metrics_away['games']) / 
                     (team_metrics_home['games'] + team_metrics_away['games']),
    'actual_win_rate': (team_metrics_home['actual_win_rate'] * team_metrics_home['games'] + 
                        team_metrics_away['actual_win_rate'] * team_metrics_away['games']) / 
                       (team_metrics_home['games'] + team_metrics_away['games']),
    'model_accuracy': (team_metrics_home['model_accuracy'] * team_metrics_home['games'] + 
                       team_metrics_away['model_accuracy'] * team_metrics_away['games']) / 
                      (team_metrics_home['games'] + team_metrics_away['games']),
    'games': team_metrics_home['games'] + team_metrics_away['games']
})

# Filter teams with enough games
team_metrics = team_metrics[team_metrics['games'] >= 10].sort_values('actual_win_rate', ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(18, 10))
fig.suptitle('Team Performance Analysis', fontsize=20, fontweight='bold')

# Heatmap of key metrics
ax1 = axes[0]
heatmap_data = team_metrics[['avg_pred_prob', 'actual_win_rate', 'model_accuracy']].T
sns.heatmap(heatmap_data, annot=True, fmt='.3f', cmap='RdYlGn', center=0.5, 
            ax=ax1, cbar_kws={'label': 'Value'}, linewidths=0.5, linecolor='black')
ax1.set_xlabel('Team', fontsize=12, fontweight='bold')
ax1.set_ylabel('Metric', fontsize=12, fontweight='bold')
ax1.set_title('Team Performance Metrics Heatmap', fontsize=14, fontweight='bold')
ax1.set_xticklabels([name.split()[-1] for name in team_metrics.index], rotation=45, ha='right')
ax1.set_yticklabels(['Avg Predicted\nWin Prob', 'Actual\nWin Rate', 'Model\nAccuracy'], rotation=0)

# Predicted vs Actual Win Rate
ax2 = axes[1]
scatter = ax2.scatter(team_metrics['avg_pred_prob'], team_metrics['actual_win_rate'], 
                     s=team_metrics['games']*3, alpha=0.6, c=team_metrics['model_accuracy'], 
                     cmap='RdYlGn', edgecolors='black', linewidth=1.5, vmin=0.3, vmax=0.7)
ax2.plot([0, 1], [0, 1], 'k--', alpha=0.3, linewidth=2, label='Perfect Calibration')
for idx, row in team_metrics.iterrows():
    team_abbrev = idx.split()[-1][:3].upper()
    ax2.annotate(team_abbrev, (row['avg_pred_prob'], row['actual_win_rate']), 
                fontsize=8, ha='center', va='center', fontweight='bold')
ax2.set_xlabel('Average Predicted Win Probability', fontsize=12, fontweight='bold')
ax2.set_ylabel('Actual Win Rate', fontsize=12, fontweight='bold')
ax2.set_title('Team Calibration: Predicted vs Actual Win Rates', fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.legend()
cbar = plt.colorbar(scatter, ax=ax2)
cbar.set_label('Model Accuracy', fontsize=11, fontweight='bold')
ax2.set_xlim(0.25, 0.75)
ax2.set_ylim(0.25, 0.75)

plt.tight_layout()
plt.savefig(output_dir / "4_team_heatmap.png", dpi=300, bbox_inches='tight')
print(f"✓ Saved: {output_dir / '4_team_heatmap.png'}\n")
plt.close()

# ============================================================================
# 5. HOME VS AWAY ADVANTAGE ANALYSIS
# ============================================================================
print("Creating Visualization 5: Home vs Away Advantage...")

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Home Ice Advantage Analysis', fontsize=20, fontweight='bold', y=0.995)

# Overall home win rate
ax1 = axes[0, 0]
home_stats = pd.DataFrame({
    'Predicted': [predictions_df['home_win_probability'].mean(), 1 - predictions_df['home_win_probability'].mean()],
    'Actual': [predictions_df['home_win'].mean(), 1 - predictions_df['home_win'].mean()]
}, index=['Home Win Rate', 'Away Win Rate'])
home_stats.plot(kind='bar', ax=ax1, color=['#2E86AB', '#A23B72'], edgecolor='black', linewidth=1.5, width=0.7)
ax1.axhline(0.5, color='gray', linestyle='--', alpha=0.5, linewidth=2)
ax1.set_ylabel('Win Rate', fontsize=12, fontweight='bold')
ax1.set_title('Home vs Away: Predicted vs Actual Win Rates', fontsize=14, fontweight='bold')
ax1.set_xticklabels(home_stats.index, rotation=0)
ax1.legend(title='Type', fontsize=11)
ax1.grid(True, alpha=0.3, axis='y')
ax1.set_ylim(0, 0.7)
# Add value labels
for container in ax1.containers:
    ax1.bar_label(container, fmt='%.3f', fontweight='bold')

# Home advantage by team
ax2 = axes[0, 1]
team_home_adv = predictions_df.groupby('teamFullName_home').agg({
    'home_win': 'mean',
    'gameId': 'count'
}).rename(columns={'home_win': 'home_win_rate', 'gameId': 'games'})
team_home_adv = team_home_adv[team_home_adv['games'] >= 5].sort_values('home_win_rate', ascending=True)
top_bottom = pd.concat([team_home_adv.head(10), team_home_adv.tail(10)])
colors_ha = ['#D62839' if x < 0.5 else '#06A77D' for x in top_bottom['home_win_rate']]
ax2.barh(range(len(top_bottom)), top_bottom['home_win_rate'], color=colors_ha, edgecolor='black', linewidth=1.5)
ax2.axvline(0.5, color='black', linestyle='--', linewidth=2)
ax2.set_yticks(range(len(top_bottom)))
ax2.set_yticklabels([name.split()[-1] for name in top_bottom.index], fontsize=10)
ax2.set_xlabel('Home Win Rate', fontsize=12, fontweight='bold')
ax2.set_title('Home Win Rate by Team (Top & Bottom 10)', fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3, axis='x')

# Model confidence: Home vs Away
ax3 = axes[1, 0]
predictions_df['predicted_home'] = predictions_df['home_win_probability'] > 0.5
predictions_df['predicted_away'] = predictions_df['home_win_probability'] <= 0.5
home_pred_accuracy = predictions_df[predictions_df['predicted_home']]['correct'].mean()
away_pred_accuracy = predictions_df[predictions_df['predicted_away']]['correct'].mean()
confidence_stats = pd.DataFrame({
    'Accuracy': [home_pred_accuracy, away_pred_accuracy],
    'Count': [predictions_df['predicted_home'].sum(), predictions_df['predicted_away'].sum()]
}, index=['Model Predicts\nHome Win', 'Model Predicts\nAway Win'])
ax3_2 = ax3.twinx()
ax3.bar([0, 1], confidence_stats['Accuracy'], color=['#2E86AB', '#A23B72'], 
        edgecolor='black', linewidth=1.5, alpha=0.7, width=0.6)
ax3_2.plot([0, 1], confidence_stats['Count'], 'ro-', linewidth=3, markersize=12, label='Sample Size')
ax3.axhline(0.5, color='gray', linestyle='--', alpha=0.5)
ax3.set_ylabel('Prediction Accuracy', fontsize=12, fontweight='bold', color='black')
ax3_2.set_ylabel('Number of Predictions', fontsize=12, fontweight='bold', color='red')
ax3.set_title('Model Accuracy: Home vs Away Predictions', fontsize=14, fontweight='bold')
ax3.set_xticks([0, 1])
ax3.set_xticklabels(confidence_stats.index)
ax3.set_ylim(0, 1)
ax3.grid(True, alpha=0.3, axis='y')
ax3_2.tick_params(axis='y', labelcolor='red')
ax3_2.legend()
# Add value labels
for i, (acc, cnt) in enumerate(zip(confidence_stats['Accuracy'], confidence_stats['Count'])):
    ax3.text(i, acc + 0.03, f'{acc:.3f}', ha='center', va='bottom', fontsize=11, fontweight='bold')

# Home advantage over time (by month)
ax4 = axes[1, 1]
monthly_home_adv = predictions_df.groupby('month').agg({
    'home_win': 'mean',
    'home_win_probability': 'mean',
    'gameId': 'count'
})
monthly_home_adv = monthly_home_adv[monthly_home_adv['gameId'] > 10]
month_labels_ha = [month_names.get(m, str(m)) for m in monthly_home_adv.index]
x_months = range(len(monthly_home_adv))
width_ha = 0.35
ax4.bar([x - width_ha/2 for x in x_months], monthly_home_adv['home_win_probability'], 
        width_ha, label='Predicted', alpha=0.8, color='#F18F01', edgecolor='black')
ax4.bar([x + width_ha/2 for x in x_months], monthly_home_adv['home_win'], 
        width_ha, label='Actual', alpha=0.8, color='#06A77D', edgecolor='black')
ax4.axhline(0.5, color='gray', linestyle='--', alpha=0.5, linewidth=2)
ax4.set_xlabel('Month', fontsize=12, fontweight='bold')
ax4.set_ylabel('Home Win Probability', fontsize=12, fontweight='bold')
ax4.set_title('Home Win Rate by Month', fontsize=14, fontweight='bold')
ax4.set_xticks(x_months)
ax4.set_xticklabels(month_labels_ha)
ax4.legend()
ax4.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(output_dir / "5_home_advantage.png", dpi=300, bbox_inches='tight')
print(f"✓ Saved: {output_dir / '5_home_advantage.png'}\n")
plt.close()

# ============================================================================
# 6. ADVANCED STATISTICS CORRELATION
# ============================================================================
print("Creating Visualization 6: Advanced Statistics Correlation...")

# Sample recent games for correlation analysis
recent_games = moneypuck_df[
    (moneypuck_df['situation'] == 'all') & 
    (moneypuck_df['season'] >= 2020)
].copy()

# Calculate per-game stats
recent_games['xG_diff'] = recent_games['xGoalsFor'] - recent_games['xGoalsAgainst']
recent_games['goal_diff'] = recent_games['goalsFor'] - recent_games['goalsAgainst']
recent_games['shot_diff'] = recent_games['shotsOnGoalFor'] - recent_games['shotsOnGoalAgainst']
recent_games['win'] = (recent_games['goalsFor'] > recent_games['goalsAgainst']).astype(int)

# Select key metrics
metrics_cols = ['xGoalsPercentage', 'corsiPercentage', 'fenwickPercentage', 
                'highDangerShotsFor', 'faceOffsWonFor', 'win']
correlation_data = recent_games[metrics_cols].corr()

fig, axes = plt.subplots(2, 2, figsize=(16, 14))
fig.suptitle('Advanced Hockey Statistics Analysis', fontsize=20, fontweight='bold', y=0.995)

# Correlation heatmap
ax1 = axes[0, 0]
mask = np.triu(np.ones_like(correlation_data, dtype=bool), k=1)
sns.heatmap(correlation_data, mask=mask, annot=True, fmt='.3f', cmap='coolwarm', 
            center=0, ax=ax1, square=True, linewidths=1, cbar_kws={'label': 'Correlation'},
            vmin=-0.5, vmax=1.0)
ax1.set_title('Correlation Matrix: Advanced Stats vs Winning', fontsize=14, fontweight='bold')
ax1.set_xticklabels(['xG%', 'Corsi%', 'Fenwick%', 'HD Shots', 'Faceoffs', 'Win'], rotation=45, ha='right')
ax1.set_yticklabels(['xG%', 'Corsi%', 'Fenwick%', 'HD Shots', 'Faceoffs', 'Win'], rotation=0)

# Possession metrics (Corsi vs Fenwick)
ax2 = axes[0, 1]
sample = recent_games.sample(min(1000, len(recent_games)))
colors_poss = ['#06A77D' if w == 1 else '#D62839' for w in sample['win']]
ax2.scatter(sample['corsiPercentage'], sample['fenwickPercentage'], 
           alpha=0.5, s=50, c=colors_poss, edgecolors='black', linewidth=0.5)
ax2.plot([0, 100], [0, 100], 'k--', alpha=0.3, linewidth=2)
ax2.set_xlabel('Corsi For %', fontsize=12, fontweight='bold')
ax2.set_ylabel('Fenwick For %', fontsize=12, fontweight='bold')
ax2.set_title('Possession Metrics Relationship', fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.legend(handles=[plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#06A77D', markersize=10, label='Win'),
                   plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#D62839', markersize=10, label='Loss')],
          loc='upper left')

# xGoals % vs Win Rate
ax3 = axes[1, 0]
xg_bins = pd.cut(recent_games['xGoalsPercentage'], bins=20)
xg_win_rate = recent_games.groupby(xg_bins)['win'].agg(['mean', 'count'])
xg_win_rate = xg_win_rate[xg_win_rate['count'] >= 20]
xg_labels = [f'{interval.mid:.1f}' for interval in xg_win_rate.index]
colors_xg = plt.cm.RdYlGn(xg_win_rate['mean'].values)
ax3.bar(range(len(xg_win_rate)), xg_win_rate['mean'], color=colors_xg, edgecolor='black', linewidth=1.5)
ax3.axhline(0.5, color='black', linestyle='--', linewidth=2, alpha=0.5)
ax3.set_xlabel('Expected Goals For % (xGF%)', fontsize=12, fontweight='bold')
ax3.set_ylabel('Win Rate', fontsize=12, fontweight='bold')
ax3.set_title('Win Rate by Expected Goals Percentage', fontsize=14, fontweight='bold')
ax3.set_xticks(range(len(xg_win_rate)))
ax3.set_xticklabels(xg_labels, rotation=45, ha='right')
ax3.set_ylim(0, 1)
ax3.grid(True, alpha=0.3, axis='y')

# High Danger Shots impact
ax4 = axes[1, 1]
recent_games['hd_shot_diff'] = recent_games['highDangerShotsFor'] - recent_games['highDangerShotsAgainst']
hd_bins = pd.cut(recent_games['hd_shot_diff'], bins=15)
hd_impact = recent_games.groupby(hd_bins).agg({'win': 'mean', 'goal_diff': 'mean', 'gameId': 'count'})
hd_impact = hd_impact[hd_impact['gameId'] >= 20]
hd_labels = [f'{interval.mid:.0f}' for interval in hd_impact.index]
ax4_2 = ax4.twinx()
ax4.bar(range(len(hd_impact)), hd_impact['win'], alpha=0.7, color='#2E86AB', 
        edgecolor='black', linewidth=1.5, label='Win Rate')
ax4_2.plot(range(len(hd_impact)), hd_impact['goal_diff'], 'ro-', linewidth=2.5, 
          markersize=8, label='Avg Goal Diff')
ax4.axhline(0.5, color='gray', linestyle='--', alpha=0.5)
ax4_2.axhline(0, color='gray', linestyle='--', alpha=0.5)
ax4.set_xlabel('High Danger Shot Differential', fontsize=12, fontweight='bold')
ax4.set_ylabel('Win Rate', fontsize=12, fontweight='bold', color='#2E86AB')
ax4_2.set_ylabel('Average Goal Differential', fontsize=12, fontweight='bold', color='red')
ax4.set_title('Impact of High Danger Shots on Winning', fontsize=14, fontweight='bold')
ax4.set_xticks(range(len(hd_impact)))
ax4.set_xticklabels(hd_labels, rotation=45, ha='right')
ax4.tick_params(axis='y', labelcolor='#2E86AB')
ax4_2.tick_params(axis='y', labelcolor='red')
ax4.legend(loc='upper left')
ax4_2.legend(loc='upper right')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / "6_advanced_stats_correlation.png", dpi=300, bbox_inches='tight')
print(f"✓ Saved: {output_dir / '6_advanced_stats_correlation.png'}\n")
plt.close()

# ============================================================================
# GENERATE SUMMARY REPORT
# ============================================================================
print("Generating summary report...")

summary_text = f"""
NHL PREDICTION MODEL - VISUALIZATION SUMMARY
============================================

DATA OVERVIEW:
- Total predictions analyzed: {len(predictions_df):,}
- Date range: {predictions_df['gameDate'].min().strftime('%Y-%m-%d')} to {predictions_df['gameDate'].max().strftime('%Y-%m-%d')}
- MoneyPuck data: {len(moneypuck_df):,} records

MODEL PERFORMANCE:
- Overall Accuracy: {predictions_df['correct'].mean():.3f} ({predictions_df['correct'].mean()*100:.1f}%)
- Brier Score: {predictions_df['brier_score'].mean():.4f}
- Games where model was correct: {predictions_df['correct'].sum():,} / {len(predictions_df):,}

HOME/AWAY ANALYSIS:
- Predicted home win rate: {predictions_df['home_win_probability'].mean():.3f}
- Actual home win rate: {predictions_df['home_win'].mean():.3f}
- Model accuracy on home predictions: {predictions_df[predictions_df['predicted_home']]['correct'].mean():.3f}
- Model accuracy on away predictions: {predictions_df[predictions_df['predicted_away']]['correct'].mean():.3f}

CONFIDENCE ANALYSIS:
- Average model confidence: {confidence.mean():.3f}
- High confidence games (>0.7): {(confidence > 0.7).sum():,}
- Low confidence games (<0.3): {(confidence < 0.3).sum():,}

VISUALIZATIONS CREATED:
1. Prediction Confidence vs Accuracy Analysis
   - Confidence distribution, binned accuracy, calibration curves, margin analysis
   
2. Expected Goals (xGoals) Analysis
   - xGF vs actual goals, xGA vs actual goals, goal differentials, over/under performance
   
3. Model Performance Over Time
   - Rolling accuracy, Brier score evolution, monthly patterns, cumulative metrics
   
4. Team Performance Heatmap
   - Team-level metrics, predicted vs actual win rates, calibration by team
   
5. Home Ice Advantage Analysis
   - Home/away win rates, team-specific advantages, model prediction accuracy, monthly trends
   
6. Advanced Statistics Correlation
   - Correlation matrix, possession metrics, xGoals impact, high danger shots analysis

All visualizations saved to: {output_dir.absolute()}
"""

with open(output_dir / "VISUALIZATION_SUMMARY.txt", "w") as f:
    f.write(summary_text)

print(summary_text)
print(f"\n{'='*70}")
print("✓ ALL VISUALIZATIONS CREATED SUCCESSFULLY!")
print(f"{'='*70}")
print(f"\nCheck the '{output_dir}' folder for all generated images.\n")

