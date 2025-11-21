import Link from "next/link";
import { PredictionCard } from "@/components/PredictionCard";
import { getGoaliePulse, getPredictionsPayload, selectCurrentSlate } from "@/lib/data";
import { PredictionTicker } from "@/components/PredictionTicker";
import { buildTeamSnapshots, computeStandingsPowerScore, getCurrentStandings } from "@/lib/current";
import { StatCard } from "@/components/StatCard";
import { TeamLogo } from "@/components/TeamLogo";
import standingsSnapshot from "@/data/currentStandings.json";
import insightsData from "@/data/modelInsights.json";
import type { ModelInsights } from "@/types/insights";

type BankrollPoint = ModelInsights["bankrollSeries"][number];

const modelInsights = insightsData as ModelInsights;
const predictionsPayload = getPredictionsPayload();
const todaysPredictions = selectCurrentSlate(predictionsPayload.games);
const teamSnapshots = buildTeamSnapshots();
const snapshotByAbbrev = new Map(teamSnapshots.map((team) => [team.abbrev, team]));
const liveStandings = getCurrentStandings();

const powerStandings = liveStandings
  .map((team) => {
    const overlay = snapshotByAbbrev.get(team.abbrev);
    return {
      ...team,
      record: `${team.wins}-${team.losses}-${team.ot}`,
      overlay,
      powerScore: computeStandingsPowerScore(team),
      nextGame: overlay?.nextGame,
    };
  })
  .sort((a, b) => b.powerScore - a.powerScore)
  .map((team, idx) => ({ ...team, powerRank: idx + 1, movement: team.rank - (idx + 1) }));

const powerLeaders = powerStandings.slice(0, 5);
const bankrollSeries = modelInsights.bankrollSeries;
const finalUnits = bankrollSeries[bankrollSeries.length - 1]?.units || 0;

const updatedTimestamp = predictionsPayload.generatedAt ? new Date(predictionsPayload.generatedAt) : null;
const updatedDisplay = updatedTimestamp
  ? new Intl.DateTimeFormat("en-US", {
      timeZone: "America/New_York",
      hour: "numeric",
      minute: "numeric",
      month: "short",
      day: "numeric",
    }).format(updatedTimestamp)
  : null;

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;
const edge = ((modelInsights.overall.accuracy - modelInsights.overall.baseline) * 100).toFixed(1);

