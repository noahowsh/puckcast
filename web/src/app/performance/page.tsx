import insightsData from "@/data/modelInsights.json";
import type { ModelInsights } from "@/types/insights";

const modelInsights = insightsData as ModelInsights;
const overview = modelInsights.overall;
const confidenceBuckets = modelInsights.confidenceBuckets;
const strategies = modelInsights.strategies;
const seasonBreakdown = modelInsights.seasonBreakdown ?? [];
const currentSeason = modelInsights.currentSeason;

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

export default function PerformancePage() {
  const edge = ((overview.accuracy - overview.baseline) * 100).toFixed(1);
  const correct = Math.round(overview.accuracy * overview.games);
  const incorrect = overview.games - correct;

  return (
    <div className="min-h-screen">
      <div className="container">
        {/* Hero - Clean Single Column */}
        <section className="nova-hero nav-offset">
          <div style={{ maxWidth: '800px' }}>
            <div className="pill-row">
              <span className="pill">Model Performance</span>
              <span className="pill">V7.9</span>
            </div>
            <h1 className="display-xl" style={{ marginBottom: '0.75rem' }}>Does the model work?</h1>
            <p className="lead" style={{ marginBottom: '1.5rem' }}>
              Yes. We tested V7.9 on {overview.games.toLocaleString()} holdout games from the 2023-24 season —
              games the model never saw during training. It correctly predicted {pct(overview.accuracy)} of outcomes,
              beating the {pct(overview.baseline)} home-team baseline by <span style={{ color: 'var(--mint)' }}>+{edge} percentage points</span>.
            </p>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap: '1rem'
            }}>
              <div className="stat-tile">
                <p className="stat-tile__label">Accuracy</p>
                <p className="stat-tile__value" style={{ color: 'var(--aqua)' }}>{pct(overview.accuracy)}</p>
              </div>
              <div className="stat-tile">
                <p className="stat-tile__label">Log Loss</p>
                <p className="stat-tile__value">{overview.logLoss.toFixed(3)}</p>
              </div>
              <div className="stat-tile">
                <p className="stat-tile__label">A+ Picks</p>
                <p className="stat-tile__value" style={{ color: 'var(--mint)' }}>{pct(confidenceBuckets[0]?.accuracy ?? 0)}</p>
              </div>
              <div className="stat-tile">
                <p className="stat-tile__label">Test Games</p>
                <p className="stat-tile__value">{overview.games.toLocaleString()}</p>
              </div>
            </div>
          </div>
        </section>

        {/* Current Season - Highlighted */}
        {currentSeason && (
          <section className="nova-section">
            <div className="card-elevated" style={{
              borderColor: 'rgba(126, 227, 255, 0.5)',
              background: 'linear-gradient(160deg, rgba(126, 227, 255, 0.08), rgba(6, 12, 24, 0.95))'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
                <span className="pill" style={{
                  borderColor: 'var(--aqua)',
                  background: 'rgba(126, 227, 255, 0.15)',
                  color: 'var(--aqua)'
                }}>
                  Live
                </span>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-tertiary)' }}>
                  Updated {currentSeason.asOf}
                </span>
              </div>
              <h2 style={{ marginBottom: '0.25rem' }}>2025-26 Season Performance</h2>
              <p className="lead-sm" style={{ marginBottom: '1.25rem' }}>
                Real-time tracking of this season. These are actual results, not backtested.
              </p>

              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                gap: '1rem'
              }}>
                <div className="stat-tile">
                  <p className="stat-tile__label">Games Tracked</p>
                  <p className="stat-tile__value">{currentSeason.games}</p>
                  <p className="stat-tile__detail">This season so far</p>
                </div>
                <div className="stat-tile">
                  <p className="stat-tile__label">Accuracy</p>
                  <p className="stat-tile__value" style={{ color: 'var(--mint)' }}>{pct(currentSeason.accuracy)}</p>
                  <p className="stat-tile__detail">+{((currentSeason.accuracy - currentSeason.baseline) * 100).toFixed(1)} vs baseline</p>
                </div>
                <div className="stat-tile">
                  <p className="stat-tile__label">A-Grade Picks</p>
                  <p className="stat-tile__value" style={{ color: 'var(--aqua)' }}>{pct(currentSeason.aGradeAccuracy)}</p>
                  <p className="stat-tile__detail">{currentSeason.aGradeGames} high-confidence calls</p>
                </div>
                <div className="stat-tile">
                  <p className="stat-tile__label">Log Loss</p>
                  <p className="stat-tile__value">{currentSeason.logLoss.toFixed(3)}</p>
                  <p className="stat-tile__detail">Calibration metric</p>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Edge Bands + How to Read - Side by Side */}
        <section className="nova-section">
          <div className="section-head">
            <div>
              <p className="eyebrow">Confidence Grading</p>
              <h2>The 6 edge bands</h2>
              <p className="lead-sm">
                Every prediction gets a grade based on edge size. Higher grades = higher confidence = higher historical accuracy.
                <span style={{ color: 'var(--text-tertiary)', display: 'block', marginTop: '0.3rem', fontSize: '0.85rem' }}>
                  Based on 2023-24 season holdout testing
                </span>
              </p>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1.5rem' }}>
            {/* Edge Bands Grid - 3x2 symmetrical */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '0.75rem'
            }}>
              {confidenceBuckets.map((bucket) => {
                const isATier = bucket.grade.startsWith("A");
                const isBTier = bucket.grade.startsWith("B");
                const tierColor = isATier ? 'var(--aqua)' : isBTier ? 'var(--amber)' : 'var(--text-tertiary)';

                return (
                  <div
                    key={bucket.grade}
                    className="stat-card"
                    style={{ padding: '1.25rem' }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        minWidth: '2.5rem',
                        padding: '0.5rem 0.75rem',
                        borderRadius: '0.6rem',
                        fontSize: '1rem',
                        fontWeight: 800,
                        background: isATier
                          ? 'linear-gradient(135deg, rgba(126, 227, 255, 0.2), rgba(110, 240, 194, 0.15))'
                          : isBTier
                            ? 'rgba(246, 193, 119, 0.15)'
                            : 'rgba(255, 255, 255, 0.08)',
                        border: `1px solid ${isATier ? 'rgba(126, 227, 255, 0.4)' : isBTier ? 'rgba(246, 193, 119, 0.4)' : 'var(--border-subtle)'}`,
                        color: tierColor
                      }}>
                        {bucket.grade}
                      </span>
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-tertiary)' }}>{bucket.label}</span>
                    </div>
                    <p style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                      {pct(bucket.accuracy)}
                    </p>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                      {bucket.count.toLocaleString()} games
                    </p>
                    <div className="edge-meter edge-meter--thick">
                      <div
                        className={isATier ? "edge-meter__fill edge-meter__fill--gradient" : "edge-meter__fill"}
                        style={{
                          width: `${bucket.accuracy * 100}%`,
                          background: isATier ? undefined : isBTier ? 'var(--amber)' : 'rgba(255,255,255,0.3)'
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            {/* How to Read Grades */}
            <div className="bento-card" style={{ padding: '1.5rem' }}>
              <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>How to read grades</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.25rem' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <span style={{
                      padding: '0.35rem 0.6rem',
                      borderRadius: '0.5rem',
                      fontSize: '0.85rem',
                      fontWeight: 700,
                      background: 'linear-gradient(135deg, rgba(126, 227, 255, 0.2), rgba(110, 240, 194, 0.15))',
                      border: '1px solid rgba(126, 227, 255, 0.4)',
                      color: 'var(--aqua)'
                    }}>A+ / A</span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>≥20 pts edge</span>
                  </div>
                  <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    High confidence. Our best picks where the model sees a clear statistical advantage. Historically ~70% accurate.
                  </p>
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <span style={{
                      padding: '0.35rem 0.6rem',
                      borderRadius: '0.5rem',
                      fontSize: '0.85rem',
                      fontWeight: 700,
                      background: 'rgba(246, 193, 119, 0.15)',
                      border: '1px solid rgba(246, 193, 119, 0.4)',
                      color: 'var(--amber)'
                    }}>B+ / B</span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>10-20 pts edge</span>
                  </div>
                  <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    Medium confidence. The model leans one way but with less conviction. Still beats the baseline at ~60%.
                  </p>
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <span style={{
                      padding: '0.35rem 0.6rem',
                      borderRadius: '0.5rem',
                      fontSize: '0.85rem',
                      fontWeight: 700,
                      background: 'rgba(255, 255, 255, 0.08)',
                      border: '1px solid var(--border-subtle)',
                      color: 'var(--text-secondary)'
                    }}>C+ / C</span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>0-10 pts edge</span>
                  </div>
                  <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    Low confidence. Near coin-flip territory where the model doesn&apos;t see much separation between teams.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Historical Season Breakdown */}
        {seasonBreakdown.length > 0 && (
          <section className="nova-section">
            <div className="section-head">
              <div>
                <p className="eyebrow">Backtest History</p>
                <h2>Performance by season</h2>
                <p className="lead-sm">
                  Holdout testing results across multiple seasons. Each season was tested
                  using a model trained only on prior years.
                </p>
              </div>
            </div>

            <div className="card-elevated">
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                {seasonBreakdown.map((season) => {
                  const seasonEdge = ((season.accuracy - season.baseline) * 100).toFixed(1);
                  return (
                    <div key={season.season} className="stat-tile">
                      <p className="stat-tile__label">{season.season}</p>
                      <p className="stat-tile__value">{pct(season.accuracy)}</p>
                      <div style={{ marginTop: '0.5rem' }}>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                          {season.games.toLocaleString()} games
                        </p>
                        <p style={{ fontSize: '0.85rem', color: 'var(--mint)' }}>
                          +{seasonEdge} pts vs baseline
                        </p>
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginTop: '0.25rem' }}>
                          Log loss: {season.logLoss.toFixed(3)}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
              <p style={{
                fontSize: '0.85rem',
                color: 'var(--text-tertiary)',
                marginTop: '1.25rem',
                paddingTop: '1rem',
                borderTop: '1px solid var(--border-subtle)'
              }}>
                The model consistently beats the baseline across all tested seasons, showing robust performance
                that isn&apos;t overfit to any single year.
              </p>
            </div>
          </section>
        )}

        {/* Metrics Explainer */}
        <section className="nova-section">
          <div className="section-head">
            <div>
              <p className="eyebrow">Understanding the Numbers</p>
              <h2>What the metrics mean</h2>
              <p className="lead-sm">Plain-English explanations for all the stats on this page.</p>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
            <div className="bento-card">
              <p className="micro-label">Accuracy</p>
              <h3 style={{ color: 'var(--aqua)' }}>{pct(overview.accuracy)}</h3>
              <p className="bento-copy">
                <strong>What it is:</strong> The percentage of games where our predicted winner actually won.
              </p>
              <p className="bento-copy" style={{ marginTop: '0.5rem' }}>
                <strong>Why it matters:</strong> This is the most intuitive metric. If accuracy is 60%, we&apos;re right
                6 out of 10 times. The NHL baseline (always picking home team) is ~54%.
              </p>
              <p className="bento-copy" style={{ marginTop: '0.5rem', color: 'var(--mint)' }}>
                We beat baseline by +{edge} percentage points.
              </p>
            </div>

            <div className="bento-card">
              <p className="micro-label">Log Loss</p>
              <h3>{overview.logLoss.toFixed(3)}</h3>
              <p className="bento-copy">
                <strong>What it is:</strong> Measures how well-calibrated our probabilities are. When we say
                &quot;70% chance&quot;, it should happen about 70% of the time.
              </p>
              <p className="bento-copy" style={{ marginTop: '0.5rem' }}>
                <strong>Why it matters:</strong> Low log loss means we&apos;re honest about our uncertainty.
                A model that says &quot;51%&quot; for a toss-up is better than one that says &quot;90%&quot; and is wrong.
              </p>
              <p className="bento-copy" style={{ marginTop: '0.5rem', color: 'var(--text-tertiary)' }}>
                Scale: 0 = perfect, 0.693 = random guessing
              </p>
            </div>

            <div className="bento-card">
              <p className="micro-label">Edge (points)</p>
              <h3>{(overview.avgEdge * 100).toFixed(1)} pts avg</h3>
              <p className="bento-copy">
                <strong>What it is:</strong> How far from 50/50 each prediction is. A 65% pick has 15 pts of edge
                (65 - 50 = 15).
              </p>
              <p className="bento-copy" style={{ marginTop: '0.5rem' }}>
                <strong>Why it matters:</strong> Higher edge = more confident prediction. Our grading system
                (A+, A, B+, etc.) is based entirely on edge size.
              </p>
              <p className="bento-copy" style={{ marginTop: '0.5rem', color: 'var(--text-tertiary)' }}>
                A+ picks: ≥25 pts edge | C picks: &lt;5 pts edge
              </p>
            </div>

            <div className="bento-card">
              <p className="micro-label">Brier Score</p>
              <h3>{overview.brier.toFixed(3)}</h3>
              <p className="bento-copy">
                <strong>What it is:</strong> Mean squared error between predicted probability and actual outcome
                (1 if correct, 0 if wrong).
              </p>
              <p className="bento-copy" style={{ marginTop: '0.5rem' }}>
                <strong>Why it matters:</strong> Like log loss, rewards calibrated predictions. Combines accuracy
                and confidence into one number.
              </p>
              <p className="bento-copy" style={{ marginTop: '0.5rem', color: 'var(--text-tertiary)' }}>
                Scale: 0 = perfect, 0.25 = random guessing
              </p>
            </div>

            <div className="bento-card">
              <p className="micro-label">Baseline</p>
              <h3>{pct(overview.baseline)}</h3>
              <p className="bento-copy">
                <strong>What it is:</strong> The accuracy you&apos;d get by always picking the home team to win.
              </p>
              <p className="bento-copy" style={{ marginTop: '0.5rem' }}>
                <strong>Why it matters:</strong> This is what we compare against. Any model worth using should
                beat this naive strategy. Home teams win ~54% in the NHL.
              </p>
            </div>

            <div className="bento-card">
              <p className="micro-label">Holdout Testing</p>
              <h3>{overview.games.toLocaleString()} games</h3>
              <p className="bento-copy">
                <strong>What it is:</strong> Testing on games the model has never seen. We trained on 4 prior seasons
                and tested on 2023-24 — a full season the model never touched during training.
              </p>
              <p className="bento-copy" style={{ marginTop: '0.5rem' }}>
                <strong>Why it matters:</strong> Prevents overfitting. Results from holdout testing show real-world
                expected performance, not just memorizing training data.
              </p>
            </div>
          </div>
        </section>

        {/* Strategy Receipts */}
        <section className="nova-section">
          <div className="section-head">
            <div>
              <p className="eyebrow">Backtest Results</p>
              <h2>Strategy receipts</h2>
              <p className="lead-sm">
                Historical performance by confidence threshold.
                <span style={{ color: 'var(--text-tertiary)', display: 'block', marginTop: '0.3rem', fontSize: '0.85rem' }}>
                  Based on 2023-24 season holdout testing
                </span>
              </p>
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
                          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{strategy.name}</div>
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginTop: '0.2rem' }}>{strategy.note}</div>
                        </td>
                        <td>{strategy.bets.toLocaleString()}</td>
                        <td style={{ fontWeight: 600 }}>{pct(strategy.winRate)}</td>
                        <td>{(strategy.avgEdge * 100).toFixed(1)} pts</td>
                        <td>
                          <span style={{
                            fontWeight: 700,
                            color: isProfitable ? 'var(--mint)' : 'var(--rose)'
                          }}>
                            {isProfitable ? "+" : ""}{strategy.units.toFixed(0)}u
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div style={{
              marginTop: '1.5rem',
              paddingTop: '1.5rem',
              borderTop: '1px solid var(--border-subtle)'
            }}>
              <div className="disclaimer-box">
                <p className="disclaimer-title">Important Disclaimer</p>
                <p className="disclaimer-copy">
                  These results assume flat 1-unit bets at -110 odds (standard juice). Actual results will vary
                  based on odds available, timing, and market conditions. Past performance does not guarantee
                  future results. <strong>Puckcast is not a betting service</strong> — this data is provided for
                  transparency and model validation purposes only.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Data Sources Clarification */}
        <section className="nova-section" style={{ paddingTop: '2rem' }}>
          <div className="bento-card" style={{
            borderColor: 'rgba(241, 217, 166, 0.3)',
            background: 'linear-gradient(165deg, rgba(241, 217, 166, 0.06), rgba(6, 10, 18, 0.9))'
          }}>
            <h3 style={{ fontSize: '1.1rem', marginBottom: '0.75rem' }}>Understanding our data</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem' }}>
              <div>
                <p style={{ fontWeight: 700, color: 'var(--amber)', marginBottom: '0.35rem' }}>Holdout test results</p>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  The main accuracy and log loss numbers come from testing on the 2023-24 season (1,230 games).
                  The model was trained on a rolling 4-season window of prior data and tested on games it never saw.
                </p>
              </div>
              <div>
                <p style={{ fontWeight: 700, color: 'var(--aqua)', marginBottom: '0.35rem' }}>Current season (2025-26)</p>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  The 2025-26 stats are live tracking of actual predictions made this season. These are real results,
                  not backtests. Updated daily as games complete.
                </p>
              </div>
              <div>
                <p style={{ fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>Daily predictions</p>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  Each day&apos;s predictions use the most recent data available. The model retrains periodically
                  on a rolling 4-season window to incorporate new patterns.
                </p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
