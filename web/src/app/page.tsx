import Link from "next/link";
import { getPredictionsPayload, selectCurrentSlate, getModelInsights } from "@/lib/data";

const predictions = getPredictionsPayload();
const todaysGames = selectCurrentSlate(predictions.games);
const insights = getModelInsights();

// Get top 3 predictions by edge
const topPredictions = [...todaysGames]
  .sort((a, b) => b.edge - a.edge)
  .slice(0, 3);

const formatTime = (timeStr: string | null) => {
  if (!timeStr) return "TBD";
  return timeStr;
};

const formatProb = (prob: number) => `${Math.round(prob * 100)}%`;

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-950">
      {/* Hero Section */}
      <section className="relative overflow-hidden border-b border-slate-800/50 bg-gradient-to-b from-slate-900/50 to-slate-950 px-6 py-20 sm:py-32">
        <div className="relative mx-auto max-w-5xl">
          <div className="text-center">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-4 py-1.5">
              <div className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
              <span className="text-sm font-medium text-emerald-400">Live for 2025-26</span>
            </div>

            <h1 className="mb-6 text-5xl font-bold tracking-tight text-white sm:text-6xl md:text-7xl">
              NHL Prediction Model
            </h1>

            <p className="mx-auto mb-10 max-w-2xl text-xl leading-relaxed text-slate-300">
              Machine learning predictions for every NHL game.
              Daily probabilities, confidence grades, and transparent performance metrics.
            </p>

            <div className="flex flex-wrap justify-center gap-4">
              <Link
                href="/predictions"
                className="inline-flex items-center gap-2 rounded-lg bg-white px-8 py-3.5 text-base font-semibold text-slate-950 transition-all hover:bg-slate-100"
              >
                View Today's Predictions
                <span>→</span>
              </Link>
              <Link
                href="https://x.com/puckcastai"
                target="_blank"
                className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-900/50 px-8 py-3.5 text-base font-semibold text-white backdrop-blur transition-all hover:border-slate-600 hover:bg-slate-800/50"
              >
                Follow Updates
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Model Stats */}
      <section className="border-b border-slate-800/50 px-6 py-16">
        <div className="mx-auto max-w-6xl">
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-lg border border-slate-800/50 bg-slate-900/30 p-6">
              <div className="text-sm font-medium uppercase tracking-wide text-slate-400">Accuracy</div>
              <div className="mt-2 text-4xl font-bold text-white">{formatProb(insights.overall.accuracy)}</div>
              <div className="mt-1 text-sm text-slate-500">Test holdout</div>
            </div>

            <div className="rounded-lg border border-slate-800/50 bg-slate-900/30 p-6">
              <div className="text-sm font-medium uppercase tracking-wide text-slate-400">Edge</div>
              <div className="mt-2 text-4xl font-bold text-emerald-400">
                +{((insights.overall.accuracy - insights.overall.baseline) * 100).toFixed(1)} pts
              </div>
              <div className="mt-1 text-sm text-slate-500">vs baseline</div>
            </div>

            <div className="rounded-lg border border-slate-800/50 bg-slate-900/30 p-6">
              <div className="text-sm font-medium uppercase tracking-wide text-slate-400">Games</div>
              <div className="mt-2 text-4xl font-bold text-white">{insights.overall.games.toLocaleString()}</div>
              <div className="mt-1 text-sm text-slate-500">2023-24 season</div>
            </div>

            <div className="rounded-lg border border-slate-800/50 bg-slate-900/30 p-6">
              <div className="text-sm font-medium uppercase tracking-wide text-slate-400">Log Loss</div>
              <div className="mt-2 text-4xl font-bold text-white">{insights.overall.logLoss.toFixed(3)}</div>
              <div className="mt-1 text-sm text-slate-500">Calibration</div>
            </div>
          </div>
        </div>
      </section>

      {/* Today's Top Predictions */}
      <section className="px-6 py-16">
        <div className="mx-auto max-w-6xl">
          <div className="mb-10">
            <h2 className="text-3xl font-bold text-white">Today's Top Edges</h2>
            <p className="mt-2 text-lg text-slate-400">
              {todaysGames.length} games • Sorted by model confidence
            </p>
          </div>

          {topPredictions.length > 0 ? (
            <div className="space-y-4">
              {topPredictions.map((game) => {
                const favorite = game.modelFavorite === "home" ? game.homeTeam : game.awayTeam;
                const underdog = game.modelFavorite === "home" ? game.awayTeam : game.homeTeam;
                const favoriteProb = game.modelFavorite === "home" ? game.homeWinProb : game.awayWinProb;

                return (
                  <div
                    key={game.id}
                    className="group overflow-hidden rounded-lg border border-slate-800/50 bg-slate-900/30 transition-all hover:border-slate-700 hover:bg-slate-900/50"
                  >
                    <div className="flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
                      <div className="flex-1">
                        <div className="mb-3 flex items-center gap-3">
                          <span className="inline-flex items-center rounded-md bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-400">
                            GRADE {game.confidenceGrade}
                          </span>
                          <span className="text-sm text-slate-500">{formatTime(game.startTimeEt)}</span>
                        </div>

                        <div className="space-y-2">
                          <div className="flex items-baseline gap-3">
                            <span className="text-2xl font-bold text-white">{favorite.name}</span>
                            <span className="text-lg font-semibold text-emerald-400">{formatProb(favoriteProb)}</span>
                          </div>
                          <div className="flex items-baseline gap-3">
                            <span className="text-xl text-slate-400">{underdog.name}</span>
                            <span className="text-base text-slate-500">{formatProb(1 - favoriteProb)}</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex flex-col items-end justify-center gap-1 sm:min-w-[120px]">
                        <div className="text-sm font-medium uppercase tracking-wide text-slate-400">Edge</div>
                        <div className="text-3xl font-bold text-white">+{Math.round(game.edge * 100)}</div>
                        <div className="text-xs text-slate-500">pts over 50%</div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="rounded-lg border border-slate-800/50 bg-slate-900/30 p-12 text-center">
              <p className="text-lg text-slate-400">No games today. Check back tomorrow.</p>
            </div>
          )}

          <div className="mt-8 text-center">
            <Link
              href="/predictions"
              className="inline-flex items-center gap-2 text-base font-semibold text-white transition-colors hover:text-slate-300"
            >
              View All {todaysGames.length} Predictions
              <span className="transition-transform group-hover:translate-x-1">→</span>
            </Link>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="border-t border-slate-800/50 bg-slate-900/20 px-6 py-16">
        <div className="mx-auto max-w-6xl">
          <h2 className="mb-10 text-center text-3xl font-bold text-white">How It Works</h2>

          <div className="grid gap-8 md:grid-cols-3">
            <div className="text-center">
              <div className="mb-4 text-4xl">📊</div>
              <h3 className="mb-2 text-xl font-semibold text-white">Data Collection</h3>
              <p className="text-slate-400">
                Real-time stats, standings, rest days, and goalie confirmations for every team.
              </p>
            </div>

            <div className="text-center">
              <div className="mb-4 text-4xl">🤖</div>
              <h3 className="mb-2 text-xl font-semibold text-white">ML Prediction</h3>
              <p className="text-slate-400">
                Logistic regression model trained on full 2023-24 season with holdout testing.
              </p>
            </div>

            <div className="text-center">
              <div className="mb-4 text-4xl">✅</div>
              <h3 className="mb-2 text-xl font-semibold text-white">Confidence Grading</h3>
              <p className="text-slate-400">
                Each prediction gets a letter grade based on edge over 50/50 baseline.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
