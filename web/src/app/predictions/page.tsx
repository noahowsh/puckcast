"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import insightsData from "@/data/modelInsights.json";
import startingGoaliesData from "@/data/startingGoalies.json";
import type { ModelInsights } from "@/types/insights";
import type { Prediction, PredictionsPayload } from "@/types/prediction";
import { getPredictionsPayload, selectCurrentSlate } from "@/lib/data";
import { getPredictionGrade } from "@/lib/prediction";
import { TeamCrest } from "@/components/TeamCrest";

// Starting goalies types and data
type StartingGoalieEntry = {
  team: string;
  playerId: number | null;
  goalieName: string | null;
  confirmedStart: boolean;
  statusCode: string;
  statusDescription: string;
  lastUpdated: string;
};

type StartingGoaliesPayload = {
  generatedAt: string;
  source: string;
  date: string;
  teams: Record<string, StartingGoalieEntry>;
};

const startingGoalies = startingGoaliesData as StartingGoaliesPayload;

function getGoalieStatusColor(statusCode: string): string {
  switch (statusCode.toLowerCase()) {
    case 'confirmed': return '#10b981';
    case 'expected': return '#3b82f6';
    case 'likely': return '#f59e0b';
    case 'probable': return '#f97316';
    default: return 'var(--text-tertiary)';
  }
}

function getGoalieStatusBg(statusCode: string): string {
  switch (statusCode.toLowerCase()) {
    case 'confirmed': return 'rgba(16, 185, 129, 0.12)';
    case 'expected': return 'rgba(59, 130, 246, 0.12)';
    case 'likely': return 'rgba(245, 158, 11, 0.12)';
    case 'probable': return 'rgba(249, 115, 22, 0.12)';
    default: return 'rgba(255,255,255,0.04)';
  }
}

const payload: PredictionsPayload = getPredictionsPayload();
const todaysPredictions = selectCurrentSlate(payload.games);
const modelInsights = insightsData as ModelInsights;

const updatedTimestamp = payload.generatedAt ? new Date(payload.generatedAt) : null;
const updatedDisplay = updatedTimestamp
  ? new Intl.DateTimeFormat("en-US", {
      timeZone: "America/New_York",
      hour: "numeric",
      minute: "numeric",
      month: "short",
      day: "numeric",
    }).format(updatedTimestamp)
  : null;

const pct = (num: number) => `${(num * 100).toFixed(1)}%`;

type SortKey = "edge" | "time";

function GoalieTag({ goalie }: { goalie: StartingGoalieEntry | undefined }) {
  if (!goalie?.goalieName) {
    return (
      <span className="goalie-tag goalie-tag--tbd">
        🥅 TBD
      </span>
    );
  }

  return (
    <span
      className="goalie-tag"
      style={{
        background: getGoalieStatusBg(goalie.statusCode),
        borderColor: `${getGoalieStatusColor(goalie.statusCode)}40`,
      }}
    >
      🥅 {goalie.goalieName}
      <span
        className="goalie-tag__status"
        style={{ color: getGoalieStatusColor(goalie.statusCode) }}
      >
        {goalie.statusCode}
      </span>
    </span>
  );
}

function MatchupCard({ game }: { game: Prediction }) {
  const favorite = game.modelFavorite === "home" ? game.homeTeam : game.awayTeam;
  const grade = getPredictionGrade(game.edge);
  const edgePts = Math.abs(game.edge * 100);
  const homeGoalie = startingGoalies.teams[game.homeTeam.abbrev];
  const awayGoalie = startingGoalies.teams[game.awayTeam.abbrev];

  return (
    <Link href={`/matchup/${game.id}`} className="matchup-card-v3">
      {/* Teams Row with Goalies */}
      <div className="matchup-card-v3__teams-row">
        {/* Away Side */}
        <div className="matchup-card-v3__side">
          <div className="matchup-card-v3__team-block">
            <TeamCrest abbrev={game.awayTeam.abbrev} size={42} />
            <div className="matchup-card-v3__team-details">
              <span className="matchup-card-v3__team-name">{game.awayTeam.name}</span>
              <span
                className="matchup-card-v3__prob"
                style={{ color: game.modelFavorite === 'away' ? 'var(--mint)' : 'var(--text-secondary)' }}
              >
                {pct(game.awayWinProb)}
              </span>
            </div>
          </div>
          <GoalieTag goalie={awayGoalie} />
        </div>

        {/* Center */}
        <div className="matchup-card-v3__center">
          <span className="matchup-card-v3__time">{game.startTimeEt ?? "TBD"}</span>
          <span className="matchup-card-v3__vs">VS</span>
        </div>

        {/* Home Side */}
        <div className="matchup-card-v3__side matchup-card-v3__side--home">
          <div className="matchup-card-v3__team-block matchup-card-v3__team-block--home">
            <div className="matchup-card-v3__team-details" style={{ textAlign: 'right' }}>
              <span className="matchup-card-v3__team-name">{game.homeTeam.name}</span>
              <span
                className="matchup-card-v3__prob"
                style={{ color: game.modelFavorite === 'home' ? 'var(--mint)' : 'var(--text-secondary)' }}
              >
                {pct(game.homeWinProb)}
              </span>
            </div>
            <TeamCrest abbrev={game.homeTeam.abbrev} size={42} />
          </div>
          <GoalieTag goalie={homeGoalie} />
        </div>
      </div>

      {/* Probability Bar - Split with gap */}
      <div className="matchup-card-v3__prob-bar">
        <div
          className="matchup-card-v3__prob-segment matchup-card-v3__prob-segment--away"
          style={{ width: `calc(${game.awayWinProb * 100}% - 2px)` }}
        />
        <div className="matchup-card-v3__prob-divider" />
        <div
          className="matchup-card-v3__prob-segment matchup-card-v3__prob-segment--home"
          style={{ width: `calc(${game.homeWinProb * 100}% - 2px)` }}
        />
      </div>

      {/* Footer: Model Lean + Grade */}
      <div className="matchup-card-v3__footer">
        <div className="matchup-card-v3__lean">
          <span className="matchup-card-v3__lean-label">Model lean →</span>
          <span className="matchup-card-v3__lean-team">{favorite.name}</span>
        </div>

        <div className={`matchup-card-v3__grade matchup-card-v3__grade--${grade.label.charAt(0).toLowerCase()}`}>
          <span className="matchup-card-v3__grade-letter">{grade.label}</span>
          <span className="matchup-card-v3__grade-edge">{edgePts.toFixed(1)} pts edge</span>
        </div>
      </div>

      <span className="matchup-card-v3__cta">View full analysis →</span>
    </Link>
  );
}

