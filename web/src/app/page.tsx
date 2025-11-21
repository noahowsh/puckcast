import Link from "next/link";
import { PredictionCard } from "@/components/PredictionCard";
import { getGoaliePulse, getPredictionsPayload, selectCurrentSlate } from "@/lib/data";
import { PredictionTicker } from "@/components/PredictionTicker";
import { buildTeamSnapshots, computeStandingsPowerScore, getCurrentStandings } from "@/lib/current";
import standingsSnapshot from "@/data/currentStandings.json";
import insightsData from "@/data/modelInsights.json";
import type { ModelInsights } from "@/types/insights";

type BankrollPoint = ModelInsights["bankrollSeries"][number];

const modelInsights = insightsData as ModelInsights;
const standingsMeta = standingsSnapshot as { generatedAt?: string };
const predictionsPayload = getPredictionsPayload();
const todaysPredictions = selectCurrentSlate(predictionsPayload.games);
const goaliePulse = getGoaliePulse();
const teamSnapshots = buildTeamSnapshots();
const snapshotByAbbrev = new Map(teamSnapshots.map((team) => [team.abbrev, team]));
const liveStandings = getCurrentStandings();
const topStandings = liveStandings.slice(0, 3);
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
const powerLeaders = powerStandings.slice(0, 6);
const bankrollPreview = modelInsights.bankrollSeries.slice(-12);

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

const shortDateFormatter = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" });
const formatShortDate = (iso?: string | null) => {
  if (!iso) return "TBD";
  return shortDateFormatter.format(new Date(`${iso}T00:00:00Z`));
};

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

const heroStats = [
  { label: "Season", value: "2025-26", detail: "Live tracking" },
  { label: "Accuracy", value: pct(modelInsights.overall.accuracy), detail: "Test holdout" },
  { label: "Edge", value: `+${((modelInsights.overall.accuracy - modelInsights.overall.baseline) * 100).toFixed(1)} pts`, detail: "vs baseline" },
];

const gradeLegend = [
  { label: "A+", detail: "≥20 pts edge" },
  { label: "B+", detail: "10-19 pts edge" },
  { label: "C+", detail: "2-9 pts edge" },
  { label: "C", detail: "<2 pts edge" },
];