export default function Home() {
  return (
    <div className="min-h-screen">
      <div className="container">
        {/* Hero Section */}
        <section className="section animate-fade-in" style={{ paddingTop: '8rem' }}>
          <div className="max-w-5xl mx-auto text-center">
            <div className="inline-flex items-center gap-3 px-5 py-2.5 rounded-full bg-sky-500/10 border border-sky-500/20 mb-12">
              <div className="w-2 h-2 rounded-full bg-sky-400 animate-pulse-subtle" />
              <span className="text-base font-semibold text-sky-400">AI-Powered NHL Predictions</span>
            </div>

            <h1 className="text-gradient mb-8">
              Know the outcome<br />before puck drop
            </h1>

            <p className="text-xl text-slate-400 leading-relaxed mb-12 max-w-3xl mx-auto">
              Machine learning meets hockey analytics. Daily win probabilities with confidence grades,
              power rankings that actually matter, and transparent model insights.
            </p>

            <div className="flex flex-wrap items-center justify-center gap-6 mb-10">
              <Link href="/predictions" className="btn btn-primary btn-lg">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                View Today's Predictions
              </Link>
              <Link href="https://x.com/puckcastai" target="_blank" className="btn btn-secondary btn-lg">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                </svg>
                Follow Daily Updates
              </Link>
            </div>

            {updatedDisplay && (
              <p className="text-sm text-slate-500">
                Last updated {updatedDisplay} ET
              </p>
            )}
          </div>

          {/* Hero Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-24 max-w-5xl mx-auto stagger-animation">
            <StatCard
              label="Model Accuracy"
              value={pct(modelInsights.overall.accuracy)}
              change={{ value: `+${edge} pts`, isPositive: true }}
              size="lg"
            />
            <StatCard
              label="Games Analyzed"
              value={modelInsights.overall.games.toLocaleString()}
              size="lg"
            />
            <StatCard
              label="ROI Performance"
              value={`+${finalUnits.toFixed(0)}u`}
              change={{ value: "Even money", isPositive: true }}
              size="lg"
            />
          </div>
        </section>

        {/* Live Ticker */}
        <section className="section">
          <div className="mb-12">
            <h2 className="text-gradient-cyan mb-3">Live Prediction Ticker</h2>
            <p className="text-slate-400 text-lg">Auto-refresh edges for tonight's games</p>
          </div>

          <div className="card-elevated animate-slide-up">
            <PredictionTicker initial={predictionsPayload} />
          </div>

          <div className="flex flex-wrap gap-4 mt-8 animate-slide-up" style={{ animationDelay: '100ms' }}>
            <div className="badge badge-confidence-s">
              <span className="font-bold">A+</span>
              <span className="text-xs">≥20pt edge</span>
            </div>
            <div className="badge badge-confidence-a">
              <span className="font-bold">B+</span>
              <span className="text-xs">10-19pt edge</span>
            </div>
            <div className="badge badge-confidence-b">
              <span className="font-bold">C+</span>
              <span className="text-xs">2-9pt edge</span>
            </div>
            <div className="badge badge-confidence-c">
              <span className="font-bold">D/F</span>
              <span className="text-xs">&lt;2pt edge</span>
            </div>
          </div>
        </section>

        {/* Tonight's Games */}
        <section className="section">
          <div className="flex items-end justify-between mb-12">
            <div>
              <h2 className="text-gradient-cyan mb-3">Tonight's Predictions</h2>
              <p className="text-slate-400 text-lg">
                {todaysPredictions.length} {todaysPredictions.length === 1 ? "game" : "games"} with confidence grades
              </p>
            </div>
            <Link href="/predictions" className="btn btn-ghost">
              View All
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>

          {todaysPredictions.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 stagger-animation">
              {todaysPredictions.slice(0, 4).map((prediction) => (
                <PredictionCard key={prediction.id} prediction={prediction} />
              ))}
            </div>
          ) : (
            <div className="card text-center py-16">
              <div className="text-slate-600 text-6xl mb-4">🏒</div>
              <p className="text-xl text-slate-400">No games scheduled today</p>
              <p className="text-sm text-slate-500 mt-2">Check back tomorrow for fresh predictions</p>
            </div>
          )}
        </section>

        {/* Model Performance */}
        <section className="section">
          <div className="mb-12">
            <h2 className="text-gradient-cyan mb-3">Model Performance</h2>
            <p className="text-slate-400 text-lg">Transparent metrics from 1,230 game holdout set</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 mb-12 stagger-animation">
            <StatCard
              label="Test Accuracy"
              value={pct(modelInsights.overall.accuracy)}
              change={{ value: `vs ${pct(modelInsights.overall.baseline)} baseline`, isPositive: true }}
            />
            <StatCard
              label="Log Loss"
              value={modelInsights.overall.logLoss.toFixed(3)}
              change={{ value: "Calibration", isPositive: true }}
            />
            <StatCard
              label="Average Edge"
              value={`${(modelInsights.overall.avgEdge * 100).toFixed(1)}%`}
            />
            <StatCard
              label="Total Profit"
              value={`+${finalUnits.toFixed(0)}u`}
              change={{ value: "Even money", isPositive: true }}
            />
          </div>

          {/* Bankroll Chart */}
          <div className="card-elevated animate-slide-up">
            <div className="flex items-start justify-between mb-8">
              <div>
                <h3 className="text-xl font-bold text-white mb-1">Bankroll Growth</h3>
                <p className="text-sm text-slate-400">Cumulative profit over {bankrollSeries.length} predictions</p>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-gradient-cyan">+{finalUnits.toFixed(0)}u</div>
                <div className="text-sm text-slate-400 mt-1">Final balance</div>
              </div>
            </div>
            <BankrollChart points={bankrollSeries} />
          </div>

          <div className="text-center mt-8">
            <Link href="/performance" className="btn btn-secondary">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              View Full Performance Dashboard
            </Link>
          </div>
        </section>

        {/* Power Rankings Preview */}
        <section className="section">
          <div className="flex items-end justify-between mb-12">
            <div>
              <h2 className="text-gradient-cyan mb-3">Power Rankings</h2>
              <p className="text-slate-400 text-lg">Top 5 teams by model strength</p>
            </div>
            <Link href="/leaderboards" className="btn btn-ghost">
              Full Rankings
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>

          <div className="space-y-6 stagger-animation">
            {powerLeaders.map((team) => {
              const overlay = team.overlay;
              return (
                <div
                  key={team.abbrev}
                  className="card flex items-center justify-between"
                >
                  <div className="flex items-center gap-6">
                    <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-sky-500/20 to-cyan-500/20 border border-sky-500/30">
                      <span className="text-2xl font-bold text-sky-400">
                        {team.powerRank}
                      </span>
                    </div>
                    <TeamLogo teamAbbrev={team.abbrev} teamName={team.team} size="md" showName />
                  </div>

                  <div className="flex items-center gap-8">
                    <div className="text-right">
                      <div className="text-xs text-slate-400 uppercase font-semibold mb-1">Record</div>
                      <div className="text-lg font-bold text-white">{team.record}</div>
                    </div>
                    {overlay && (
                      <div className="text-right">
                        <div className="text-xs text-slate-400 uppercase font-semibold mb-1">Model Win %</div>
                        <div className="text-lg font-bold text-sky-400">{pct(overlay.avgProb)}</div>
                      </div>
                    )}
                    <div className="text-right">
                      <div className="text-xs text-slate-400 uppercase font-semibold mb-1">Goal Diff</div>
                      <div className={`text-lg font-bold ${team.goalDifferential >= 0 ? "text-green-400" : "text-red-400"}`}>
                        {team.goalDifferential >= 0 ? "+" : ""}
                        {team.goalDifferential}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* CTA Section */}
        <section className="section">
          <div className="card-elevated text-center max-w-3xl mx-auto">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-sky-500/20 to-cyan-500/20 border border-sky-500/30 mb-6">
              <svg className="w-8 h-8 text-sky-400" fill="currentColor" viewBox="0 0 24 24">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
              </svg>
            </div>

            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Stay ahead of the game
            </h2>
            <p className="text-lg text-slate-400 leading-relaxed mb-8 max-w-2xl mx-auto">
              Get daily prediction summaries, goalie confirmations, and model insights delivered to your timeline.
            </p>
            <Link
              href="https://x.com/puckcastai"
              target="_blank"
              className="btn btn-primary btn-lg"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
              </svg>
              Follow @puckcastai
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}

function BankrollChart({ points }: { points: BankrollPoint[] }) {
  if (!points.length) {
    return <p className="text-sm text-slate-400">No bankroll history available.</p>;
  }

  const max = Math.max(...points.map((p) => p.units));
  const min = Math.min(...points.map((p) => p.units));
  const range = max - min;
  const span = Math.max(points.length - 1, 1);

  const normalized = points.map((point, idx) => ({
    x: (idx / span) * 100,
    y: range === 0 ? 50 : ((point.units - min) / range) * 80 + 10,
  }));

  const path = normalized
    .map((point, idx) => `${idx === 0 ? "M" : "L"} ${point.x} ${100 - point.y}`)
    .join(" ");

  const areaPath = `${path} L 100 100 L 0 100 Z`;

  return (
    <div className="relative">
      <svg viewBox="0 0 100 100" className="w-full h-40" preserveAspectRatio="none">
        {/* Gradient definition */}
        <defs>
          <linearGradient id="bankrollGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="rgb(59, 130, 246)" stopOpacity="0.3" />
            <stop offset="100%" stopColor="rgb(6, 182, 212)" stopOpacity="0.05" />
          </linearGradient>
        </defs>

        {/* Area fill */}
        <path d={areaPath} fill="url(#bankrollGradient)" />

        {/* Line stroke */}
        <path
          d={path}
          fill="none"
          stroke="rgb(6, 182, 212)"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}
