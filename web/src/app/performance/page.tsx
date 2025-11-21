import { buildTeamSnapshots, type TeamSnapshot } from "@/lib/current";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { TeamLogo } from "@/components/TeamLogo";
import insightsData from "@/data/modelInsights.json";
import type { ModelInsights } from "@/types/insights";

const snapshots = buildTeamSnapshots();
const modelInsights = insightsData as ModelInsights;
const overview = modelInsights.overall;
const confidenceBuckets = modelInsights.confidenceBuckets;
const strategies = modelInsights.strategies;
const bankrollSeries = modelInsights.bankrollSeries;
const finalUnits = bankrollSeries[bankrollSeries.length - 1]?.units || 0;

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;
const topTeams = snapshots.slice(0, 10);

function bucketUpcomingGames(teams: TeamSnapshot[]) {
  const buckets = [
    { label: "0-5 pts", min: 0, max: 0.05, count: 0, color: "bg-slate-500" },
    { label: "5-10 pts", min: 0.05, max: 0.1, count: 0, color: "bg-amber-500" },
    { label: "10-15 pts", min: 0.1, max: 0.15, count: 0, color: "bg-sky-500" },
    { label: "15-20 pts", min: 0.15, max: 0.2, count: 0, color: "bg-cyan-500" },
    { label: "20+ pts", min: 0.2, max: Infinity, count: 0, color: "bg-green-500" },
  ];

  const gamesPerTeam = teams.reduce((sum, team) => sum + team.games, 0);

  teams.forEach((team) => {
    buckets.forEach((bucket) => {
      if (team.avgEdge >= bucket.min && team.avgEdge < bucket.max) {
        bucket.count += team.games;
      }
    });
  });

  return { buckets, total: gamesPerTeam };
}

const edgeDistribution = bucketUpcomingGames(snapshots);

