import insightsData from "@/data/modelInsights.json";
import type { ModelInsights } from "@/types/insights";

const modelInsights = insightsData as ModelInsights;
const overview = modelInsights.overall;
const confidenceBuckets = modelInsights.confidenceBuckets;
const strategies = modelInsights.strategies;
const bankrollSeries = modelInsights.bankrollSeries;
const finalUnits = bankrollSeries[bankrollSeries.length - 1]?.units ?? 0;

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

export default function PerformancePage() {
  const edge = ((overview.accuracy - overview.baseline) * 100).toFixed(1);
  const correct = Math.round(overview.accuracy * overview.games);
  const incorrect = Math.round((1 - overview.accuracy) * overview.games);
  const bestStrategy = strategies.slice().sort((a, b) => b.units - a.units)[0];

  return (
    <div className="min-h-screen">
      <div className="container">
        <section className="nova-hero nav-offset">
          <div className="nova-hero__grid">
            <div className="nova-hero__text">
              <div className="pill-row">
                <span className="pill">Model accuracy</span>
                <span className="pill">Holdout proof</span>
              </div>
              <h1 className="display-xl">Does the model work?</h1>
              <p className="lead">
                Yes. Calibrated on official NHL data across {overview.games.toLocaleString()} holdout games. Baseline challenged, edge measured,
                confidence graded.
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
                  <p className="stat-tile__detail">Probability gap per game</p>
                </div>
                <div className="stat-tile">
                  <p className="stat-tile__label">Holdout size</p>
                  <p className="stat-tile__value">{overview.games.toLocaleString()}</p>
                  <p className="stat-tile__detail">
                    {correct.toLocaleString()} correct · {incorrect.toLocaleString()} incorrect
                  </p>
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
                  <p className="stat-tile__label">A-grade hit rate</p>
                  <p className="stat-tile__value">
                    {pct(confidenceBuckets[confidenceBuckets.length - 1]?.accuracy ?? 0)}
                  </p>
                  <p className="stat-tile__detail">{confidenceBuckets[confidenceBuckets.length - 1]?.count ?? 0} games</p>
                </div>
                <div className="stat-tile">
                  <p className="stat-tile__label">Best strategy</p>
                  <p className="stat-tile__value">{bestStrategy?.name ?? "N/A"}</p>
                  <p className="stat-tile__detail">
                    {bestStrategy ? `${bestStrategy.units.toFixed(0)}u · ${pct(bestStrategy.winRate)}` : "N/A"}
                  </p>
                </div>
                <div className="stat-tile">
                  <p className="stat-tile__label">Historical bankroll</p>
                  <p className="stat-tile__value">{finalUnits >= 0 ? `+${finalUnits.toFixed(0)}u` : `${finalUnits.toFixed(0)}u`}</p>
                  <p className="stat-tile__detail">Flat stakes, even money assumption</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="nova-section">
          <div className="section-head">
            <div>
              <p className="eyebrow">Confidence calibration</p>
              <h2>Accuracy by edge band</h2>
              <p className="lead-sm">204-feature model, official NHL API data, {overview.games.toLocaleString()} holdout games.</p>
            </div>
          </div>
          <div className="power-grid">
            {confidenceBuckets
              .slice()
              .reverse()
              .map((bucket) => (
                <div key={bucket.label} className="stat-card">
                  <div className="flex items-center justify-between mb-2">
                    <p className="stat-label">{bucket.label}</p>
                    <span className="px-2 py-1 text-xs font-bold rounded bg-white/10 text-white">{bucket.grade}</span>
                  </div>
                  <p className="stat-value text-3xl">{pct(bucket.accuracy)}</p>
                  <p className="text-sm text-white/60">{bucket.count.toLocaleString()} games</p>
                  <div className="edge-meter edge-meter--thick mt-4">
                    <div className="edge-meter__fill edge-meter__fill--gradient" style={{ width: `${Math.min(bucket.accuracy * 100, 100)}%` }} />
                  </div>
                </div>
              ))}
          </div>
        </section>

        <section className="nova-section">
          <div className="card-elevated">
            <h2 className="text-2xl font-bold text-white mb-3">Strategy receipts (reference only)</h2>
            <p className="text-white/60 mb-6">Historical backtest on the same holdout set. Not betting advice.</p>
            <div className="table-container mb-4">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Strategy</th>
                    <th>Win Rate</th>
                    <th>ROI/Bet</th>
                    <th>Total Units</th>
                    <th>Bets</th>
                  </tr>
                </thead>
                <tbody>
                  {strategies.map((strategy) => {
                    const roiPerBet = ((strategy.units / strategy.bets) * 100).toFixed(1);
                    const isProfitable = strategy.units > 0;
                    return (
                      <tr key={strategy.name}>
                        <td>
                          <div>
                            <div className="font-semibold text-white">{strategy.name}</div>
                            <div className="text-xs text-white/60">{strategy.note}</div>
                          </div>
                        </td>
                        <td className="font-semibold">{pct(strategy.winRate)}</td>
                        <td className={isProfitable ? "text-emerald-300" : "text-rose-300"}>{roiPerBet}%</td>
                        <td>
                          <span className={`font-bold ${isProfitable ? "text-emerald-300" : "text-rose-300"}`}>
                            {isProfitable ? "+" : ""}
                            {strategy.units.toFixed(0)}u
                          </span>
                        </td>
                        <td>{strategy.bets.toLocaleString()}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4">
              <div className="disclaimer-box">
                <p className="disclaimer-title">Important disclaimer</p>
                <p className="disclaimer-copy">
                  These results are for transparency and calibration analysis. Puckcast is not a betting service; this is not wagering advice. Always bet
                  responsibly.
                </p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
