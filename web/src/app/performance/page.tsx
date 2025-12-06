import insightsData from "@/data/modelInsights.json";
import type { ModelInsights } from "@/types/insights";

const modelInsights = insightsData as ModelInsights;
const overview = modelInsights.overall;
const confidenceBuckets = modelInsights.confidenceBuckets;
const strategies = modelInsights.strategies;
const seasonBreakdown = modelInsights.seasonBreakdown ?? [];

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

export default function PerformancePage() {
  const edge = ((overview.accuracy - overview.baseline) * 100).toFixed(1);
  const correct = Math.round(overview.accuracy * overview.games);
  const incorrect = overview.games - correct;

  return (
    <div className="min-h-screen">
      <div className="container">
        {/* Hero */}
        <section className="nova-hero nav-offset">
          <div className="nova-hero__grid">
            <div className="nova-hero__text">
              <div className="pill-row">
                <span className="pill">Model Performance</span>
                <span className="pill">V7.9</span>
              </div>
              <h1 className="display-xl">Does the model work?</h1>
              <p className="lead">
                Yes. Tested on {overview.games.toLocaleString()} holdout games across multiple NHL seasons.
                We measure accuracy, calibration, and edge — transparency first.
              </p>
              <div className="stat-grid">
                <div className="stat-tile">
                  <p className="stat-tile__label">Test accuracy</p>
                  <p className="stat-tile__value">{pct(overview.accuracy)}</p>
                  <p className="stat-tile__detail">+{edge} pts vs baseline</p>
                </div>
                <div className="stat-tile">
                  <p className="stat-tile__label">Baseline</p>
                  <p className="stat-tile__value">{pct(overview.baseline)}</p>
                  <p className="stat-tile__detail">Home/away prior</p>
                </div>
                <div className="stat-tile">
                  <p className="stat-tile__label">Avg edge</p>
                  <p className="stat-tile__value">{(overview.avgEdge * 100).toFixed(1)} pts</p>
                  <p className="stat-tile__detail">Per prediction</p>
                </div>
                <div className="stat-tile">
                  <p className="stat-tile__label">Holdout size</p>
                  <p className="stat-tile__value">{overview.games.toLocaleString()}</p>
                  <p className="stat-tile__detail">{correct} correct · {incorrect} wrong</p>
                </div>
              </div>
            </div>

            <div className="nova-hero__panel">
              <div className="stat-grid stat-grid-compact">
                <div className="stat-tile">
                  <p className="stat-tile__label">Log loss</p>
                  <p className="stat-tile__value">{overview.logLoss.toFixed(3)}</p>
                  <p className="stat-tile__detail">Lower is better</p>
                </div>
                <div className="stat-tile">
                  <p className="stat-tile__label">Brier score</p>
                  <p className="stat-tile__value">{overview.brier.toFixed(3)}</p>
                  <p className="stat-tile__detail">Calibration metric</p>
                </div>
                <div className="stat-tile">
                  <p className="stat-tile__label">A+ accuracy</p>
                  <p className="stat-tile__value">{pct(confidenceBuckets[0]?.accuracy ?? 0)}</p>
                  <p className="stat-tile__detail">{confidenceBuckets[0]?.count ?? 0} games</p>
                </div>
                <div className="stat-tile">
                  <p className="stat-tile__label">Seasons tested</p>
                  <p className="stat-tile__value">{seasonBreakdown.length || 4}</p>
                  <p className="stat-tile__detail">2020-2024 data</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Edge Bands */}
        <section className="nova-section">
          <div className="section-head">
            <div>
              <p className="eyebrow">Confidence grading</p>
              <h2>The 6 edge bands</h2>
              <p className="lead-sm">
                Every prediction gets a grade based on edge size. Higher grades = higher confidence = higher accuracy.
              </p>
            </div>
          </div>

          <div className="power-grid">
            {confidenceBuckets.map((bucket) => {
              const isATier = bucket.grade.startsWith("A");
              const isBTier = bucket.grade.startsWith("B");
              return (
                <div key={bucket.grade} className="stat-card">
                  <div className="flex items-center justify-between mb-2">
                    <span className={`
                      px-2 py-1 text-xs font-bold rounded
                      ${isATier ? "bg-[var(--aqua)]/20 text-[var(--aqua)]" : ""}
                      ${isBTier ? "bg-[var(--amber)]/20 text-[var(--amber)]" : ""}
                      ${!isATier && !isBTier ? "bg-white/10 text-white/70" : ""}
                    `}>
                      {bucket.grade}
                    </span>
                    <span className="text-sm text-white/50">{bucket.label}</span>
                  </div>
                  <p className="stat-value text-3xl">{pct(bucket.accuracy)}</p>
                  <p className="text-sm text-white/60 mb-1">{bucket.count.toLocaleString()} games</p>
                  {bucket.description && (
                    <p className="text-xs text-white/40">{bucket.description}</p>
                  )}
                  <div className="edge-meter edge-meter--thick mt-3">
                    <div
                      className={`edge-meter__fill ${isATier ? "edge-meter__fill--gradient" : ""}`}
                      style={{
                        width: `${bucket.accuracy * 100}%`,
                        background: isATier ? undefined : isBTier ? "var(--amber)" : "rgba(255,255,255,0.3)"
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Grade Legend */}
          <div className="bento-card mt-6">
            <p className="micro-label">How to read grades</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3">
              <div>
                <span className="inline-block px-2 py-1 text-xs font-bold rounded bg-[var(--aqua)]/20 text-[var(--aqua)] mb-2">A+ / A</span>
                <p className="text-sm text-white/70">High confidence. Our best picks — the model sees a clear edge.</p>
              </div>
              <div>
                <span className="inline-block px-2 py-1 text-xs font-bold rounded bg-[var(--amber)]/20 text-[var(--amber)] mb-2">B+ / B</span>
                <p className="text-sm text-white/70">Medium confidence. The model leans one way but with less conviction.</p>
              </div>
              <div>
                <span className="inline-block px-2 py-1 text-xs font-bold rounded bg-white/10 text-white/70 mb-2">C+ / C</span>
                <p className="text-sm text-white/70">Low confidence. Near coin-flip territory.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Season Breakdown */}
        {seasonBreakdown.length > 0 && (
          <section className="nova-section">
            <div className="section-head">
              <div>
                <p className="eyebrow">Historical performance</p>
                <h2>Accuracy by season</h2>
                <p className="lead-sm">How the model performed across different NHL seasons.</p>
              </div>
            </div>

            <div className="card-elevated">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {seasonBreakdown.map((season) => (
                  <div key={season.season} className="stat-tile">
                    <p className="stat-tile__label">{season.season}</p>
                    <p className="stat-tile__value">{pct(season.accuracy)}</p>
                    <p className="stat-tile__detail">
                      {season.games.toLocaleString()} games · +{((season.accuracy - season.baseline) * 100).toFixed(1)} vs base
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* Strategy Receipts */}
        <section className="nova-section">
          <div className="section-head">
            <div>
              <p className="eyebrow">Backtest results</p>
              <h2>Strategy receipts</h2>
              <p className="lead-sm">Historical performance by confidence threshold. Reference only — not betting advice.</p>
            </div>
          </div>

          <div className="card-elevated">
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Strategy</th>
                    <th>Games</th>
                    <th>Win Rate</th>
                    <th>Avg Edge</th>
                    <th>Units</th>
                  </tr>
                </thead>
                <tbody>
                  {strategies.map((strategy) => {
                    const isProfitable = strategy.units > 0;
                    return (
                      <tr key={strategy.name}>
                        <td>
                          <div className="font-semibold text-white">{strategy.name}</div>
                          <div className="text-xs text-white/50">{strategy.note}</div>
                        </td>
                        <td>{strategy.bets.toLocaleString()}</td>
                        <td className="font-semibold">{pct(strategy.winRate)}</td>
                        <td>{(strategy.avgEdge * 100).toFixed(1)} pts</td>
                        <td>
                          <span className={`font-bold ${isProfitable ? "text-[var(--mint)]" : "text-[var(--rose)]"}`}>
                            {isProfitable ? "+" : ""}{strategy.units.toFixed(0)}u
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 mt-6">
              <div className="disclaimer-box">
                <p className="disclaimer-title">Important disclaimer</p>
                <p className="disclaimer-copy">
                  These results assume flat 1-unit bets at even money. Real-world results vary.
                  Puckcast is not a betting service — this is for transparency and model validation only.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Metrics Explainer */}
        <section className="nova-section">
          <div className="section-head">
            <div>
              <p className="eyebrow">Understanding the numbers</p>
              <h2>What the metrics mean</h2>
              <p className="lead-sm">Plain-English explanations for the stats that matter.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bento-card">
              <p className="micro-label">Accuracy</p>
              <h3>{pct(overview.accuracy)}</h3>
              <p className="bento-copy">
                The percentage of games where our predicted winner actually won. The NHL baseline
                (always picking home) is ~54%, so we beat that by {edge} percentage points.
              </p>
            </div>

            <div className="bento-card">
              <p className="micro-label">Log Loss</p>
              <h3>{overview.logLoss.toFixed(3)}</h3>
              <p className="bento-copy">
                Measures probability calibration. A model saying &quot;60%&quot; should be right 60% of the time.
                Lower is better — perfect is 0, random guessing is ~0.693.
              </p>
            </div>

            <div className="bento-card">
              <p className="micro-label">Edge</p>
              <h3>{(overview.avgEdge * 100).toFixed(1)} pts avg</h3>
              <p className="bento-copy">
                How far from 50/50 each prediction is. A 65% pick has 15 pts of edge.
                Higher edge = more confident prediction. A+ picks average 25+ pts.
              </p>
            </div>

            <div className="bento-card">
              <p className="micro-label">Brier Score</p>
              <h3>{overview.brier.toFixed(3)}</h3>
              <p className="bento-copy">
                Mean squared error of predictions. Ranges 0 (perfect) to 1 (worst).
                Below 0.25 is good for win/loss predictions.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
