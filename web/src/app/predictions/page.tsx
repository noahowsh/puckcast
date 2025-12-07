"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import insightsData from "@/data/modelInsights.json";
import type { ModelInsights } from "@/types/insights";
import type { Prediction, PredictionsPayload } from "@/types/prediction";
import { getPredictionsPayload, selectCurrentSlate } from "@/lib/data";
import { getPredictionGrade } from "@/lib/prediction";
import { teamBorderColor, teamGradient } from "@/lib/teamColors";
import { TeamCrest } from "@/components/TeamCrest";

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

function EdgeMeter({ value }: { value: number }) {
  const width = Math.min(Math.abs(value) * 520, 100);
  const positive = value >= 0;
  return (
    <div className="edge-meter">
      <div
        className="edge-meter__fill"
        style={{ width: `${width}%`, background: positive ? "linear-gradient(90deg, #6ef0c2, #7ee3ff)" : "linear-gradient(90deg, #ff94a8, #f6c177)" }}
      />
    </div>
  );
}

function getSummary(predictions: Prediction[]) {
  if (!predictions.length) {
    return { avgEdge: 0, aGrades: 0, tossUps: 0 };
  }
  const edges = predictions.map((g) => Math.abs(g.edge));
  const avgEdge = edges.reduce((acc, curr) => acc + curr, 0) / predictions.length;
  const aGrades = predictions.filter((g) => getPredictionGrade(g.edge).label.includes("A")).length;
  const tossUps = predictions.filter((g) => Math.abs(g.edge) < 0.02).length;
  return { avgEdge, aGrades, tossUps };
}

function PredictionRow({ game }: { game: Prediction }) {
  const favorite = game.modelFavorite === "home" ? game.homeTeam : game.awayTeam;
  const prob = game.modelFavorite === "home" ? game.homeWinProb : game.awayWinProb;
  const grade = getPredictionGrade(game.edge);
  const edgePts = Math.abs(game.edge * 100);
  return (
    <Link href={`/matchup/${game.id}`} className="prediction-row prediction-row--clickable">
          <div className="prediction-row__teams">
            <div className="versus">
              <TeamCrest abbrev={game.awayTeam.abbrev} />
              <span className="versus__divider">@</span>
              <TeamCrest abbrev={game.homeTeam.abbrev} />
            </div>
            <div className="prediction-row__meta">
              <span className="tag">{game.startTimeEt ?? "TBD"}</span>
          <span className="chip-soft">{game.modelFavorite === "home" ? "Home tilt" : "Road lean"}</span>
        </div>
      </div>

      <div className="prediction-row__body">
        <div>
          <p className="micro-label">Model lean</p>
          <p className="edge-card__team">{favorite.name}</p>
          <p className="edge-card__prob-value">{pct(prob)}</p>
        </div>
        <div className="prediction-row__grade">
          <span className="edge-card__grade">{grade.label}</span>
          <span className="chip-soft">{edgePts.toFixed(1)} pts edge</span>
        </div>
      </div>

      <EdgeMeter value={game.edge} />

      <div className="prediction-row__footer">
        <span className="chip-soft">Confidence {game.confidenceScore.toFixed(2)}</span>
        <span className="chip-soft prediction-row__cta">
          View matchup details →
        </span>
      </div>
    </Link>
  );
}

