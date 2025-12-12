#!/usr/bin/env python3
"""
Repository Organization Script

Moves files to clean directory structure:
- training/ for training scripts
- analysis/current for current analysis
- analysis/archive for old analysis
- prediction/ for prediction scripts
- goalie_system/ for goalie infrastructure
- docs/experiments for experiment docs
- docs/archive for old docs
"""

import shutil
from pathlib import Path

# Current directory
ROOT = Path("/home/user/puckcast")

def organize():
    print("=" * 80)
    print("ORGANIZING REPOSITORY")
    print("=" * 80)

    # 1. Move training scripts
    training_moves = {
        # Production
        "train_v7_3_situational.py": "training/train_v7_3_situational.py",

        # Experiments
        "train_v7_4_head_to_head.py": "training/experiments/train_v7_4_head_to_head.py",
        "train_v7_5_interactions.py": "training/experiments/train_v7_5_interactions.py",
        "train_v7_6_team_calibration.py": "training/experiments/train_v7_6_team_calibration.py",

        # Archive old
        "train_optimal.py": "training/archive/train_optimal.py",
        "train_v6_improved.py": "training/archive/train_v6_improved.py",
        "train_v7_1_simple_goalies.py": "training/archive/train_v7_1_simple_goalies.py",
        "train_v7_1_with_goalies.py": "training/archive/train_v7_1_with_goalies.py",
        "train_v7_2_lightgbm.py": "training/archive/train_v7_2_lightgbm.py",
        "train_v7_4_special_teams.py": "training/archive/train_v7_4_special_teams.py",
        "train_v7_5_pdo.py": "training/archive/train_v7_5_pdo.py",
        "train_v7_6_confirmed_starters.py": "training/archive/train_v7_6_confirmed_starters.py",
    }

    # 2. Move analysis scripts
    analysis_moves = {
        # Current
        "analyze_v7_3_errors.py": "analysis/current/analyze_v7_3_errors.py",
        "analyze_b2b_weakness.py": "analysis/current/analyze_b2b_weakness.py",
        "analyze_confidence_calibration.py": "analysis/current/analyze_confidence_calibration.py",

        # Archive old
        "analyze_v6_features.py": "analysis/archive/analyze_v6_features.py",
        "analyze_v7_features.py": "analysis/archive/analyze_v7_features.py",
        "evaluate_model_comprehensive.py": "analysis/archive/evaluate_model_comprehensive.py",
        "evaluate_v7_pruned.py": "analysis/archive/evaluate_v7_pruned.py",
        "test_v7_features.py": "analysis/archive/test_v7_features.py",
    }

    # 3. Move prediction scripts
    prediction_moves = {
        "predict_tonight.py": "prediction/predict_tonight.py",
        "predict_simple.py": "prediction/predict_simple.py",
        "predict_full.py": "prediction/predict_full.py",
        "generate_insights.py": "prediction/generate_insights.py",
    }

    # 4. Move goalie system scripts
    goalie_moves = {
        "populate_starting_goalies_from_history.py": "goalie_system/populate_starting_goalies_from_history.py",
        "build_goalie_database.py": "goalie_system/build_goalie_database.py",
        "build_goalie_database_fixed.py": "goalie_system/build_goalie_database_fixed.py",
        "build_goalie_database_train_only.py": "goalie_system/build_goalie_database_train_only.py",
        "extract_starting_goalies.py": "goalie_system/extract_starting_goalies.py",
        "check_starter_field.py": "goalie_system/check_starter_field.py",
    }

    # 5. Move documentation
    doc_moves = {
        # Current docs
        "CLOSING_GAP_TO_62_ANALYSIS.md": "docs/current/CLOSING_GAP_ANALYSIS.md",

        # Experiment docs
        "V7_4_HEAD_TO_HEAD_ANALYSIS.md": "docs/experiments/V7.4_HEAD_TO_HEAD.md",
        "GOALIE_TRACKING_ANALYSIS.md": "docs/experiments/GOALIE_TRACKING.md",

        # Archive old docs
        "V7_1_ANALYSIS_CORRECTED.md": "docs/archive/V7_1_ANALYSIS_CORRECTED.md",
        "V7_1_RELEASE_NOTES.md": "docs/archive/V7_1_RELEASE_NOTES.md",
        "V7_4_FEATURE_ENHANCEMENT_PLAN.md": "docs/archive/V7_4_FEATURE_ENHANCEMENT_PLAN.md",
        "V7_4_PHASE1_RESULTS.md": "docs/archive/V7_4_PHASE1_RESULTS.md",
        "V7_6_FINDINGS.md": "docs/archive/V7_6_FINDINGS.md",
        "V7_FINAL_SUMMARY.md": "docs/archive/V7_FINAL_SUMMARY.md",
        "V7_PROGRESS.md": "docs/archive/V7_PROGRESS.md",
        "V7_QUICK_START.md": "docs/archive/V7_QUICK_START.md",
        "V7_ROADMAP.md": "docs/archive/V7_ROADMAP.md",
        "V7_SERIES_FINAL_SUMMARY.md": "docs/archive/V7_SERIES_FINAL_SUMMARY.md",
        "STARTING_GOALIE_SYSTEM.md": "docs/archive/STARTING_GOALIE_SYSTEM.md",
    }

    all_moves = {
        **training_moves,
        **analysis_moves,
        **prediction_moves,
        **goalie_moves,
        **doc_moves
    }

    # Execute moves
    moved = 0
    skipped = 0

    for src, dst in all_moves.items():
        src_path = ROOT / src
        dst_path = ROOT / dst

        if src_path.exists():
            # Create parent directory if needed
            dst_path.parent.mkdir(parents=True, exist_ok=True)

            # Move file
            shutil.move(str(src_path), str(dst_path))
            print(f"✓ Moved: {src} → {dst}")
            moved += 1
        else:
            print(f"⊘ Skipped (not found): {src}")
            skipped += 1

    print()
    print("=" * 80)
    print(f"Organization complete!")
    print(f"  Moved: {moved} files")
    print(f"  Skipped: {skipped} files (not found)")
    print("=" * 80)


if __name__ == "__main__":
    organize()
