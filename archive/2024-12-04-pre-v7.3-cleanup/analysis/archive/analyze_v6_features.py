"""
Analyze V6.3 model feature importance to guide V7.0 pruning.

Generates feature importance report showing:
- Top 20 most important features
- Bottom 20 least important features
- Features recommended for pruning
- Core features to preserve
"""

import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from src.nhl_prediction.feature_pruning import (
    analyze_feature_importance,
    get_pruned_features,
    V7_CORE_FEATURES,
    V7_KEEP_PATTERNS
)

PROJECT_ROOT = Path(__file__).parent
MODEL_PATH = PROJECT_ROOT / "model_v6_nhl_api.pkl"
OUTPUT_PATH = PROJECT_ROOT / "reports" / "v6_feature_importance.csv"

def main():
    print("=" * 80)
    print("V6.3 Feature Importance Analysis")
    print("=" * 80)

    # Load current model
    print(f"\nLoading model from: {MODEL_PATH}")
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)

    # Extract feature names from pipeline
    # Model is a Pipeline with preprocessor and clf
    feature_names = model.named_steps['preprocessor'].get_feature_names_out()
    print(f"Total features in V6.3 model: {len(feature_names)}")

    # Analyze importance
    print("\nAnalyzing feature importance...")
    importance_df = analyze_feature_importance(
        model=model,
        feature_names=list(feature_names),
        threshold=0.05  # Features below 0.05 coefficient considered weak
    )

    # Get pruning recommendations
    pruned_features, removed_features = get_pruned_features(
        importance_df=importance_df,
        percentile_threshold=20  # Remove bottom 20%
    )

    print(f"\nFeatures to keep: {len(pruned_features)}")
    print(f"Features to remove: {len(removed_features)}")
    print(f"Reduction: {len(removed_features) / len(feature_names) * 100:.1f}%")

    # Display top features
    print("\n" + "=" * 80)
    print("TOP 20 MOST IMPORTANT FEATURES")
    print("=" * 80)
    top_20 = importance_df.nlargest(20, 'abs_importance')
    for idx, row in top_20.iterrows():
        keep_reason = ""
        if row['feature'] in V7_CORE_FEATURES:
            keep_reason = " [CORE]"
        elif any(pattern in row['feature'] for pattern in V7_KEEP_PATTERNS):
            keep_reason = " [PATTERN]"

        print(f"{row['feature']:50s} {row['coefficient']:8.4f} {keep_reason}")

    # Display bottom features
    print("\n" + "=" * 80)
    print("BOTTOM 20 LEAST IMPORTANT FEATURES")
    print("=" * 80)
    bottom_20 = importance_df.nsmallest(20, 'abs_importance')
    for idx, row in bottom_20.iterrows():
        prune = "PRUNE" if not row['keep'] else "KEEP"
        print(f"{row['feature']:50s} {row['abs_importance']:8.4f} [{prune}]")

    # Save full report
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    importance_df.to_csv(OUTPUT_PATH, index=False)
    print(f"\n✓ Full report saved to: {OUTPUT_PATH}")

    # Summary stats
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Mean coefficient (abs): {importance_df['abs_importance'].mean():.4f}")
    print(f"Median coefficient (abs): {importance_df['abs_importance'].median():.4f}")
    print(f"Max coefficient (abs): {importance_df['abs_importance'].max():.4f}")
    print(f"Min coefficient (abs): {importance_df['abs_importance'].min():.4f}")

    # Core features status
    core_in_model = [f for f in V7_CORE_FEATURES if f in feature_names]
    print(f"\nCore features in model: {len(core_in_model)}/{len(V7_CORE_FEATURES)}")

    missing_core = V7_CORE_FEATURES - set(feature_names)
    if missing_core:
        print(f"\nMissing core features:")
        for f in missing_core:
            print(f"  - {f}")

    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
