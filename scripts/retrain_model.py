#!/usr/bin/env python3
"""
Automated model retraining script with performance comparison.

This script retrains the V6.0 model on the latest data and compares
performance against the current model to decide whether to deploy.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = REPO_ROOT / "models"
REPORTS_DIR = REPO_ROOT / "reports"
RETRAINING_LOG = REPO_ROOT / "data" / "archive" / "retraining_log.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Retrain model and compare performance."
    )
    parser.add_argument(
        "--train-seasons",
        nargs="+",
        help="Seasons to train on (e.g., 20212022 20222023 20232024)",
    )
    parser.add_argument(
        "--test-season",
        help="Season to test on (e.g., 20242025)",
    )
    parser.add_argument(
        "--auto-deploy",
        action="store_true",
        help="Automatically deploy if new model is better",
    )
    parser.add_argument(
        "--min-improvement",
        type=float,
        default=0.01,
        help="Minimum accuracy improvement to deploy (default: 1%)",
    )
    return parser.parse_args()


def load_current_performance() -> Dict[str, Any] | None:
    """Load performance metrics of current production model."""
    insights_file = REPO_ROOT / "web" / "src" / "data" / "modelInsights.json"

    if not insights_file.exists():
        return None

    with open(insights_file) as f:
        data = json.load(f)

    return {
        "accuracy": data.get("overall", {}).get("accuracy", 0),
        "logLoss": data.get("overall", {}).get("logLoss", 0),
        "brier": data.get("overall", {}).get("brier", 0),
    }


def run_training(train_seasons: list[str] | None, test_season: str | None) -> Dict[str, Any]:
    """Run model training and return performance metrics."""
    print("🔧 Starting model training...")
    print(f"   Train seasons: {train_seasons or 'default'}")
    print(f"   Test season: {test_season or 'default'}")

    # Build command
    cmd = [sys.executable, "-m", "nhl_prediction.train", "train"]

    if train_seasons:
        cmd.extend(["--train-seasons"] + train_seasons)
    if test_season:
        cmd.extend(["--test-season", test_season])

    # Run training
    try:
        result = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
        )

        print(result.stdout)

        # Parse output for metrics (simplistic - adjust based on actual output)
        # In production, the train.py should output JSON metrics
        output_lines = result.stdout.split("\n")

        # Try to find test metrics in output
        metrics = {}
        for line in output_lines:
            if "Test accuracy" in line or "test_acc" in line.lower():
                try:
                    # Extract accuracy (format: "Test accuracy: 0.6089" or similar)
                    parts = line.split(":")
                    if len(parts) >= 2:
                        acc_str = parts[-1].strip().rstrip("%")
                        metrics["accuracy"] = float(acc_str)
                except (ValueError, IndexError):
                    pass

            if "Log loss" in line or "log_loss" in line.lower():
                try:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        loss_str = parts[-1].strip()
                        metrics["logLoss"] = float(loss_str)
                except (ValueError, IndexError):
                    pass

        # If we couldn't parse metrics, check reports directory
        if not metrics:
            print("⚠️  Couldn't parse metrics from output, checking reports...")
            # Look for latest report file
            report_files = sorted(REPORTS_DIR.glob("*.csv"))
            if report_files:
                print(f"   Found report: {report_files[-1]}")
                # Could parse CSV here if needed

        return metrics

    except subprocess.CalledProcessError as e:
        print(f"❌ Training failed with exit code {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        raise


def compare_models(current: Dict[str, Any] | None, new: Dict[str, Any], min_improvement: float) -> tuple[bool, str]:
    """Compare model performance and decide whether to deploy."""
    if not current:
        return True, "No current model found - deploying new model"

    if not new.get("accuracy"):
        return False, "New model metrics unavailable - keeping current model"

    current_acc = current.get("accuracy", 0)
    new_acc = new.get("accuracy", 0)

    improvement = new_acc - current_acc

    if improvement >= min_improvement:
        return True, f"New model improved accuracy by {improvement:.2%} (threshold: {min_improvement:.2%})"
    elif improvement > 0:
        return False, f"New model improved by {improvement:.2%}, but below threshold of {min_improvement:.2%}"
    else:
        return False, f"New model performance declined by {abs(improvement):.2%} - keeping current model"


def log_retraining(
    train_seasons: list[str] | None,
    test_season: str | None,
    current_metrics: Dict[str, Any] | None,
    new_metrics: Dict[str, Any],
    deployed: bool,
    reason: str,
) -> None:
    """Log retraining event to history."""
    RETRAINING_LOG.parent.mkdir(parents=True, exist_ok=True)

    # Load existing log
    if RETRAINING_LOG.exists():
        with open(RETRAINING_LOG) as f:
            log = json.load(f)
    else:
        log = {"retraining_events": []}

    # Add new event
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trainSeasons": train_seasons,
        "testSeason": test_season,
        "currentMetrics": current_metrics,
        "newMetrics": new_metrics,
        "deployed": deployed,
        "reason": reason,
    }

    log["retraining_events"].append(event)

    # Save log
    with open(RETRAINING_LOG, "w") as f:
        json.dump(log, f, indent=2)

    print(f"📝 Logged retraining event → {RETRAINING_LOG}")


def main() -> int:
    args = parse_args()

    print("=" * 70)
    print("🤖 MODEL RETRAINING WORKFLOW")
    print("=" * 70)

    # Load current model performance
    print("\n1️⃣  Loading current model performance...")
    current_metrics = load_current_performance()

    if current_metrics:
        print(f"   Current accuracy: {current_metrics.get('accuracy', 0):.2%}")
    else:
        print("   No current model found")

    # Run training
    print("\n2️⃣  Training new model...")
    try:
        new_metrics = run_training(args.train_seasons, args.test_season)
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        return 1

    if new_metrics:
        print(f"\n   New model accuracy: {new_metrics.get('accuracy', 0):.2%}")
    else:
        print("\n   ⚠️  Could not determine new model performance")

    # Compare models
    print("\n3️⃣  Comparing models...")
    should_deploy, reason = compare_models(
        current_metrics, new_metrics, args.min_improvement
    )

    print(f"   {reason}")

    # Decide on deployment
    deployed = False
    if should_deploy and args.auto_deploy:
        print("\n4️⃣  Deploying new model...")
        print("   ✅ New model artifacts will be committed")
        deployed = True
    elif should_deploy:
        print("\n4️⃣  New model is better, but auto-deploy is disabled")
        print("   💡 Run with --auto-deploy to automatically deploy better models")
    else:
        print("\n4️⃣  Keeping current model")

    # Log event
    log_retraining(
        args.train_seasons,
        args.test_season,
        current_metrics,
        new_metrics,
        deployed,
        reason,
    )

    # Summary
    print("\n" + "=" * 70)
    print("✅ RETRAINING COMPLETE")
    print(f"   Deployed: {'Yes' if deployed else 'No'}")
    print(f"   Reason: {reason}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
