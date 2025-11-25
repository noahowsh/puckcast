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
    <div className="prediction-row">
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
        <span className="chip-soft">
          {game.homeTeam.name} @ {game.awayTeam.name}
        </span>
      </div>
    </div>
  );
}

function ConfidenceLadder() {
  const ladder = [...modelInsights.confidenceBuckets].reverse();
  const bandLabel = (label: string) => {
    // label examples: "20+ pts", "17-19 pts", "14-16 pts", "10-13 pts", "7-9 pts", "4-6 pts", "2-3 pts", "<2 pts"
    const key = label.replace(/\s+/g, "").toLowerCase();
    if (key.startsWith("20")) return "A+";
    if (key.startsWith("17")) return "A";
    if (key.startsWith("14")) return "A-";
    if (key.startsWith("10")) return "B+";
    if (key.startsWith("7")) return "B";
    if (key.startsWith("4")) return "B-";
    if (key.startsWith("2")) return "C+";
    return "C";
  };
  return (
    <div className="bento-card">
      <p className="micro-label">Confidence ladder</p>
      <h3>Holdout accuracy by band</h3>
      <div className="ladder">
        {ladder.map((bucket) => (
          <div key={bucket.label} className="ladder__row">
            <div>
              <p className="edge-card__team">
                {bucket.label} <span className="chip-soft" style={{ marginLeft: "0.35rem" }}>{bandLabel(bucket.label)}</span>
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

            <div className="nova-hero__panel">
              <div className="stat-grid">
                <div className="stat-tile">
                  <p className="stat-tile__label">Holdout accuracy</p>
                  <p className="stat-tile__value">{pct(modelInsights.overall.accuracy)}</p>
                  <p className="stat-tile__detail">Baseline {pct(modelInsights.overall.baseline)}</p>
                </div>
                <div className="stat-tile">
                  <p className="stat-tile__label">Average edge</p>
                  <p className="stat-tile__value">{(summary.avgEdge * 100).toFixed(1)} pts</p>
                  <p className="stat-tile__detail">Per matchup</p>
                </div>
                <div className="stat-tile">
                  <p className="stat-tile__label">A grades</p>
                  <p className="stat-tile__value">{summary.aGrades}</p>
                  <p className="stat-tile__detail">+ B grade: {todaysPredictions.length - summary.aGrades - summary.tossUps}</p>
                </div>
                <div className="stat-tile">
                  <p className="stat-tile__label">Toss ups</p>
                  <p className="stat-tile__value">{summary.tossUps}</p>
                  <p className="stat-tile__detail">Less than 2 pts edge</p>
                </div>
              </div>
              <div className="cta-row">
                <Link href="/performance" className="cta cta-ghost">
                  View model receipts
                </Link>
                <Link href="/leaderboards" className="cta cta-light">
                  Power index
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