function ConfidenceLadder() {
  const ladder = [...modelInsights.confidenceBuckets].reverse();
  return (
    <div className="bento-card">
      <p className="micro-label">Confidence ladder</p>
      <h3>Holdout accuracy by band</h3>
      <div className="ladder">
        {ladder.map((bucket) => (
          <div key={bucket.label} className="ladder__row">
            <div>
              <p className="edge-card__team">
                {bucket.label}{" "}
                <span className="chip-soft" style={{ marginLeft: "0.35rem" }}>
                  {bucket.grade}
                </span>
              </p>
              <p className="micro-label">{bucket.count} games</p>
            </div>
            <div className="ladder__meter">
              <div className="edge-meter edge-meter--thick">
                <div className="edge-meter__fill edge-meter__fill--gradient" style={{ width: `${Math.min(bucket.accuracy * 100, 100)}%` }} />
              </div>
              <span className="edge-card__prob-value">{pct(bucket.accuracy)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function PredictionsPage() {
  const [sortBy, setSortBy] = useState<SortKey>("edge");
  const summary = getSummary(todaysPredictions);

  const sortedGames = useMemo(() => {
    const games = [...todaysPredictions];
    if (sortBy === "edge") {
      return games.sort((a, b) => Math.abs(b.edge) - Math.abs(a.edge));
    }
    return games.sort((a, b) => (a.startTimeUtc ?? "").localeCompare(b.startTimeUtc ?? ""));
  }, [sortBy]);

  const upsetRadar = useMemo(
    () =>
      todaysPredictions
        .filter((g) => g.modelFavorite === "away" && g.awayWinProb >= 0.55)
        .sort((a, b) => b.awayWinProb - a.awayWinProb)
        .slice(0, 3),
    []
  );

  return (
    <div className="min-h-screen">
      <div className="container">
        <section className="nova-hero">
          <div className="nova-hero__grid">
            <div className="nova-hero__text">
              <div className="pill-row">
                <span className="pill">{todaysPredictions.length ? `${todaysPredictions.length} games live` : "Off day"}</span>
                {updatedDisplay && <span className="pill">Updated {updatedDisplay} ET</span>}
              </div>
              <h1 className="display-xl">Tonight&apos;s predictions, rebuilt.</h1>
              <p className="lead">
                This is the product: clean, confident, and fast. Every matchup shows the lean, the win probability, the edge bar, and the model&apos;s
                conviction so you can scan the slate in seconds.
              </p>
            </div>

            {/* Visual: Tonight's Grade Distribution */}
            <div className="nova-hero__panel" style={{ padding: '1.25rem' }}>
              <p style={{ fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-tertiary)', marginBottom: '1rem' }}>
                Tonight&apos;s Slate
              </p>

              {/* Grade bars */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
                {(() => {
                  const aCount = todaysPredictions.filter(g => getPredictionGrade(g.edge).label.includes('A')).length;
                  const bCount = todaysPredictions.filter(g => getPredictionGrade(g.edge).label.includes('B')).length;
                  const cCount = todaysPredictions.length - aCount - bCount;
                  const total = todaysPredictions.length || 1;

                  return [
                    { label: 'A-tier', count: aCount, pct: (aCount / total) * 100, color: 'linear-gradient(90deg, var(--aqua), var(--mint))' },
                    { label: 'B-tier', count: bCount, pct: (bCount / total) * 100, color: 'var(--amber)' },
                    { label: 'Toss-ups', count: cCount, pct: (cCount / total) * 100, color: 'rgba(255,255,255,0.3)' },
                  ].map((tier) => (
                    <div key={tier.label} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <span style={{ width: '4rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{tier.label}</span>
                      <div style={{ flex: 1, height: '1.25rem', background: 'rgba(255,255,255,0.08)', borderRadius: '0.375rem', overflow: 'hidden' }}>
                        <div style={{ width: `${tier.pct}%`, height: '100%', background: tier.color, borderRadius: '0.375rem', minWidth: tier.count > 0 ? '8px' : '0' }} />
                      </div>
                      <span style={{ width: '1.5rem', fontSize: '0.9rem', fontWeight: 700, textAlign: 'right' }}>{tier.count}</span>
                    </div>
                  ));
                })()}
              </div>

              {/* Summary stats */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border-subtle)' }}>
                <div style={{ textAlign: 'center' }}>
                  <p style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--mint)' }}>{(summary.avgEdge * 100).toFixed(1)}</p>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Avg edge (pts)</p>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <p style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--aqua)' }}>{pct(modelInsights.overall.accuracy)}</p>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Model accuracy</p>
                </div>
              </div>

              <div className="cta-row" style={{ marginTop: '1rem' }}>
                <Link href="/performance" className="cta cta-ghost" style={{ flex: 1, justifyContent: 'center' }}>
                  Model receipts
                </Link>
              </div>
            </div>
          </div>
        </section>

        <section className="nova-section">
          <div className="section-head">
            <div>
              <p className="eyebrow">Clean, fast, scannable</p>
              <h2>Tonight&apos;s board</h2>
              <p className="lead-sm">Sort by edge, confidence, or puck drop time. Each row is its own mini dashboard.</p>
            </div>
            <div className="sort-tabs">
              {(["edge", "time"] as SortKey[]).map((key) => (
                <button
                  key={key}
                  className={`sort-tab ${sortBy === key ? "sort-tab--active" : ""}`}
                  onClick={() => setSortBy(key)}
                  type="button"
                >
                  {key === "edge" ? "Edge first" : "By start time"}
                </button>
              ))}
            </div>
          </div>

          <div className="prediction-shell">
            <div className="prediction-main">
              {sortedGames.length ? (
                sortedGames.map((game) => <PredictionRow key={game.id} game={game} />)
              ) : (
                <div className="empty-tile">
                  <p>No games tonight. The feed will auto-refresh when the slate posts.</p>
                </div>
              )}
            </div>

            <div className="prediction-rail">
              <ConfidenceLadder />

              <div className="bento-card">
                <p className="micro-label">Update cadence</p>
                <h3>Live ticker</h3>
                <p className="bento-copy">
                  Edges and probabilities refresh as goalies confirm and injuries post. Watch drift in real time on the ticker so you can capture the
                  earliest number.
                </p>
                {updatedDisplay && <span className="chip-soft">Last refresh {updatedDisplay} ET</span>}
                <Link href="/" className="cta cta-ghost" style={{ width: "100%", justifyContent: "center", marginTop: "0.9rem" }}>
                  Return to overview
                </Link>
              </div>

              {upsetRadar.length > 0 && (
                <div className="bento-card">
                  <p className="micro-label">Upset radar</p>
                  <h3>Road favorites to watch</h3>
                  <div className="upset-grid">
                    {upsetRadar.map((game) => (
                      <div key={game.id} className="upset-card">
                        <div className="versus">
                          <TeamCrest abbrev={game.awayTeam.abbrev} />
                          <span className="versus__divider">at</span>
                          <TeamCrest abbrev={game.homeTeam.abbrev} />
                        </div>
                        <div className="upset-card__prob">
                          <span className="edge-card__prob-value">{pct(game.awayWinProb)}</span>
                          <span className="tag">Road lean</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
