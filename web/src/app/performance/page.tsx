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
    <div className="relative overflow-hidden">
      <div className="relative mx-auto flex max-w-6xl flex-col gap-12 px-6 pb-16 pt-8 lg:px-12">
        <header className="space-y-3">
          <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Performance analytics</p>
          <h1 className="text-4xl font-semibold text-white">Model diagnostics & insights.</h1>
          <p className="max-w-3xl text-base text-white/75">
            Track current season performance, upcoming slate breakdowns, and historical model analysis all in one place.
          </p>
        </header>

        {/* Model Performance Overview */}
        <section className="grid gap-6 md:grid-cols-4">
          <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-lime-300/10 to-emerald-400/10 p-5">
            <p className="text-xs uppercase tracking-[0.5em] text-white/60">Test Accuracy</p>
            <p className="mt-3 text-3xl font-semibold text-lime-300">{pct(overview.accuracy)}</p>
            <p className="text-xs uppercase tracking-[0.4em] text-white/50">2023-24 holdout</p>
          </div>
          <div className="rounded-3xl border border-white/10 bg-black/20 p-5">
            <p className="text-xs uppercase tracking-[0.5em] text-white/60">Baseline</p>
            <p className="mt-3 text-3xl font-semibold text-white">{pct(overview.baseline)}</p>
            <p className="text-xs uppercase tracking-[0.4em] text-white/50">Home win rate</p>
          </div>
          <div className="rounded-3xl border border-white/10 bg-black/20 p-5">
            <p className="text-xs uppercase tracking-[0.5em] text-white/60">Edge</p>
            <p className="mt-3 text-3xl font-semibold text-white">+{((overview.accuracy - overview.baseline) * 100).toFixed(1)}</p>
            <p className="text-xs uppercase tracking-[0.4em] text-white/50">pts over baseline</p>
          </div>
          <div className="rounded-3xl border border-white/10 bg-black/20 p-5">
            <p className="text-xs uppercase tracking-[0.5em] text-white/60">Games</p>
            <p className="mt-3 text-3xl font-semibold text-white">{overview.games.toLocaleString()}</p>
            <p className="text-xs uppercase tracking-[0.4em] text-white/50">validated</p>
          </div>
        </section>

        {/* Upcoming Slate Focus */}
        <section className="rounded-[36px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30">
          <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Today's Top Matchups</p>
          <p className="mt-2 text-xs text-white/60">Teams with the highest model confidence</p>
          <div className="mt-6 overflow-x-auto">
            <table className="min-w-full divide-y divide-white/10 text-sm">
              <thead className="text-white/60">
                <tr>
                  <th className="py-3 pr-4 text-left">Team</th>
                  <th className="py-3 px-4 text-left">Record</th>
                  <th className="py-3 px-4 text-left">Games listed</th>
                  <th className="py-3 px-4 text-left">Avg win %</th>
                  <th className="py-3 px-4 text-left">Avg edge</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-white/80">
                {topTeams.map((team) => (
                  <tr key={team.team}>
                    <td className="py-3 pr-4 font-semibold text-white">{team.team}</td>
                    <td className="py-3 px-4 text-white/70">{team.record ?? "—"}</td>
                    <td className="py-3 px-4">{team.games}</td>
                    <td className="py-3 px-4">{pct(team.avgProb)}</td>
                    <td className="py-3 px-4">{(team.avgEdge * 100).toFixed(1)} pts</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Edge Distribution */}
        <section className="rounded-[36px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30">
          <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Edge distribution across upcoming games</p>
          <div className="mt-6 space-y-4">
            {edgeDistribution.buckets.map((bucket) => (
              <div key={bucket.label}>
                <div className="flex items-center justify-between text-xs uppercase tracking-[0.4em] text-white/60">
                  <span>{bucket.label}</span>
                  <span>{bucket.count} slots</span>
                </div>
                <div className="mt-2 h-2.5 w-full rounded-full bg-white/10">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-lime-300 via-emerald-400 to-cyan-300"
                    style={{ width: edgeDistribution.total ? `${(bucket.count / edgeDistribution.total) * 100}%` : "0%" }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Confidence Calibration */}
        <section className="rounded-[36px] border border-white/10 bg-gradient-to-br from-black/40 via-slate-900/60 to-slate-950 p-8 shadow-2xl shadow-black/40">
          <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Confidence Calibration</p>
          <p className="mt-2 text-xs text-white/60">Accuracy by prediction strength (2023-24 test set)</p>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {confidenceBuckets.map((bucket) => {
              const strength = Math.min(Math.max((bucket.accuracy - 0.5) * 3, 0), 1);
              const background = `linear-gradient(135deg, rgba(190,242,100,${0.25 + strength * 0.5}), rgba(34,197,94,${0.2 + strength * 0.5}))`;
              return (
                <div key={bucket.label} className="rounded-3xl border border-white/10 p-5" style={{ background }}>
                  <p className="text-xs uppercase tracking-[0.4em] text-white/70">{bucket.label}</p>
                  <p className="mt-2 text-3xl font-semibold text-white">{pct(bucket.accuracy)}</p>
                  <p className="text-xs uppercase tracking-[0.4em] text-white/60">{bucket.count.toLocaleString()} games</p>
                </div>
              );
            })}
          </div>
        </section>

        {/* Betting Strategies */}
        <section className="rounded-[36px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30">
          <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Strategy Performance</p>
          <p className="mt-2 text-xs text-white/60">Historical betting strategy results (for reference only)</p>
          <div className="mt-6 overflow-x-auto">
            <table className="min-w-full divide-y divide-white/10 text-sm">
              <thead className="text-white/60">
                <tr>
                  <th className="py-3 pr-4 text-left">Strategy</th>
                  <th className="py-3 px-4 text-left">Win %</th>
                  <th className="py-3 px-4 text-left">ROI / bet</th>
                  <th className="py-3 px-4 text-left">Units</th>
                  <th className="py-3 px-4 text-left">Bets</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-white/80">
                {strategies.map((strategy) => (
                  <tr key={strategy.name}>
                    <td className="py-3 pr-4">
                      <p className="font-semibold text-white">{strategy.name}</p>
                      <p className="text-xs text-white/60">{strategy.note}</p>
                    </td>
                    <td className="py-3 px-4">{pct(strategy.winRate)}</td>
                    <td className="py-3 px-4">{((strategy.units / strategy.bets) * 100).toFixed(1)}%</td>
                    <td className="py-3 px-4 font-semibold text-lime-300">{strategy.units > 0 ? `+${strategy.units}` : strategy.units}u</td>
                    <td className="py-3 px-4">{strategy.bets.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-6 rounded-2xl border border-amber-200/30 bg-gradient-to-r from-amber-200/10 to-orange-200/10 p-5">
            <p className="text-sm font-semibold text-amber-200">⚠️  Disclaimer</p>
            <p className="mt-2 text-xs text-white/75">
              These strategy results are shown for transparency and calibration analysis. We are not a betting service and do not recommend specific wagers. Always bet responsibly.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
