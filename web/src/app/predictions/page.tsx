"use client";

import { useState, useMemo } from "react";
import type { PredictionsPayload, Prediction } from "@/types/prediction";
import { getPredictionsPayload, selectCurrentSlate } from "@/lib/data";
import { PredictionCard } from "@/components/PredictionCard";
import { PredictionTicker } from "@/components/PredictionTicker";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { ConfidenceBadge } from "@/components/ConfidenceBadge";
import { getPredictionGrade } from "@/lib/prediction";
import { TeamLogo } from "@/components/TeamLogo";

const payload: PredictionsPayload = getPredictionsPayload();
const todaysPredictions = selectCurrentSlate(payload.games);

const pct = (num: number) => `${(num * 100).toFixed(1)}%`;

function getSummary(predictions: Prediction[]) {
  if (!predictions.length) {
    return { avgEdge: 0, aGrades: 0, bPlusEdges: 0, tossUps: 0 };
  }

  const edges = predictions.map((g) => Math.abs(g.edge));
  const avgEdge = edges.reduce((acc, curr) => acc + curr, 0) / predictions.length;
  const aGrades = predictions.filter((g) => getPredictionGrade(g.edge).label.includes("A")).length;
  const bPlusEdges = predictions.filter((g) => {
    const label = getPredictionGrade(g.edge).label;
    return ["A+", "A", "A-", "B+", "B"].includes(label);
  }).length;
  const tossUps = predictions.filter((g) => Math.abs(g.edge) < 0.02).length;

  return { avgEdge, aGrades, bPlusEdges, tossUps };
}

