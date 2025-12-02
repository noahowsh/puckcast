#!/usr/bin/env python3
"""
Analyze existing predictions CSV to generate comprehensive statistics.
Works without dependencies by using basic Python only.
"""
import csv
import math
from collections import defaultdict

print("=" * 80)
print("COMPREHENSIVE MODEL EVALUATION - NHL API ONLY")
print("Analyzing existing predictions from reports/predictions_20232024.csv")
print("=" * 80)
print()

# Load predictions
predictions = []
with open('reports/predictions_20232024.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        predictions.append({
            'actual': int(row['home_win']),
            'prob_home': float(row['home_win_probability']),
            'predicted': int(row['predicted_home_win']),
            'correct': int(row['correct'])
        })

total_games = len(predictions)
print(f"Total test games loaded: {total_games}")
print()

# ============================================================================
# Overall Metrics
# ============================================================================
print("=" * 80)
print("📊 OVERALL PERFORMANCE")
print("=" * 80)

correct = sum(p['correct'] for p in predictions)
accuracy = correct / total_games
baseline_acc = sum(p['actual'] for p in predictions) / total_games

# ROC-AUC calculation
def calculate_roc_auc(predictions):
    """Calculate ROC-AUC score."""
    # Sort by predicted probability
    sorted_preds = sorted(predictions, key=lambda x: x['prob_home'], reverse=True)

    # Count positives and negatives
    num_pos = sum(p['actual'] for p in predictions)
    num_neg = total_games - num_pos

    # Calculate AUC using trapezoidal rule
    tp = 0
    fp = 0
    auc = 0.0
    prev_fp = 0

    for p in sorted_preds:
        if p['actual'] == 1:
            tp += 1
        else:
            fp += 1
            auc += tp

    if num_pos > 0 and num_neg > 0:
        auc = auc / (num_pos * num_neg)
    else:
        auc = 0.5

    return auc

roc_auc = calculate_roc_auc(predictions)

# Log Loss
def calculate_log_loss(predictions):
    """Calculate log loss."""
    eps = 1e-15
    log_loss_sum = 0.0
    for p in predictions:
        prob = max(eps, min(1 - eps, p['prob_home']))
        if p['actual'] == 1:
            log_loss_sum -= math.log(prob)
        else:
            log_loss_sum -= math.log(1 - prob)
    return log_loss_sum / len(predictions)

log_loss_val = calculate_log_loss(predictions)

# Brier Score
def calculate_brier_score(predictions):
    """Calculate Brier score."""
    brier_sum = 0.0
    for p in predictions:
        brier_sum += (p['prob_home'] - p['actual']) ** 2
    return brier_sum / len(predictions)

brier_score = calculate_brier_score(predictions)

print(f"{'Metric':<25} {'Test':<15} {'Baseline':<15}")
print("-" * 80)
print(f"{'Accuracy':<25} {accuracy:>14.2%} {baseline_acc:>14.2%}")
print(f"{'ROC-AUC':<25} {roc_auc:>14.4f} {'0.5000':>15}")
print(f"{'Log Loss':<25} {log_loss_val:>14.4f} {'-':>15}")
print(f"{'Brier Score':<25} {brier_score:>14.4f} {'-':>15}")
print(f"{'Improvement vs Baseline':<25} {accuracy - baseline_acc:>+13.2%} {'-':>15}")
print(f"{'Correct Predictions':<25} {correct:>14} / {total_games}")
print()

# ============================================================================
# Confidence Bucket Analysis
# ============================================================================
print("=" * 80)
print("📈 CONFIDENCE BUCKET ANALYSIS")
print("=" * 80)
print()

def assign_confidence_grade(prob):
    """Assign confidence grade based on probability distance from 0.5"""
    edge = abs(prob - 0.5) * 100

    if edge >= 20:
        return "A+"
    elif edge >= 17:
        return "A"
    elif edge >= 14:
        return "A-"
    elif edge >= 10:
        return "B+"
    elif edge >= 7:
        return "B"
    elif edge >= 4:
        return "B-"
    elif edge >= 2:
        return "C+"
    else:
        return "C"

# Assign grades
for p in predictions:
    p['grade'] = assign_confidence_grade(p['prob_home'])
    p['edge'] = abs(p['prob_home'] - 0.5) * 100

# Calculate bucket statistics
buckets = defaultdict(lambda: {'games': 0, 'correct': 0, 'edge_sum': 0.0, 'prob_sum': 0.0})
grade_order = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C"]

for p in predictions:
    grade = p['grade']
    buckets[grade]['games'] += 1
    buckets[grade]['correct'] += p['correct']
    buckets[grade]['edge_sum'] += p['edge']
    buckets[grade]['prob_sum'] += p['prob_home']

print(f"{'Grade':<8} {'Games':<8} {'Correct':<10} {'Accuracy':<12} {'Avg Edge':<12}")
print("-" * 80)

