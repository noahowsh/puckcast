import { buildTeamSnapshots, type TeamSnapshot } from "@/lib/current";
import insightsData from "@/data/modelInsights.json";
import type { ModelInsights } from "@/types/insights";

const snapshots = buildTeamSnapshots();
const modelInsights = insightsData as ModelInsights;
const overview = modelInsights.overall;
const confidenceBuckets = modelInsights.confidenceBuckets;
const strategies = modelInsights.strategies;

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

const topTeams = snapshots.slice(0, 8);

function bucketUpcomingGames(teams: TeamSnapshot[]) {
  const buckets = [
    { label: "0-5 pts edge", min: 0, max: 0.05, count: 0 },
    { label: "5-10 pts edge", min: 0.05, max: 0.1, count: 0 },
    { label: "10-15 pts edge", min: 0.1, max: 0.15, count: 0 },
    { label: "15-20 pts edge", min: 0.15, max: 0.2, count: 0 },
    { label: "20+ pts edge", min: 0.2, max: Infinity, count: 0 },
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
  return (
    <div className="relative min-h-screen bg-slate-950">
      {/* Subtle background gradient */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-b from-sky-950/20 via-slate-950 to-slate-950" />
      </div>

      <div className="relative mx-auto max-w-7xl px-6 py-16 lg:px-8">
        {/* Header */}
        <section className="mb-32">
          <div className="mx-auto max-w-4xl text-center">
            <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-sky-500/20 bg-sky-500/5 px-3 py-1">
              <span className="text-xs font-medium text-sky-400">Performance</span>
            </div>
            <h1 className="mb-8 text-6xl font-extrabold text-white lg:text-7xl">Model diagnostics</h1>
            <p className="text-xl text-slate-300">
              Track current season performance, upcoming slate breakdowns, and historical model analysis all in one place.
            </p>
          </div>
        </section>

        {/* Model Performance Overview */}
        <section className="mb-32">
          <h2 className="mb-10 text-center text-3xl font-extrabold text-white">Key Metrics</h2>
          <div className="grid gap-8 md:grid-cols-4">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
              <p className="text-sm font-medium text-slate-400">Test Accuracy</p>
              <p className="mt-2 text-3xl font-bold text-sky-400">{pct(overview.accuracy)}</p>
              <p className="mt-1 text-sm text-slate-500">2023-24 holdout</p>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
              <p className="text-sm font-medium text-slate-400">Baseline</p>
              <p className="mt-2 text-3xl font-bold text-white">{pct(overview.baseline)}</p>
              <p className="mt-1 text-sm text-slate-500">Home win rate</p>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
              <p className="text-sm font-medium text-slate-400">Edge</p>
              <p className="mt-2 text-3xl font-bold text-white">+{((overview.accuracy - overview.baseline) * 100).toFixed(1)}</p>
              <p className="mt-1 text-sm text-slate-500">pts over baseline</p>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
              <p className="text-sm font-medium text-slate-400">Games</p>
              <p className="mt-2 text-3xl font-bold text-white">{overview.games.toLocaleString()}</p>
              <p className="mt-1 text-sm text-slate-500">validated</p>
            </div>
          </div>
        </section>

        {/* Upcoming Slate Focus */}
        <section className="mb-32">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
            <h2 className="mb-4 text-2xl font-extrabold text-white">Today's Top Matchups</h2>
            <p className="mb-8 text-sm text-slate-400">Teams with the highest model confidence</p>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="border-b border-slate-800">
                  <tr className="text-slate-400">
                    <th className="py-3 pr-4 text-left font-medium">Team</th>
                    <th className="py-3 px-4 text-left font-medium">Record</th>
                    <th className="py-3 px-4 text-left font-medium">Games Listed</th>
                    <th className="py-3 px-4 text-left font-medium">Avg Win %</th>
                    <th className="py-3 px-4 text-left font-medium">Avg Edge</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {topTeams.map((team) => (
                    <tr key={team.team} className="text-slate-300">
                      <td className="py-3 pr-4 font-semibold text-white">{team.team}</td>
                      <td className="py-3 px-4">{team.record ?? "—"}</td>
                      <td className="py-3 px-4">{team.games}</td>
                      <td className="py-3 px-4">{pct(team.avgProb)}</td>
                      <td className="py-3 px-4 text-sky-400">{(team.avgEdge * 100).toFixed(1)} pts</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Edge Distribution */}
        <section className="mb-32">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
            <h2 className="mb-4 text-2xl font-extrabold text-white">Edge Distribution</h2>
            <p className="mb-8 text-sm text-slate-400">Upcoming games by confidence level</p>
            <div className="space-y-4">
              {edgeDistribution.buckets.map((bucket) => (
                <div key={bucket.label}>
                  <div className="mb-2 flex items-center justify-between text-sm">
                    <span className="font-medium text-slate-300">{bucket.label}</span>
                    <span className="text-slate-400">{bucket.count} games</span>
                  </div>
                  <div className="h-3 w-full rounded-full bg-slate-800">
                    <div
                      className="h-full rounded-full bg-sky-500"
                      style={{ width: edgeDistribution.total ? `${(bucket.count / edgeDistribution.total) * 100}%` : "0%" }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Confidence Calibration */}
        <section className="mb-32">
          <div className="mb-10 text-center">
            <h2 className="text-3xl font-extrabold text-white">Confidence Calibration</h2>
            <p className="mt-2 text-sm text-slate-400">Accuracy by prediction strength (2023-24 test set)</p>
          </div>
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {confidenceBuckets.map((bucket) => {
              const isStrong = bucket.accuracy > 0.6;
              return (
                <div key={bucket.label} className={`rounded-2xl border p-8 ${isStrong ? 'border-sky-500/30 bg-sky-500/5' : 'border-slate-800 bg-slate-900/50'}`}>
                  <p className="text-sm font-medium text-slate-400">{bucket.label}</p>
                  <p className="mt-2 text-3xl font-bold text-white">{pct(bucket.accuracy)}</p>
                  <p className="mt-1 text-sm text-slate-500">{bucket.count.toLocaleString()} games</p>
                </div>
              );
            })}
          </div>
        </section>

        {/* Betting Strategies */}
        <section className="mb-32">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
            <h2 className="mb-4 text-2xl font-extrabold text-white">Strategy Performance</h2>
            <p className="mb-8 text-sm text-slate-400">Historical betting strategy results (for reference only)</p>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="border-b border-slate-800">
                  <tr className="text-slate-400">
                    <th className="py-3 pr-4 text-left font-medium">Strategy</th>
                    <th className="py-3 px-4 text-left font-medium">Win %</th>
                    <th className="py-3 px-4 text-left font-medium">ROI / Bet</th>
                    <th className="py-3 px-4 text-left font-medium">Units</th>
                    <th className="py-3 px-4 text-left font-medium">Bets</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {strategies.map((strategy) => (
                    <tr key={strategy.name} className="text-slate-300">
                      <td className="py-3 pr-4">
                        <p className="font-semibold text-white">{strategy.name}</p>
                        <p className="text-xs text-slate-500">{strategy.note}</p>
                      </td>
                      <td className="py-3 px-4">{pct(strategy.winRate)}</td>
                      <td className="py-3 px-4">{((strategy.units / strategy.bets) * 100).toFixed(1)}%</td>
                      <td className="py-3 px-4 font-semibold text-sky-400">{strategy.units > 0 ? `+${strategy.units}` : strategy.units}u</td>
                      <td className="py-3 px-4">{strategy.bets.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-6 rounded-lg border border-sky-500/20 bg-sky-500/5 p-4">
              <p className="mb-2 text-sm font-semibold text-sky-400">Disclaimer</p>
              <p className="text-xs text-slate-300">
                These strategy results are shown for transparency and calibration analysis. We are not a betting service and do not recommend specific wagers. Always bet responsibly.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