export default function PerformancePage() {
  const edge = ((overview.accuracy - overview.baseline) * 100).toFixed(1);

  return (
    <div className="min-h-screen">
      <div className="container" style={{ paddingTop: '6rem' }}>
        <PageHeader
          title="Model Performance"
          description="Track model accuracy, confidence calibration, betting strategies, and comprehensive diagnostics from our 1,230 game holdout set."
          icon={
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          }
        />

        {/* Key Metrics */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Key Metrics</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 stagger-animation">
            <StatCard
              label="Test Accuracy"
              value={pct(overview.accuracy)}
              change={{ value: `+${edge} pts`, isPositive: true }}
              size="lg"
            />
            <StatCard
              label="Baseline"
              value={pct(overview.baseline)}
              size="lg"
            />
            <StatCard
              label="Total Games"
              value={overview.games.toLocaleString()}
              size="lg"
            />
            <StatCard
              label="Total Profit"
              value={`+${finalUnits.toFixed(0)}u`}
              change={{ value: "Even money", isPositive: true }}
              size="lg"
            />
          </div>
        </section>

        {/* Calibration Metrics */}
        <section className="mb-12">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-lg font-bold text-white mb-4">Calibration Metrics</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-400">Log Loss</span>
                    <span className="text-xl font-bold text-white">{overview.logLoss.toFixed(3)}</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: '32%' }} />
                  </div>
                  <p className="text-xs text-slate-500 mt-1">Lower is better (0-1 scale)</p>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-400">Average Edge</span>
                    <span className="text-xl font-bold text-sky-400">{(overview.avgEdge * 100).toFixed(1)}%</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${overview.avgEdge * 100}%` }} />
                  </div>
                  <p className="text-xs text-slate-500 mt-1">Average probability gap</p>
                </div>
              </div>
            </div>

            <div className="card">
              <h3 className="text-lg font-bold text-white mb-4">Win Rate Analysis</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">Correct Predictions</span>
                  <span className="text-lg font-bold text-green-400">
                    {Math.round(overview.accuracy * overview.games).toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">Incorrect Predictions</span>
                  <span className="text-lg font-bold text-red-400">
                    {Math.round((1 - overview.accuracy) * overview.games).toLocaleString()}
                  </span>
                </div>
                <div className="divider"></div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">Edge Over Baseline</span>
                  <span className="text-xl font-bold text-sky-400">+{edge} pts</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Confidence Calibration */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Confidence Calibration</h2>
          <p className="text-slate-400 mb-6">Accuracy by prediction confidence (2023-24 holdout set)</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 stagger-animation">
            {confidenceBuckets.map((bucket) => {
              const isStrong = bucket.accuracy > 0.65;
              return (
                <div
                  key={bucket.label}
                  className={`stat-card ${isStrong ? 'border-green-500/30 bg-green-500/5' : ''}`}
                >
                  <div className="stat-label">{bucket.label}</div>
                  <div className="stat-value text-3xl">{pct(bucket.accuracy)}</div>
                  <div className="text-sm text-slate-400 mt-2">{bucket.count.toLocaleString()} games</div>
                  {isStrong && (
                    <div className="mt-3 inline-flex items-center gap-1 px-2 py-1 rounded-full bg-green-500/20 text-xs font-semibold text-green-400">
                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      Strong
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        {/* Edge Distribution */}
        <section className="mb-12">
          <div className="card-elevated">
            <h2 className="text-2xl font-bold text-white mb-4">Edge Distribution</h2>
            <p className="text-slate-400 mb-8">Upcoming games by confidence level</p>
            <div className="space-y-5">
              {edgeDistribution.buckets.map((bucket) => {
                const percentage = edgeDistribution.total
                  ? (bucket.count / edgeDistribution.total) * 100
                  : 0;
                return (
                  <div key={bucket.label}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold text-white">{bucket.label} edge</span>
                      <div className="flex items-center gap-3">
                        <span className="text-slate-400">{bucket.count} games</span>
                        <span className="text-sm font-semibold text-sky-400">
                          {percentage.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    <div className="h-4 w-full rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className={`h-full ${bucket.color} transition-all duration-500`}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Top Matchups */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Top Confidence Matchups</h2>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Team</th>
                  <th>Record</th>
                  <th>Games</th>
                  <th>Avg Win %</th>
                  <th>Avg Edge</th>
                </tr>
              </thead>
              <tbody>
                {topTeams.map((team, idx) => (
                  <tr key={team.team}>
                    <td>
                      <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-slate-800 text-slate-400 font-bold text-sm">
                        {idx + 1}
                      </div>
                    </td>
                    <td>
                      <div className="flex items-center gap-3">
                        <TeamLogo teamAbbrev={team.abbrev} size="xs" />
                        <span className="font-semibold">{team.team}</span>
                      </div>
                    </td>
                    <td>{team.record ?? "—"}</td>
                    <td>{team.games}</td>
                    <td className="font-semibold">{pct(team.avgProb)}</td>
                    <td>
                      <span className="text-sky-400 font-bold">
                        {(team.avgEdge * 100).toFixed(1)} pts
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Strategy Performance */}
        <section className="mb-12">
          <div className="card-elevated">
            <div className="flex items-start justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">Strategy Performance</h2>
                <p className="text-slate-400">Historical betting strategy results (for reference only)</p>
              </div>
            </div>

            <div className="table-container mb-6">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Strategy</th>
                    <th>Win Rate</th>
                    <th>ROI per Bet</th>
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
                            <div className="text-xs text-slate-500">{strategy.note}</div>
                          </div>
                        </td>
                        <td className="font-semibold">{pct(strategy.winRate)}</td>
                        <td className={isProfitable ? "text-green-400" : "text-red-400"}>
                          {roiPerBet}%
                        </td>
                        <td>
                          <span
                            className={`font-bold ${
                              isProfitable ? "text-green-400" : "text-red-400"
                            }`}
                          >
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
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <div>
                  <p className="font-semibold text-amber-400 mb-1">Disclaimer</p>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    These strategy results are shown for transparency and calibration analysis.
                    We are not a betting service and do not recommend specific wagers. Always bet responsibly.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