for grade in grade_order:
    if buckets[grade]['games'] == 0:
        continue

    games = buckets[grade]['games']
    correct_count = buckets[grade]['correct']
    accuracy_pct = correct_count / games if games > 0 else 0
    avg_edge = buckets[grade]['edge_sum'] / games if games > 0 else 0

    print(f"{grade:<8} {games:<8} {correct_count:<10} {accuracy_pct:>10.2%}  {avg_edge:>10.1f}%")

print()

# High confidence summary
high_confidence_grades = ['A+', 'A', 'A-']
high_conf_games = sum(buckets[g]['games'] for g in high_confidence_grades if g in buckets)
high_conf_correct = sum(buckets[g]['correct'] for g in high_confidence_grades if g in buckets)
high_conf_acc = high_conf_correct / high_conf_games if high_conf_games > 0 else 0

print(f"High Confidence (A+/A/A-): {high_conf_games} games, {high_conf_acc:.2%} accuracy")
print()

# ============================================================================
# Probability Distribution Analysis
# ============================================================================
print("=" * 80)
print("📊 PROBABILITY DISTRIBUTION")
print("=" * 80)
print()

# Bin predictions into 10 buckets
prob_bins = defaultdict(lambda: {'count': 0, 'actual_wins': 0})
for p in predictions:
    bin_idx = min(9, int(p['prob_home'] * 10))
    prob_bins[bin_idx]['count'] += 1
    prob_bins[bin_idx]['actual_wins'] += p['actual']

print(f"{'Prob Range':<20} {'Predicted':<15} {'Actual':<15} {'Count':<10} {'Cal Error':<15}")
print("-" * 80)

calibration_errors = []
for i in range(10):
    if prob_bins[i]['count'] == 0:
        continue

    count = prob_bins[i]['count']
    actual_freq = prob_bins[i]['actual_wins'] / count
    predicted_prob = (i + 0.5) / 10  # Midpoint of bin
    error = abs(predicted_prob - actual_freq)
    calibration_errors.append(error)

    prob_range = f"{i/10:.1f} - {(i+1)/10:.1f}"
    print(f"{prob_range:<20} {predicted_prob:>13.1%}  {actual_freq:>13.1%}  {count:>8}  {error:>13.1%}")

avg_calibration_error = sum(calibration_errors) / len(calibration_errors) if calibration_errors else 0
print()
print(f"Average Calibration Error: {avg_calibration_error:.4f}")
print()

# ============================================================================
# Edge Analysis
# ============================================================================
print("=" * 80)
print("💰 EDGE ANALYSIS (Betting Value)")
print("=" * 80)
print()

# Group by edge magnitude
edge_ranges = [
    (0, 5, "0-5%"),
    (5, 10, "5-10%"),
    (10, 15, "10-15%"),
    (15, 20, "15-20%"),
    (20, 100, "20%+")
]

print(f"{'Edge Range':<15} {'Games':<8} {'Correct':<10} {'Accuracy':<12} {'Avg Edge':<12}")
print("-" * 80)

for min_edge, max_edge, label in edge_ranges:
    edge_preds = [p for p in predictions if min_edge <= p['edge'] < max_edge]
    if not edge_preds:
        continue

    games = len(edge_preds)
    correct_count = sum(p['correct'] for p in edge_preds)
    accuracy_pct = correct_count / games if games > 0 else 0
    avg_edge = sum(p['edge'] for p in edge_preds) / games if games > 0 else 0

    print(f"{label:<15} {games:<8} {correct_count:<10} {accuracy_pct:>10.2%}  {avg_edge:>10.1f}%")

print()

# ============================================================================
# Summary
# ============================================================================
print("=" * 80)
print("✅ SUMMARY - NHL API ONLY MODEL")
print("=" * 80)
print()
print("DATA SOURCE:")
print("  - Native NHL API play-by-play ingestion")
print("  - Custom xG model (gradient boosting)")
print("  - NO MoneyPuck dependency")
print()
print("MODEL PERFORMANCE:")
print(f"  - Test Accuracy: {accuracy:.2%} (baseline: {baseline_acc:.2%})")
print(f"  - Improvement: +{(accuracy - baseline_acc)*100:.2f} percentage points")
print(f"  - ROC-AUC: {roc_auc:.4f}")
print(f"  - Log Loss: {log_loss_val:.4f}")
print(f"  - Brier Score: {brier_score:.4f}")
print()
print("TOP CONFIDENCE PREDICTIONS:")
print(f"  - A+/A/A- Grades: {high_conf_games} games, {high_conf_acc:.2%} accuracy")
print()
print("CALIBRATION:")
print(f"  - Average Calibration Error: {avg_calibration_error:.4f}")
print()
print("=" * 80)
print("Analysis complete!")
print("=" * 80)
