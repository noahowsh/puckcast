import Link from "next/link";
import { fetchGoalieLeaders, fetchGoalieStats } from "@/lib/playerHub";
import { GoalieStatsTable, LeaderRow } from "@/components/PlayerStatsTable";
import { GoalieCardView } from "@/components/PlayerCard";

export const revalidate = 3600; // Revalidate every hour

export default async function GoaliePage() {
  const [goalieLeaders, allGoalies] = await Promise.all([
    fetchGoalieLeaders(),
    fetchGoalieStats(3),
  ]);

  const updatedAt = new Date().toLocaleString("en-US", { timeZone: "America/New_York", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });

  return (
    <div className="min-h-screen">
      <div className="container pt-24 pb-12">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">Goalie Intelligence</h1>
          <p className="text-sm text-white/50">2025-26 Season • Updated {updatedAt} ET</p>
        </div>

        {/* Navigation Links */}
        <div className="flex gap-3 mb-10">
          <Link href="/players" className="px-4 py-2 rounded-lg bg-white/[0.04] text-white/60 text-sm font-medium hover:bg-white/[0.06] transition-colors">
            All Players
          </Link>
          <Link href="/goalies" className="px-4 py-2 rounded-lg bg-sky-500/20 text-sky-400 text-sm font-medium">
            Goalie Intelligence
          </Link>
        </div>

        {/* League Leaders Grid */}
        <section className="mb-12">
          <h2 className="text-xl font-bold text-white mb-6">League Leaders</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {/* Wins */}
            <div className="rounded-xl border border-white/[0.06] bg-gradient-to-b from-white/[0.03] to-transparent p-5">
              <h3 className="text-sm font-semibold text-white/60 mb-4 uppercase tracking-wide flex items-center gap-2">
                <span className="w-6 h-6 rounded bg-emerald-500/20 flex items-center justify-center">
                  <svg className="w-3 h-3 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </span>
                Wins
              </h3>
              <div className="space-y-1">
                {goalieLeaders.wins.slice(0, 5).map((goalie, idx) => (
                  <LeaderRow
                    key={goalie.bio.playerId}
                    rank={idx + 1}
                    name={goalie.bio.lastName}
                    team={goalie.bio.teamAbbrev}
                    value={goalie.stats.wins}
                    playerId={goalie.bio.playerId}
                    isGoalie
                  />
                ))}
              </div>
            </div>

            {/* Save Percentage */}
            <div className="rounded-xl border border-white/[0.06] bg-gradient-to-b from-white/[0.03] to-transparent p-5">
              <h3 className="text-sm font-semibold text-white/60 mb-4 uppercase tracking-wide flex items-center gap-2">
                <span className="w-6 h-6 rounded bg-sky-500/20 flex items-center justify-center">
                  <svg className="w-3 h-3 text-sky-400" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                </span>
                Save %
              </h3>
              <div className="space-y-1">
                {goalieLeaders.savePct.slice(0, 5).map((goalie, idx) => (
                  <LeaderRow
                    key={goalie.bio.playerId}
                    rank={idx + 1}
                    name={goalie.bio.lastName}
                    team={goalie.bio.teamAbbrev}
                    value={`.${Math.round(goalie.stats.savePct * 1000)}`}
                    playerId={goalie.bio.playerId}
                    isGoalie
                  />
                ))}
              </div>
            </div>

            {/* GAA */}
            <div className="rounded-xl border border-white/[0.06] bg-gradient-to-b from-white/[0.03] to-transparent p-5">
              <h3 className="text-sm font-semibold text-white/60 mb-4 uppercase tracking-wide flex items-center gap-2">
                <span className="w-6 h-6 rounded bg-amber-500/20 flex items-center justify-center">
                  <svg className="w-3 h-3 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 0l-2 2a1 1 0 101.414 1.414L8 10.414l1.293 1.293a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </span>
                GAA
              </h3>
              <div className="space-y-1">
                {goalieLeaders.goalsAgainstAverage.slice(0, 5).map((goalie, idx) => (
                  <LeaderRow
                    key={goalie.bio.playerId}
                    rank={idx + 1}
                    name={goalie.bio.lastName}
                    team={goalie.bio.teamAbbrev}
                    value={goalie.stats.goalsAgainstAverage.toFixed(2)}
                    playerId={goalie.bio.playerId}
                    isGoalie
                  />
                ))}
              </div>
            </div>

            {/* Shutouts */}
            <div className="rounded-xl border border-white/[0.06] bg-gradient-to-b from-white/[0.03] to-transparent p-5">
              <h3 className="text-sm font-semibold text-white/60 mb-4 uppercase tracking-wide flex items-center gap-2">
                <span className="w-6 h-6 rounded bg-rose-500/20 flex items-center justify-center">
                  <svg className="w-3 h-3 text-rose-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M13.477 14.89A6 6 0 015.11 6.524l8.367 8.368zm1.414-1.414L6.524 5.11a6 6 0 018.367 8.367zM18 10a8 8 0 11-16 0 8 8 0 0116 0z" clipRule="evenodd" />
                  </svg>
                </span>
                Shutouts
              </h3>
              <div className="space-y-1">
                {goalieLeaders.shutouts.slice(0, 5).map((goalie, idx) => (
                  <LeaderRow
                    key={goalie.bio.playerId}
                    rank={idx + 1}
                    name={goalie.bio.lastName}
                    team={goalie.bio.teamAbbrev}
                    value={goalie.stats.shutouts}
                    playerId={goalie.bio.playerId}
                    isGoalie
                  />
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Top Goalies Cards */}
        <section className="mb-12">
          <h2 className="text-xl font-bold text-white mb-6">Top Performers</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {goalieLeaders.wins.slice(0, 4).map((goalie, idx) => (
              <GoalieCardView key={goalie.bio.playerId} goalie={goalie} rank={idx + 1} />
            ))}
          </div>
        </section>

        {/* Full Stats Table */}
        <section className="mb-12">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold text-white">All Goalies</h2>
              <p className="text-sm text-white/40 mt-1">Minimum 3 games played</p>
            </div>
          </div>
          <div className="rounded-xl border border-white/[0.06] bg-gradient-to-b from-white/[0.02] to-transparent overflow-hidden">
            <GoalieStatsTable goalies={allGoalies} maxRows={30} />
          </div>
        </section>
      </div>
    </div>
  );
}
