#!/bin/bash
# Automated post-training deployment script
# Run this after train_optimal.py completes successfully

set -e  # Exit on error

echo "=================================="
echo "POST-TRAINING DEPLOYMENT"
echo "=================================="
echo ""

# Check if training completed successfully
if [ ! -f "reports/predictions_20232024.csv" ]; then
    echo "❌ Error: predictions file not found!"
    echo "Training may not have completed successfully."
    exit 1
fi

# Check file was recently modified (within last hour)
if [ $(find reports/predictions_20232024.csv -mmin -60 | wc -l) -eq 0 ]; then
    echo "⚠️  Warning: Predictions file is old (>1 hour)"
    echo "Training may not have completed. Continue anyway? (y/n)"
    read -r response
    if [ "$response" != "y" ]; then
        exit 1
    fi
fi

echo "✅ Training outputs found"
echo ""

# Step 1: Calculate actual accuracy from predictions
echo "[1/4] Calculating model accuracy..."
ACCURACY=$(python3 -c "
import pandas as pd
df = pd.read_csv('reports/predictions_20232024.csv')
acc = df['correct'].mean()
print(f'{acc:.4f} ({acc*100:.2f}%)')
")
echo "   Test Accuracy: $ACCURACY"
echo ""

# Step 2: Generate model insights
echo "[2/4] Generating model insights for website..."
python scripts/generate_site_metrics.py
echo "   ✅ web/src/data/modelInsights.json updated"
echo ""

# Step 3: Verify JSON is valid
echo "[3/4] Validating generated JSON..."
python3 -c "
import json
with open('web/src/data/modelInsights.json') as f:
    data = json.load(f)
    print(f'   Overall accuracy: {data[\"overall\"][\"accuracy\"]*100:.2f}%')
    print(f'   Games: {data[\"overall\"][\"games\"]}')
    print(f'   Generated: {data[\"generatedAt\"]}')
"
echo "   ✅ JSON valid"
echo ""

# Step 4: Show git status
echo "[4/4] Git status..."
git status --short | grep -E "predictions|model.*pkl|modelInsights" || echo "   No changes detected"
echo ""

echo "=================================="
echo "DEPLOYMENT READY"
echo "=================================="
echo ""
echo "Next steps:"
echo "  1. Review changes: git diff web/src/data/modelInsights.json"
echo "  2. Commit: git add reports/ model*.pkl web/src/data/"
echo "  3. git commit -m \"Deploy V6.0 model with $ACCURACY accuracy\""
echo "  4. Push: git push"
echo "  5. Create PR to main for Vercel deployment"
echo ""