function ConfidenceLadder() {
  const ladder = [...modelInsights.confidenceBuckets].sort((a, b) => b.accuracy - a.accuracy);
  return (
    <div className="confidence-ladder-bottom">
      <div className="confidence-ladder-bottom__header">
        <div>
          <p className="eyebrow">Model Performance</p>
          <h3>Confidence Ladder</h3>
          <p className="lead-sm">Holdout accuracy by prediction confidence band</p>
        </div>
        <Link href="/performance" className="cta cta-ghost">
          Full breakdown →
        </Link>
      </div>
      <div className="confidence-ladder-bottom__grid">
        {ladder.map((bucket) => (
          <div key={bucket.label} className="confidence-ladder-bottom__item">
            <div className="confidence-ladder-bottom__bar-wrap">
              <div
                className="confidence-ladder-bottom__bar"
                style={{ height: `${Math.max(bucket.accuracy * 100, 10)}%` }}
              />
            </div>
            <span className="confidence-ladder-bottom__pct">{pct(bucket.accuracy)}</span>
            <span className="confidence-ladder-bottom__grade">{bucket.grade}</span>
            <span className="confidence-ladder-bottom__count">{bucket.count} games</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function PredictionsPage() {
  const [sortBy, setSortBy] = useState<SortKey>("edge");

  const sortedGames = useMemo(() => {
    const games = [...todaysPredictions];
    if (sortBy === "edge") {
      return games.sort((a, b) => Math.abs(b.edge) - Math.abs(a.edge));
    }
    return games.sort((a, b) => (a.startTimeUtc ?? "").localeCompare(b.startTimeUtc ?? ""));
  }, [sortBy]);

  const aCount = todaysPredictions.filter(g => getPredictionGrade(g.edge).label.includes('A')).length;
  const bCount = todaysPredictions.filter(g => getPredictionGrade(g.edge).label.includes('B')).length;
  const cCount = todaysPredictions.length - aCount - bCount;

  return (
    <div className="min-h-screen">
      <div className="container">
        {/* Compact Header with Update Badge */}
        <section className="predictions-header-v2">
          <div className="predictions-header-v2__top">
            <div className="predictions-header-v2__title-group">
              <h1 className="predictions-header-v2__title">Tonight&apos;s Board</h1>
              <div className="predictions-header-v2__badges">
                <span className="predictions-header-v2__badge predictions-header-v2__badge--count">
                  {todaysPredictions.length} games
                </span>
                {updatedDisplay && (
                  <span className="predictions-header-v2__badge predictions-header-v2__badge--live">
                    <span className="predictions-header-v2__live-dot" />
                    Updated {updatedDisplay} ET
                  </span>
                )}
              </div>
            </div>

            <div className="predictions-header-v2__grade-summary">
              {aCount > 0 && <span className="grade-chip grade-chip--a">{aCount} A-tier</span>}
              {bCount > 0 && <span className="grade-chip grade-chip--b">{bCount} B-tier</span>}
              {cCount > 0 && <span className="grade-chip grade-chip--c">{cCount} Toss-up</span>}
            </div>
          </div>

          <div className="predictions-header-v2__controls">
            <p className="predictions-header-v2__subtitle">
              Win probabilities and edges with confirmed goalie matchups
            </p>
            <div className="sort-tabs">
              {(["edge", "time"] as SortKey[]).map((key) => (
                <button
                  key={key}
                  className={`sort-tab ${sortBy === key ? "sort-tab--active" : ""}`}
                  onClick={() => setSortBy(key)}
                  type="button"
                >
                  {key === "edge" ? "By edge" : "By time"}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Full Width Matchup Cards */}
        <section className="matchup-grid-v2">
          {sortedGames.length ? (
            sortedGames.map((game) => <MatchupCard key={game.id} game={game} />)
          ) : (
            <div className="empty-tile" style={{ gridColumn: '1 / -1' }}>
              <p>No games tonight. The feed will auto-refresh when the slate posts.</p>
            </div>
          )}
        </section>

        {/* Confidence Ladder - Bottom */}
        {sortedGames.length > 0 && (
          <section className="nova-section" style={{ paddingTop: '1.5rem' }}>
            <ConfidenceLadder />
          </section>
        )}
      </div>
    </div>
  );
}