export default function Home() {
  return (
    <div className="relative min-h-screen bg-slate-950">
      {/* Premium background gradient */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-b from-slate-900/50 via-slate-950 to-slate-950" />
      </div>

      <div className="relative mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8 lg:py-24">
        {/* Hero Section */}
        <section className="mb-24 lg:mb-32">
          <div className="mx-auto max-w-4xl text-center">
            <div className="mb-6 inline-flex items-center gap-2.5 rounded-full border border-sky-500/20 bg-sky-500/5 px-4 py-2">
              <div className="h-2 w-2 animate-pulse rounded-full bg-sky-400" />
              <span className="text-xs font-semibold uppercase tracking-wider text-sky-400">AI-Powered NHL Predictions</span>
            </div>

            <h1 className="mb-6 text-5xl font-bold leading-tight tracking-tight text-white sm:text-6xl lg:text-7xl">
              Know the outcome<br />before puck drop
            </h1>

            <p className="mx-auto mb-8 max-w-2xl text-lg leading-relaxed text-slate-300 sm:text-xl">
              Machine learning meets hockey analytics. Daily win probabilities with confidence grades,
              power rankings that actually matter, and transparent model insights.
            </p>

            <div className="flex flex-wrap justify-center gap-3">
              <Link
                href="https://x.com/puckcastai"
                target="_blank"
                className="group inline-flex items-center gap-2 rounded-lg bg-sky-500 px-6 py-3 text-base font-semibold text-white shadow-lg shadow-sky-500/25 transition-all hover:bg-sky-400 hover:shadow-xl hover:shadow-sky-500/30"
              >
                Follow Daily Updates
              </Link>
              <Link
                href="/predictions"
                className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-900/50 px-6 py-3 text-base font-semibold text-white backdrop-blur-sm transition-all hover:border-slate-600 hover:bg-slate-800/50"
              >
                View Predictions
              </Link>
            </div>

            {updatedDisplay && (
              <p className="mt-6 text-sm text-slate-500">
                Last updated {updatedDisplay} ET
              </p>
            )}
          </div>

          {/* Hero Stats */}
          <div className="mt-16 grid gap-6 sm:grid-cols-3 lg:mt-20">
            {heroStats.map((stat) => (
              <div key={stat.label} className="group rounded-xl border border-slate-800/50 bg-slate-900/30 p-6 backdrop-blur-sm transition-all hover:border-slate-700 hover:bg-slate-900/50">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{stat.label}</p>
                <p className="mt-3 text-3xl font-bold text-white lg:text-4xl">{stat.value}</p>
                <p className="mt-1.5 text-sm text-slate-500">{stat.detail}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Live Edges */}
        <section className="mb-24 lg:mb-32">
          <div className="mb-8 text-center lg:mb-10">
            <h2 className="mb-3 text-3xl font-bold text-white lg:text-4xl">Live Edges</h2>
            <p className="text-base text-slate-400 lg:text-lg">Auto-refresh prediction ticker</p>
          </div>

          <div className="mb-6 flex flex-wrap justify-center gap-2">
            {gradeLegend.map((g) => (
              <div key={g.label} className="inline-flex items-center gap-2 rounded-lg border border-slate-800/50 bg-slate-900/30 px-3 py-1.5 backdrop-blur-sm">
                <span className="text-sm font-bold text-white">{g.label}</span>
                <span className="text-xs text-slate-500">{g.detail}</span>
              </div>
            ))}
          </div>

          <div className="overflow-hidden rounded-xl border border-slate-800/50 bg-slate-900/30 shadow-xl shadow-black/20">
            <PredictionTicker initial={predictionsPayload} />
          </div>
        </section>

        {/* Today's Predictions */}
        <section className="mb-24 lg:mb-32">
          <div className="mb-8 text-center lg:mb-10">
            <h2 className="mb-3 text-3xl font-bold text-white lg:text-4xl">Tonight's Predictions</h2>
            <p className="text-base text-slate-400 lg:text-lg">
              {todaysPredictions.length} {todaysPredictions.length === 1 ? "game" : "games"} with confidence grades
            </p>
          </div>

          {todaysPredictions.length > 0 ? (
            <div className="grid gap-6 md:grid-cols-2 lg:gap-8">
              {todaysPredictions.map((prediction) => (
                <PredictionCard key={prediction.id} prediction={prediction} />
              ))}
            </div>
          ) : (
            <div className="rounded-xl border border-slate-800/50 bg-slate-900/30 p-12 text-center backdrop-blur-sm lg:p-16">
              <p className="text-lg text-slate-400">No games scheduled. Check back tomorrow.</p>
            </div>
          )}
        </section>

        {/* Model Performance */}
        <section className="mb-24 lg:mb-32">
          <div className="mb-8 text-center lg:mb-10">
            <h2 className="mb-3 text-3xl font-bold text-white lg:text-4xl">Model Health</h2>
            <p className="text-base text-slate-400 lg:text-lg">Season-long vitals at a glance</p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl border border-slate-800/50 bg-slate-900/30 p-6 backdrop-blur-sm">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Games Tracked</p>
              <p className="mt-3 text-3xl font-bold text-white lg:text-4xl">{modelInsights.overall.games.toLocaleString()}</p>
              <p className="mt-1.5 text-sm text-slate-500">2023-24 season</p>
            </div>

            <div className="rounded-xl border border-slate-800/50 bg-slate-900/30 p-6 backdrop-blur-sm">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Model Accuracy</p>
              <p className="mt-3 text-3xl font-bold text-white lg:text-4xl">{pct(modelInsights.overall.accuracy)}</p>
              <p className="mt-1.5 text-sm text-slate-500">vs actual results</p>
            </div>

            <div className="rounded-xl border border-slate-800/50 bg-slate-900/30 p-6 backdrop-blur-sm">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Home Baseline</p>
              <p className="mt-3 text-3xl font-bold text-white lg:text-4xl">{pct(modelInsights.overall.baseline)}</p>
              <p className="mt-1.5 text-sm text-slate-500">Always pick home</p>
            </div>

            <div className="rounded-xl border border-slate-800/50 bg-slate-900/30 p-6 backdrop-blur-sm">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Log Loss</p>
              <p className="mt-3 text-3xl font-bold text-white lg:text-4xl">{modelInsights.overall.logLoss.toFixed(3)}</p>
              <p className="mt-1.5 text-sm text-slate-500">Probability calibration</p>
            </div>
          </div>

          {/* Bankroll Chart */}
          <div className="mt-6 rounded-xl border border-slate-800/50 bg-slate-900/30 p-6 backdrop-blur-sm lg:p-8">
            <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-lg font-bold text-white">Bankroll Trace</p>
                <p className="mt-1 text-sm text-slate-500">Even-money assumption · audit sample</p>
              </div>
              <p className="text-2xl font-bold text-sky-400 sm:text-3xl">
                +{bankrollPreview[bankrollPreview.length - 1]?.units.toFixed(0)}u
              </p>
            </div>
            <BankrollSparkline points={bankrollPreview} />
          </div>
        </section>

        {/* Top Teams */}
        <section className="mb-24 lg:mb-32">
          <div className="mb-8 text-center lg:mb-10">
            <h2 className="mb-3 text-3xl font-bold text-white lg:text-4xl">Power Rankings</h2>
            <p className="text-base text-slate-400 lg:text-lg">Top clubs by live power score</p>
          </div>

          <div className="grid gap-4 lg:gap-6">
            {powerLeaders.map((team) => {
              const overlay = team.overlay;
              return (
                <div
                  key={team.abbrev}
                  className="flex items-center justify-between rounded-xl border border-slate-800/50 bg-slate-900/30 p-6 backdrop-blur-sm transition-all hover:border-slate-700 hover:bg-slate-900/50 lg:p-8"
                >
                  <div className="flex items-center gap-4 lg:gap-8">
                    <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-lg bg-sky-500/10 text-xl font-bold text-sky-400 lg:h-14 lg:w-14 lg:text-2xl">
                      {team.powerRank}
                    </div>
                    <div>
                      <p className="text-lg font-bold text-white lg:text-xl">{team.team}</p>
                      <p className="mt-0.5 text-sm text-slate-400">
                        {team.record} · {team.points} pts
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-6 lg:gap-12">
                    {overlay && (
                      <div className="hidden text-right sm:block">
                        <p className="text-xs font-semibold text-slate-400">Model Win %</p>
                        <p className="mt-1 text-lg font-bold text-white lg:text-xl">{pct(overlay.avgProb)}</p>
                      </div>
                    )}
                    <div className="text-right">
                      <p className="text-xs font-semibold text-slate-400">Goal Diff</p>
                      <p className={`mt-1 text-lg font-bold lg:text-xl ${team.goalDifferential >= 0 ? "text-sky-400" : "text-slate-400"}`}>
                        {team.goalDifferential >= 0 ? "+" : ""}
                        {team.goalDifferential}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-8 text-center">
            <Link
              href="/leaderboards"
              className="group inline-flex items-center gap-2 text-base font-semibold text-sky-400 transition-colors hover:text-sky-300 lg:text-lg"
            >
              View All Rankings
              <span className="transition-transform group-hover:translate-x-1">→</span>
            </Link>
          </div>
        </section>

        {/* CTA Section */}
        <section className="rounded-xl border border-sky-500/20 bg-gradient-to-br from-sky-500/5 to-slate-900/30 p-12 text-center backdrop-blur-sm lg:p-16">
          <h2 className="text-3xl font-bold text-white lg:text-4xl">Stay ahead of the game</h2>
          <p className="mx-auto mt-4 max-w-2xl text-base text-slate-300 lg:text-lg">
            Get daily prediction summaries, goalie confirmations, and model insights delivered to your timeline.
          </p>
          <Link
            href="https://x.com/puckcastai"
            target="_blank"
            className="mt-8 inline-flex items-center gap-2 rounded-lg bg-sky-500 px-8 py-3.5 text-base font-semibold text-white shadow-lg shadow-sky-500/25 transition-all hover:bg-sky-400 hover:shadow-xl hover:shadow-sky-500/30 lg:text-lg"
          >
            Follow @puckcastai
          </Link>
        </section>
      </div>
    </div>
  );
}

function BankrollSparkline({ points }: { points: BankrollPoint[] }) {
  if (!points.length) {
    return <p className="text-sm text-slate-400">No bankroll history available.</p>;
  }
  const max = Math.max(...points.map((point) => point.units));
  const min = Math.min(...points.map((point) => point.units));
  const span = Math.max(points.length - 1, 1);
  const normalized = points.map((point, idx) => ({
    x: (idx / span) * 100,
    y: max === min ? 50 : ((point.units - min) / (max - min)) * 100,
  }));
  const path = normalized.map((point, idx) => `${idx === 0 ? "M" : "L"} ${point.x} ${100 - point.y}`).join(" ");

  return (
    <svg viewBox="0 0 100 100" className="h-32 w-full" preserveAspectRatio="none">
      <path d={path} fill="none" stroke="#38bdf8" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
