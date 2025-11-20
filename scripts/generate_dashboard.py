#!/usr/bin/env python3
"""
Generate a visual performance dashboard as HTML.

Creates an interactive HTML dashboard with charts showing model performance,
accuracy trends, confidence calibration, and more.
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKTESTING_REPORT = REPO_ROOT / "web" / "src" / "data" / "backtestingReport.json"
CALIBRATION_REPORT = REPO_ROOT / "web" / "src" / "data" / "calibrationReport.json"
MODEL_INSIGHTS = REPO_ROOT / "web" / "src" / "data" / "modelInsights.json"
DASHBOARD_OUTPUT = REPO_ROOT / "reports" / "performance_dashboard.html"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate visual performance dashboard."
    )
    parser.add_argument(
        "--output",
        help="Output HTML file path",
        default=str(DASHBOARD_OUTPUT),
    )
    return parser.parse_args()


def load_data():
    """Load all data files for dashboard."""
    data = {}

    if BACKTESTING_REPORT.exists():
        with open(BACKTESTING_REPORT) as f:
            data["backtesting"] = json.load(f)

    if CALIBRATION_REPORT.exists():
        with open(CALIBRATION_REPORT) as f:
            data["calibration"] = json.load(f)

    if MODEL_INSIGHTS.exists():
        with open(MODEL_INSIGHTS) as f:
            data["insights"] = json.load(f)

    return data


def generate_html(data: dict) -> str:
    """Generate HTML dashboard."""

    # Extract metrics
    backtesting = data.get("backtesting", {})
    calibration = data.get("calibration", {})
    insights = data.get("insights", {})

    overall = backtesting.get("overall", {})
    total_games = overall.get("totalGames", 0)
    accuracy = overall.get("accuracy", 0) * 100
    last_7 = overall.get("last7Days", {})
    last_30 = overall.get("last30Days", {})

    # Build HTML
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Puckcast Performance Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }}
        .header h1 {{
            font-size: 48px;
            margin-bottom: 10px;
        }}
        .header p {{
            font-size: 18px;
            opacity: 0.9;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .stat-label {{
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        .stat-value {{
            font-size: 42px;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-detail {{
            font-size: 14px;
            color: #999;
            margin-top: 10px;
        }}
        .section {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .section h2 {{
            font-size: 24px;
            margin-bottom: 20px;
            color: #333;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #666;
        }}
        .grade-A {{ color: #22c55e; font-weight: bold; }}
        .grade-B {{ color: #3b82f6; font-weight: bold; }}
        .grade-C {{ color: #ef4444; font-weight: bold; }}
        .footer {{
            text-align: center;
            color: white;
            margin-top: 40px;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏒 Puckcast Performance Dashboard</h1>
            <p>Real-time model performance analytics</p>
            <p style="font-size: 14px; margin-top: 10px;">Generated: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Games</div>
                <div class="stat-value">{total_games:,}</div>
                <div class="stat-detail">All-time tracked</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Overall Accuracy</div>
                <div class="stat-value">{accuracy:.1f}%</div>
                <div class="stat-detail">vs {overall.get('baseline', 0)*100:.1f}% baseline</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Last 7 Days</div>
                <div class="stat-value">{last_7.get('accuracy', 0)*100:.1f}%</div>
                <div class="stat-detail">{last_7.get('correct', 0)}/{last_7.get('games', 0)} correct</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Last 30 Days</div>
                <div class="stat-value">{last_30.get('accuracy', 0)*100:.1f}%</div>
                <div class="stat-detail">{last_30.get('correct', 0)}/{last_30.get('games', 0)} correct</div>
            </div>
        </div>

        <div class="section">
            <h2>📊 Performance by Confidence Grade</h2>
            <table>
                <thead>
                    <tr>
                        <th>Grade</th>
                        <th>Games</th>
                        <th>Correct</th>
                        <th>Accuracy</th>
                        <th>Avg Edge</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Add confidence buckets
    by_confidence = backtesting.get("byConfidence", [])
    for item in by_confidence:
        grade = item.get("grade", "?")
        games = item.get("games", 0)
        correct = item.get("correct", 0)
        acc = item.get("accuracy", 0) * 100
        edge = item.get("avgEdge", 0) * 100

        grade_class = "grade-A" if grade[0] == "A" else ("grade-B" if grade[0] == "B" else "grade-C")

        html += f"""
                    <tr>
                        <td class="{grade_class}">{grade}</td>
                        <td>{games}</td>
                        <td>{correct}</td>
                        <td>{acc:.1f}%</td>
                        <td>{edge:.1f} pts</td>
                    </tr>
"""

    html += """
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>🏆 Best Performing Teams</h2>
            <table>
                <thead>
                    <tr>
                        <th>Team</th>
                        <th>Games</th>
                        <th>Accuracy</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Add top teams
    by_team = backtesting.get("byTeam", [])[:10]
    for item in by_team:
        team = item.get("team", "Unknown")
        games = item.get("games", 0)
        acc = item.get("accuracy", 0) * 100

        html += f"""
                    <tr>
                        <td>{team}</td>
                        <td>{games}</td>
                        <td>{acc:.1f}%</td>
                    </tr>
"""

    html += """
                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>🏒 Puckcast.AI - Data-Driven NHL Predictions</p>
            <p style="font-size: 12px; margin-top: 5px;">100% Independent • NHL Official APIs Only</p>
        </div>
    </div>
</body>
</html>
"""

    return html


def main() -> None:
    args = parse_args()

    print("📊 Generating performance dashboard...")

    # Load data
    data = load_data()

    if not data:
        print("❌ No data files found. Generate predictions and backtesting reports first.")
        return

    # Generate HTML
    html = generate_html(data)

    # Save
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        f.write(html)

    print(f"✅ Dashboard generated → {output_path}")
    print(f"   Open in browser: file://{output_path.absolute()}")


if __name__ == "__main__":
    main()
