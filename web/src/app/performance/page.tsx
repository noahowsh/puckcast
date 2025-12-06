import insightsData from "@/data/modelInsights.json";
import type { ModelInsights } from "@/types/insights";

const modelInsights = insightsData as ModelInsights;
const overview = modelInsights.overall;
const confidenceBuckets = modelInsights.confidenceBuckets;
const strategies = modelInsights.strategies;
const seasonBreakdown = modelInsights.seasonBreakdown ?? [];
const featureImportance = modelInsights.featureImportance ?? [];

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

export default function PerformancePage() {
  const edge = ((overview.accuracy - overview.baseline) * 100).toFixed(1);
  const correct = Math.round(overview.accuracy * overview.games);
  const incorrect = overview.games - correct;

  // Calculate averages across seasons
  const avgAccuracy = seasonBreakdown.length > 0
    ? seasonBreakdown.reduce((sum, s) => sum + s.accuracy, 0) / seasonBreakdown.length
    : overview.accuracy;
  const avgLogLoss = seasonBreakdown.length > 0
    ? seasonBreakdown.reduce((sum, s) => sum + s.logLoss, 0) / seasonBreakdown.length
    : overview.logLoss;

  return (
    <div className="min-h-screen">
      <div className="container">
        {/* Hero Section - Simplified */}
        <section className="nova-hero nav-offset">
          <div className="max-w-4xl">
            <div className="pill-row mb-6">
              <span className="pill">Model Performance</span>
              <span className="pill">V7.9</span>
            </div>
            <h1 className="display-xl mb-4">Does the model work?</h1>
            <p className="lead mb-8">
              Yes. Tested on {overview.games.toLocaleString()} holdout games across multiple NHL seasons.
              We measure accuracy, calibration, and edge — and share everything transparently.
            </p>

            {/* Core Stats - Clean 3-column */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="card text-center">
                <p className="text-sm text-white/60 uppercase tracking-wider mb-2">Test Accuracy</p>
                <p className="text-5xl font-bold text-white mb-1">{pct(overview.accuracy)}</p>
                <p className="text-sm text-sky-400">+{edge} pts vs baseline</p>
              </div>
              <div className="card text-center">
                <p className="text-sm text-white/60 uppercase tracking-wider mb-2">Log Loss</p>
                <p className="text-5xl font-bold text-white mb-1">{overview.logLoss.toFixed(3)}</p>
                <p className="text-sm text-sky-400">Lower is better</p>
              </div>
              <div className="card text-center">
                <p className="text-sm text-white/60 uppercase tracking-wider mb-2">Avg Edge</p>
                <p className="text-5xl font-bold text-white mb-1">{(overview.avgEdge * 100).toFixed(1)}</p>
                <p className="text-sm text-sky-400">Points per prediction</p>
              </div>
            </div>

            {/* Secondary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white/5 rounded-lg p-4 text-center">
                <p className="text-2xl font-bold text-white">{overview.games.toLocaleString()}</p>
                <p className="text-xs text-white/60">Games tested</p>
              </div>
              <div className="bg-white/5 rounded-lg p-4 text-center">
                <p className="text-2xl font-bold text-emerald-400">{correct.toLocaleString()}</p>
                <p className="text-xs text-white/60">Correct picks</p>
              </div>
              <div className="bg-white/5 rounded-lg p-4 text-center">
                <p className="text-2xl font-bold text-rose-400">{incorrect.toLocaleString()}</p>
                <p className="text-xs text-white/60">Incorrect picks</p>
              </div>
              <div className="bg-white/5 rounded-lg p-4 text-center">
                <p className="text-2xl font-bold text-white">{pct(overview.baseline)}</p>
                <p className="text-xs text-white/60">Baseline (home wins)</p>
              </div>
            </div>
          </div>
        </section>

        {/* Metrics Explained Section */}
        <section className="nova-section">
          <div className="section-head mb-8">
            <p className="eyebrow">Understanding the numbers</p>
            <h2>What these metrics mean</h2>
            <p className="lead-sm">Plain-English explanations for the stats that matter.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-lg bg-sky-500/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-2xl">🎯</span>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white mb-2">Accuracy ({pct(overview.accuracy)})</h3>
                  <p className="text-sm text-white/70 leading-relaxed">
                    The percentage of games where our predicted winner actually won. If we pick 100 games,
                    we get about {Math.round(overview.accuracy * 100)} right. The NHL baseline (always picking
                    home team) is ~54%, so we beat that by {edge} percentage points.
                  </p>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-lg bg-amber-500/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-2xl">📊</span>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white mb-2">Log Loss ({overview.logLoss.toFixed(3)})</h3>
                  <p className="text-sm text-white/70 leading-relaxed">
                    Measures how well-calibrated our probabilities are. A model saying &quot;60% chance&quot; should
                    be right about 60% of the time, not 80% or 40%. Lower log loss = better calibration.
                    Perfect would be 0, random guessing is ~0.693. Our {overview.logLoss.toFixed(3)} shows strong calibration.
                  </p>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-lg bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-2xl">📈</span>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white mb-2">Edge ({(overview.avgEdge * 100).toFixed(1)} pts)</h3>
                  <p className="text-sm text-white/70 leading-relaxed">
                    How far our prediction is from 50/50. A 65% pick has a 15-point edge. Higher edge =
                    more confident prediction. We grade picks A+ through C based on edge size. A+ picks
                    (≥25 pts) hit at 71.5% — that&apos;s where the model shines brightest.
                  </p>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-lg bg-purple-500/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-2xl">⚖️</span>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white mb-2">Brier Score ({overview.brier.toFixed(3)})</h3>
                  <p className="text-sm text-white/70 leading-relaxed">
                    Another calibration metric measuring the mean squared error of predictions. Ranges
                    from 0 (perfect) to 1 (worst). Below 0.25 is considered good for binary outcomes like
                    win/loss. Our {overview.brier.toFixed(3)} indicates well-calibrated probability estimates.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Season Breakdown */}
        {seasonBreakdown.length > 0 && (
          <section className="nova-section">
            <div className="section-head mb-8">
              <p className="eyebrow">Historical performance</p>
              <h2>Accuracy by season</h2>
              <p className="lead-sm">How the model performed across different NHL seasons.</p>
            </div>

            <div className="card-elevated">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
                {seasonBreakdown.map((season) => (
                  <div key={season.season} className="text-center p-4 bg-white/5 rounded-lg">
                    <p className="text-sm text-white/60 mb-1">{season.season}</p>
                    <p className="text-3xl font-bold text-white mb-1">{pct(season.accuracy)}</p>
                    <p className="text-xs text-white/50">{season.games.toLocaleString()} games</p>
                    <p className="text-xs text-sky-400 mt-1">+{((season.accuracy - season.baseline) * 100).toFixed(1)} vs baseline</p>
                  </div>
                ))}
              </div>

              <div className="border-t border-white/10 pt-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                  <div>
                    <p className="text-sm text-white/60">Avg Accuracy</p>
                    <p className="text-2xl font-bold text-white">{pct(avgAccuracy)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-white/60">Avg Log Loss</p>
                    <p className="text-2xl font-bold text-white">{avgLogLoss.toFixed(3)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-white/60">Total Games</p>
                    <p className="text-2xl font-bold text-white">
                      {seasonBreakdown.reduce((sum, s) => sum + s.games, 0).toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-white/60">Seasons Tested</p>
                    <p className="text-2xl font-bold text-white">{seasonBreakdown.length}</p>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Edge Bands - 6 Clear Grades */}
        <section className="nova-section">
          <div className="section-head mb-8">
            <p className="eyebrow">Confidence grading</p>
            <h2>The 6 edge bands</h2>
            <p className="lead-sm">
              We grade every prediction A+ through C based on edge size. Higher grades = higher confidence = higher accuracy.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {confidenceBuckets.map((bucket) => {
              const isATier = bucket.grade.startsWith("A");
              const isBTier = bucket.grade.startsWith("B");
              const isCTier = bucket.grade.startsWith("C");

              return (
                <div
                  key={bucket.grade}
                  className={`card relative overflow-hidden ${
                    isATier ? "border-sky-500/30 bg-sky-500/5" :
                    isBTier ? "border-amber-500/30 bg-amber-500/5" :
                    "border-white/10"
                  }`}
                >
                  {/* Grade badge */}
                  <div className="flex items-center justify-between mb-4">
                    <span className={`
                      px-3 py-1.5 rounded-lg text-sm font-bold
                      ${isATier ? "bg-sky-500 text-white" : ""}
                      ${isBTier ? "bg-amber-500 text-black" : ""}
                      ${isCTier ? "bg-white/20 text-white" : ""}
                    `}>
                      Grade {bucket.grade}
                    </span>
                    <span className="text-sm text-white/60">{bucket.label}</span>
                  </div>

                  {/* Accuracy */}
                  <div className="mb-3">
                    <p className="text-4xl font-bold text-white">{pct(bucket.accuracy)}</p>
                    <p className="text-sm text-white/60">accuracy</p>
                  </div>

                  {/* Stats */}
                  <div className="flex items-center gap-4 text-sm text-white/70 mb-3">
                    <span>{bucket.count.toLocaleString()} games</span>
                    <span>·</span>
                    <span>{((bucket.coverage ?? 0) * 100).toFixed(0)}% of picks</span>
                  </div>

                  {/* Description */}
                  {bucket.description && (
                    <p className="text-xs text-white/50 italic">{bucket.description}</p>
                  )}

                  {/* Accuracy bar */}
                  <div className="mt-4 h-2 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        isATier ? "bg-sky-500" :
                        isBTier ? "bg-amber-500" :
                        "bg-white/30"
                      }`}
                      style={{ width: `${bucket.accuracy * 100}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Grade Legend */}
          <div className="mt-8 card bg-white/5">
            <h3 className="text-lg font-bold text-white mb-4">How to read the grades</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div className="flex items-start gap-3">
                <span className="px-2 py-1 bg-sky-500 text-white rounded font-bold text-xs">A+/A</span>
                <p className="text-white/70">
                  <strong className="text-white">High confidence.</strong> These are our best picks —
                  the model sees a clear edge. Worth paying attention to.
                </p>
              </div>
              <div className="flex items-start gap-3">
                <span className="px-2 py-1 bg-amber-500 text-black rounded font-bold text-xs">B+/B</span>
                <p className="text-white/70">
                  <strong className="text-white">Medium confidence.</strong> The model leans one way
                  but with less conviction. Decent edge, not elite.
                </p>
              </div>
              <div className="flex items-start gap-3">
                <span className="px-2 py-1 bg-white/20 text-white rounded font-bold text-xs">C+/C</span>
                <p className="text-white/70">
                  <strong className="text-white">Low confidence.</strong> Near coin-flip territory.
                  The model doesn&apos;t see much separating the teams.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Strategy Receipts */}
        <section className="nova-section">
          <div className="section-head mb-8">
            <p className="eyebrow">Backtest results</p>
            <h2>Strategy receipts</h2>
            <p className="lead-sm">
              Historical performance of different filtering strategies. For transparency only — not betting advice.
            </p>
          </div>

          <div className="card-elevated">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-white/60">Strategy</th>
                    <th className="text-center py-3 px-4 text-sm font-semibold text-white/60">Games</th>
                    <th className="text-center py-3 px-4 text-sm font-semibold text-white/60">Win Rate</th>
                    <th className="text-center py-3 px-4 text-sm font-semibold text-white/60">Avg Edge</th>
                    <th className="text-right py-3 px-4 text-sm font-semibold text-white/60">Units (flat)</th>
                  </tr>
                </thead>
                <tbody>
                  {strategies.map((strategy, idx) => {
                    const isProfitable = strategy.units > 0;
                    return (
                      <tr
                        key={strategy.name}
                        className={`border-b border-white/5 ${idx === 0 ? "bg-white/5" : ""}`}
                      >
                        <td className="py-4 px-4">
                          <p className="font-semibold text-white">{strategy.name}</p>
                          <p className="text-xs text-white/50">{strategy.note}</p>
                        </td>
                        <td className="py-4 px-4 text-center text-white/80">
                          {strategy.bets.toLocaleString()}
                        </td>
                        <td className="py-4 px-4 text-center">
                          <span className={`font-semibold ${
                            strategy.winRate >= 0.60 ? "text-emerald-400" :
                            strategy.winRate >= 0.55 ? "text-sky-400" :
                            "text-white/80"
                          }`}>
                            {pct(strategy.winRate)}
                          </span>
                        </td>
                        <td className="py-4 px-4 text-center text-white/80">
                          {(strategy.avgEdge * 100).toFixed(1)} pts
                        </td>
                        <td className="py-4 px-4 text-right">
                          <span className={`font-bold ${isProfitable ? "text-emerald-400" : "text-rose-400"}`}>
                            {isProfitable ? "+" : ""}{strategy.units.toFixed(0)}u
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="mt-6 p-4 rounded-lg border border-amber-500/30 bg-amber-500/10">
              <p className="text-sm text-amber-200">
                <strong>Important:</strong> These results assume flat 1-unit bets at even money (-110/+100).
                Real-world results vary with odds, bankroll management, and market conditions.
                This is not betting advice — we share this data for transparency and model validation only.
              </p>
            </div>
          </div>
        </section>

        {/* Top Features */}
        {featureImportance.length > 0 && (
          <section className="nova-section">
            <div className="section-head mb-8">
              <p className="eyebrow">Under the hood</p>
              <h2>What drives predictions</h2>
              <p className="lead-sm">The most influential features in the V7.9 model.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {featureImportance.slice(0, 6).map((feature, idx) => (
                <div key={feature.feature} className="card bg-white/5">
                  <div className="flex items-start gap-3">
                    <span className="w-8 h-8 rounded-lg bg-sky-500/20 flex items-center justify-center text-sky-400 font-bold text-sm">
                      #{idx + 1}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-white text-sm truncate">{feature.feature}</p>
                      <p className="text-xs text-white/60 mt-1">{feature.description}</p>
                      <div className="mt-2 flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-sky-500 rounded-full"
                            style={{ width: `${(feature.absImportance / featureImportance[0].absImportance) * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-white/50">{feature.absImportance.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