export default function PredictionsPage() {
  const [sortBy, setSortBy] = useState<"time" | "edge" | "confidence">("edge");
  const summary = getSummary(todaysPredictions);

  const topEdges = useMemo(
    () =>
      [...todaysPredictions]
        .sort((a, b) => Math.abs(b.edge) - Math.abs(a.edge))
        .slice(0, 4),
    [todaysPredictions]
  );

  const upsetRadar = useMemo(
    () =>
      todaysPredictions
        .filter((g) => g.modelFavorite === "away" && g.awayWinProb >= 0.55)
        .sort((a, b) => b.awayWinProb - a.awayWinProb)
        .slice(0, 3),
    [todaysPredictions]
  );

  const sortedGames = useMemo(() => {
    const games = [...todaysPredictions];
    if (sortBy === "edge") {
      return games.sort((a, b) => Math.abs(b.edge) - Math.abs(a.edge));
    } else if (sortBy === "confidence") {
      return games.sort((a, b) => b.confidenceScore - a.confidenceScore);
    } else {
      return games.sort((a, b) => (a.startTimeUtc ?? "").localeCompare(b.startTimeUtc ?? ""));
    }
  }, [sortBy]);

  return (
    <div className="min-h-screen">
      <div className="container" style={{ paddingTop: '8rem' }}>
        <PageHeader
          title="Tonight's Predictions"
          description={`Full-game projections with lineup context, rolling form, and NHL API features. ${todaysPredictions.length} games on the slate.`}
          icon={
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          }
        />

        {/* Summary Stats */}
        <section className="mb-16">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 stagger-animation">
            <StatCard
              label="Avg Edge"
              value={`${(summary.avgEdge * 100).toFixed(1)} pts`}
            />
            <StatCard
              label="A-Grade Plays"
              value={summary.aGrades.toString()}
            />
            <StatCard
              label="B+ Edges"
              value={summary.bPlusEdges.toString()}
            />
            <StatCard
              label="Toss-Ups"
              value={summary.tossUps.toString()}
            />
          </div>
        </section>

        {/* Live Ticker */}
        <section className="mb-16">
          <h3 className="text-xl font-bold text-white mb-6">Live Prediction Ticker</h3>
          <div className="card-elevated">
            <PredictionTicker initial={payload} />
          </div>
        </section>

        {todaysPredictions.length > 0 ? (
          <>
            {/* Top Edges & Upsets */}
            <section className="mb-16">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Largest Edges */}
                <div className="card">
                  <h3 className="text-xl font-bold text-white mb-6">Largest Probability Gaps</h3>
                  <div className="space-y-4">
                    {topEdges.map((game) => {
                      const grade = getPredictionGrade(game.edge);
                      return (
                        <div
                          key={game.id}
                          className="p-4 rounded-lg bg-slate-900/50 border border-slate-800 hover:border-slate-700 transition-colors"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-3">
                              <TeamLogo teamAbbrev={game.awayTeam.abbrev} size="xs" />
                              <span className="text-slate-400">@</span>
                              <TeamLogo teamAbbrev={game.homeTeam.abbrev} size="xs" />
                            </div>
                            <div className="flex items-center gap-2">
                              <ConfidenceBadge grade={grade.label} size="sm" />
                              <span className="text-sm text-slate-400">
                                {(Math.abs(game.edge) * 100).toFixed(1)} pts
                              </span>
                            </div>
                          </div>
                          <p className="text-sm text-slate-400">{game.startTimeEt ?? "TBD"}</p>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Upset Radar */}
                <div className="card">
                  <h3 className="text-xl font-bold text-white mb-6">Upset Radar</h3>
                  {upsetRadar.length > 0 ? (
                    <div className="space-y-4">
                      {upsetRadar.map((game) => (
                        <div
                          key={game.id}
                          className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/30 hover:border-amber-500/50 transition-colors"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-3">
                              <TeamLogo teamAbbrev={game.awayTeam.abbrev} size="xs" />
                              <span className="text-white font-semibold">{game.awayTeam.name}</span>
                            </div>
                            <span className="text-amber-400 font-bold">
                              {pct(game.awayWinProb)}
                            </span>
                          </div>
                          <p className="text-sm text-slate-400">@ {game.homeTeam.name}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-slate-400">
                      <p>No strong road favorites tonight</p>
                    </div>
                  )}
                </div>
              </div>
            </section>

            {/* All Games */}
            <section className="mb-16">
              <div className="flex items-center justify-between mb-8">
                <h3 className="text-2xl font-bold text-white">All Games</h3>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-400">Sort by:</span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setSortBy("edge")}
                      className={`btn btn-sm ${sortBy === "edge" ? "btn-primary" : "btn-secondary"}`}
                    >
                      Edge
                    </button>
                    <button
                      onClick={() => setSortBy("confidence")}
                      className={`btn btn-sm ${sortBy === "confidence" ? "btn-primary" : "btn-secondary"}`}
                    >
                      Confidence
                    </button>
                    <button
                      onClick={() => setSortBy("time")}
                      className={`btn btn-sm ${sortBy === "time" ? "btn-primary" : "btn-secondary"}`}
                    >
                      Time
                    </button>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {sortedGames.map((prediction) => (
                  <PredictionCard key={prediction.id} prediction={prediction} />
                ))}
              </div>
            </section>

            {/* Game Table */}
            <section className="mb-16">
              <h3 className="text-2xl font-bold text-white mb-8">Game-by-Game Sheet</h3>
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Matchup</th>
                      <th>Home %</th>
                      <th>Away %</th>
                      <th>Edge</th>
                      <th>Visual</th>
                      <th>Grade</th>
                      <th>Start</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedGames.map((game) => {
                      const grade = getPredictionGrade(game.edge);
                      return (
                        <tr key={game.id}>
                          <td className="font-semibold">
                            <div className="flex items-center gap-2">
                              <TeamLogo teamAbbrev={game.awayTeam.abbrev} size="xs" />
                              <span>@</span>
                              <TeamLogo teamAbbrev={game.homeTeam.abbrev} size="xs" />
                            </div>
                          </td>
                          <td>{pct(game.homeWinProb)}</td>
                          <td>{pct(game.awayWinProb)}</td>
                          <td>{(game.edge * 100).toFixed(1)} pts</td>
                          <td>
                            <EdgeBar value={game.edge} />
                          </td>
                          <td>
                            <ConfidenceBadge grade={grade.label} size="sm" />
                          </td>
                          <td className="text-slate-400">{game.startTimeEt ?? "TBD"}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        ) : (
          <div className="card text-center py-16">
            <div className="text-slate-600 text-6xl mb-4">🏒</div>
            <p className="text-xl text-slate-400">No games scheduled today</p>
            <p className="text-sm text-slate-500 mt-2">Check back tomorrow for fresh predictions</p>
          </div>
        )}
      </div>
    </div>
  );
}

function EdgeBar({ value }: { value: number }) {
  const width = Math.min(Math.abs(value) * 200, 100);
  return (
    <div className="progress-bar w-20 h-2">
      <div className="progress-fill" style={{ width: `${width}%` }} />
    </div>
  );
}
