"""
Generate aggregated metrics for the Next.js site.

Reads model outputs from `reports/predictions_20232024.csv`
and feature importance rankings from `reports/feature_importance_v2.csv`,
then writes `web/src/data/modelInsights.json`.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PRED_PATH = ROOT / "reports" / "predictions_20232024.csv"
FEATURE_PATH = ROOT / "reports" / "feature_importance_v2.csv"
TEAM_PATH = ROOT / "data" / "nhl_teams.csv"
OUT_PATH = ROOT / "web" / "src" / "data" / "modelInsights.json"


def pct(value: float) -> float:
  return float(value)


def main() -> None:
  df = pd.read_csv(PRED_PATH)
  df["correct_int"] = df["correct"].astype(int)
  df["edge"] = (df["home_win_probability"] - 0.5).abs()

  games = int(len(df))
  accuracy = df["correct_int"].mean()
  home_win_rate = df["home_win"].mean()
  brier = float(np.mean((df["home_win_probability"] - df["home_win"]) ** 2))
  log_loss = float(
    -np.mean(
      df["home_win"] * np.log(np.clip(df["home_win_probability"], 1e-15, 1))
      + (1 - df["home_win"]) * np.log(np.clip(1 - df["home_win_probability"], 1e-15, 1))
    )
  )
  avg_edge = float(df["edge"].mean())

  team_meta = pd.read_csv(TEAM_PATH)
  division_map = {15: "Pacific", 16: "Central", 17: "Atlantic", 18: "Metropolitan"}
  conference_map = {"Pacific": "West", "Central": "West", "Atlantic": "East", "Metropolitan": "East"}
  team_meta["division"] = team_meta["divisionId"].map(division_map)
  team_meta["conference"] = team_meta["division"].map(conference_map)
  team_meta = team_meta.set_index("triCode")

  teams: dict[str, dict[str, float]] = {}

  def ensure_team(code: str) -> dict[str, float]:
    if code not in teams:
      meta = team_meta.loc[code] if code in team_meta.index else None
      teams[code] = {
        "team": meta["fullName"] if meta is not None else code,
        "abbrev": code,
        "conference": meta["conference"] if meta is not None else "Unknown",
        "division": meta["division"] if meta is not None else "Unknown",
        "games": 0,
        "wins": 0,
        "losses": 0,
        "correct": 0,
      }
    return teams[code]

  for _, row in df.iterrows():
    home = ensure_team(row["teamAbbrev_home"])
    away = ensure_team(row["teamAbbrev_away"])
    home_win = int(row["home_win"])
    is_correct = int(row["correct"])

    home["games"] += 1
    home["wins"] += home_win
    home["losses"] += 1 - home_win
    home["correct"] += is_correct

    away["games"] += 1
    away["wins"] += 1 - home_win
    away["losses"] += home_win
    away["correct"] += is_correct

  team_performance: list[dict[str, float]] = []
  for team in teams.values():
    games_played = team["games"]
    accuracy_team = team["correct"] / games_played if games_played else 0
    team_performance.append(
      {
        "team": team["team"],
        "abbrev": team["abbrev"],
        "conference": team["conference"],
        "division": team["division"],
        "games": int(games_played),
        "wins": int(team["wins"]),
        "losses": int(team["losses"]),
        "record": f"{team['wins']}-{team['losses']}",
        "points": int(team["wins"] * 2),
        "modelAccuracy": accuracy_team,
        "winPct": team["wins"] / games_played if games_played else 0,
        "correct": int(team["correct"]),
      }
    )

  team_performance.sort(key=lambda x: x["modelAccuracy"], reverse=True)

  def build_standings(conf: str) -> list[dict[str, float]]:
    conf_teams = [t.copy() for t in team_performance if t["conference"] == conf]
    conf_teams.sort(key=lambda x: (x["points"], x["winPct"]), reverse=True)
    return [
      {"team": t["team"], "abbrev": t["abbrev"], "record": t["record"], "points": t["points"], "winPct": t["winPct"]}
      for t in conf_teams
    ]

  standings = {"east": build_standings("East"), "west": build_standings("West")}

  buckets = [
    (0, 0.05, "0-5 pts"),
    (0.05, 0.1, "5-10 pts"),
    (0.1, 0.15, "10-15 pts"),
    (0.15, 0.2, "15-20 pts"),
    (0.2, None, "20+ pts"),
  ]
  confidence_buckets = []
  for lower, upper, label in buckets:
    mask = df["edge"] >= lower
    if upper is not None:
      mask &= df["edge"] < upper
    subset = df[mask]
    count = int(len(subset))
    accuracy_bucket = subset["correct_int"].mean() if count else 0
    confidence_buckets.append({"label": label, "min": lower, "max": upper, "accuracy": accuracy_bucket, "count": count})

  strategy_defs = [
    ("All predictions", df.index, "Use the higher probability team for every game"),
    ("Edge ≥ 5 pts", df[df["edge"] >= 0.05].index, "Skip games with <5 percentage point edge"),
    ("Edge ≥ 10 pts", df[df["edge"] >= 0.10].index, "Focus on double-digit probability edges"),
    ("Edge ≥ 15 pts", df[df["edge"] >= 0.15].index, "Only strongest probability splits"),
  ]
  strategies = []
  for name, idx, note in strategy_defs:
    subset = df.loc[idx]
    bets = int(len(subset))
    if bets == 0:
      continue
    wins = int(subset["correct_int"].sum())
    losses = bets - wins
    strategies.append(
      {
        "name": name,
        "bets": bets,
        "winRate": wins / bets,
        "units": wins - losses,
        "note": note,
        "avgEdge": subset["edge"].mean() if bets else 0,
      }
    )

  matchup_stats: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: {"games": 0, "correct": 0})
  for _, row in df.iterrows():
    key = tuple(sorted([row["teamAbbrev_home"], row["teamAbbrev_away"]]))
    matchup_stats[key]["games"] += 1
    matchup_stats[key]["correct"] += int(row["correct"])

  matchup_rows = []
  for (team_a, team_b), stats in matchup_stats.items():
    games_pair = stats["games"]
    accuracy_pair = stats["correct"] / games_pair if games_pair else 0
    matchup_rows.append({"teams": f"{team_a} vs {team_b}", "games": games_pair, "correct": stats["correct"], "accuracy": accuracy_pair})

  consistent = sorted((m for m in matchup_rows if m["games"] >= 4), key=lambda x: x["accuracy"], reverse=True)[:5]
  volatile = sorted((m for m in matchup_rows if m["games"] >= 4), key=lambda x: x["accuracy"])[:5]

  feature_importance = []
  if FEATURE_PATH.exists():
    feat_df = pd.read_csv(FEATURE_PATH)
    feat_df = feat_df.sort_values("abs_importance", ascending=False).head(10)
    for _, row in feat_df.iterrows():
      feature_importance.append(
        {"feature": row["feature"], "coefficient": float(row["coefficient"]), "absImportance": float(row["abs_importance"])}
      )

  distribution_metrics = []
  for column, label in [
    ("rolling_goal_diff_5_diff", "Rolling goal differential (5 games)"),
    ("rolling_win_pct_5_diff", "Rolling win% (5 games)"),
    ("specialTeamEdge_diff", "Special teams edge differential"),
  ]:
    if column in df.columns:
      correct_mask = df["correct"] == 1
      incorrect_mask = df["correct"] == 0
      distribution_metrics.append(
        {"metric": label, "correctMean": float(df.loc[correct_mask, column].mean()), "incorrectMean": float(df.loc[incorrect_mask, column].mean())}
      )

  df_sorted = df.sort_values("gameDate")
  df_sorted["unit_delta"] = np.where(df_sorted["correct"], 1, -1)
  df_sorted["bankroll"] = df_sorted["unit_delta"].cumsum()
  points = 12
  indices = np.linspace(0, len(df_sorted) - 1, points, dtype=int)
  bankroll_series = [{"label": str(df_sorted.iloc[idx]["gameDate"]), "units": float(df_sorted.iloc[idx]["bankroll"])} for idx in indices]

  hero_stats = [
    {"label": "Test accuracy", "value": f"{accuracy * 100:.1f}%", "detail": "2023-24 holdout"},
    {"label": "Log loss", "value": f"{log_loss:.3f}", "detail": "calibration"},
    {"label": "Games tracked", "value": f"{games:,}", "detail": "2023-24 season"},
  ]

  payload = {
    "generatedAt": datetime.now(timezone.utc).isoformat(),
    "overall": {
      "games": games,
      "accuracy": accuracy,
      "baseline": home_win_rate,
      "homeWinRate": home_win_rate,
      "brier": brier,
      "logLoss": log_loss,
      "avgEdge": avg_edge,
    },
    "heroStats": hero_stats,
    "insights": [
      {"title": "Edge ≥ 10 pts", "detail": f"{strategies[2]['winRate'] * 100:.1f}% accuracy across {strategies[2]['bets']} games"} if len(strategies) > 2 else None,
      {"title": "Edge ≥ 15 pts", "detail": f"{strategies[3]['winRate'] * 100:.1f}% accuracy (n={strategies[3]['bets']})"} if len(strategies) > 3 else None,
      {"title": "Home baseline", "detail": f"Home teams won {home_win_rate * 100:.1f}% of games; model adds {(accuracy - home_win_rate) * 100:.1f} pts"},
    ],
    "strategies": strategies,
    "confidenceBuckets": confidence_buckets,
    "teamPerformance": team_performance,
    "standings": standings,
    "matchupInsights": {"consistent": consistent, "volatile": volatile},
    "featureImportance": feature_importance,
    "distributionFindings": distribution_metrics,
    "bankrollSeries": bankroll_series,
  }

  payload["insights"] = [item for item in payload["insights"] if item is not None]

  OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
  OUT_PATH.write_text(json.dumps(payload, indent=2))
  print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
  main()
