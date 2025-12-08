import { PageHeader } from "@/components/PageHeader";
import { SkaterStatsTable, GoalieStatsTable, LeaderRow } from "@/components/PlayerStatsTable";
import { fetchSkaterLeaders, fetchGoalieLeaders, fetchEnrichedSkaterStats, fetchGoalieStats } from "@/lib/playerHub";

export const revalidate = 3600; // Revalidate every hour

export default async function PlayersPage() {
  const [skaterLeaders, goalieLeaders, allSkaters, allGoalies] = await Promise.all([
    fetchSkaterLeaders(),
    fetchGoalieLeaders(),
    fetchEnrichedSkaterStats(5),
    fetchGoalieStats(3),
  ]);

  const updatedAt = new Date().toLocaleString("en-US", { timeZone: "America/New_York", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });

  return (
    <div className="min-h-screen">
      <div className="container" style={{ paddingTop: "8rem" }}>
        <PageHeader
          title="Player Stats"
          description="NHL league leaders and player statistics for the 2025-26 season."
          icon={
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          }
        />

        <div className="mb-8 flex items-center gap-3">
          <span className="text-xs font-medium text-white/40">Updated {updatedAt} ET</span>
          <span className="text-white/20">•</span>
          <span className="text-xs font-medium text-white/40">{allSkaters.length} skaters</span>
          <span className="text-white/20">•</span>
          <span className="text-xs font-medium text-white/40">{allGoalies.length} goalies</span>
        </div>

        {/* Scoring Leaders Grid */}
        <section className="mb-10">
          <h2 className="text-xl font-bold text-white mb-5">Scoring Leaders</h2>
          {skaterLeaders.points.length === 0 ? (
            <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-6 text-center">
              <p className="text-white/50">Skater statistics are being loaded. Please refresh the page.</p>
            </div>
          ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Points Leaders */}
            <div className="rounded-xl border border-white/[0.06] bg-gradient-to-b from-white/[0.03] to-transparent p-5">
              <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-lg bg-sky-500/15 flex items-center justify-center">
                  <svg className="w-3.5 h-3.5 text-sky-400" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                </span>
                Points
              </h3>
              <div className="space-y-0.5">
                {skaterLeaders.points.slice(0, 10).map((player, idx) => (
                  <LeaderRow
                    key={player.bio.playerId}
                    rank={idx + 1}
                    name={player.bio.fullName}
                    team={player.bio.teamAbbrev}
                    value={player.stats.points}
                    playerId={player.bio.playerId}
                  />
                ))}
              </div>
            </div>

            {/* Goals Leaders */}
            <div className="rounded-xl border border-white/[0.06] bg-gradient-to-b from-white/[0.03] to-transparent p-5">
              <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-lg bg-emerald-500/15 flex items-center justify-center">
                  <svg className="w-3.5 h-3.5 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                  </svg>
                </span>
                Goals
              </h3>
              <div className="space-y-0.5">
                {skaterLeaders.goals.slice(0, 10).map((player, idx) => (
                  <LeaderRow
                    key={player.bio.playerId}
                    rank={idx + 1}
                    name={player.bio.fullName}
                    team={player.bio.teamAbbrev}
                    value={player.stats.goals}
                    playerId={player.bio.playerId}
                  />
                ))}
              </div>
            </div>

            {/* Assists Leaders */}
            <div className="rounded-xl border border-white/[0.06] bg-gradient-to-b from-white/[0.03] to-transparent p-5">
              <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-lg bg-amber-500/15 flex items-center justify-center">
                  <svg className="w-3.5 h-3.5 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M15 8a3 3 0 10-2.977-2.63l-4.94 2.47a3 3 0 100 4.319l4.94 2.47a3 3 0 10.895-1.789l-4.94-2.47a3.027 3.027 0 000-.74l4.94-2.47C13.456 7.68 14.19 8 15 8z" />
                  </svg>
                </span>
                Assists
              </h3>
              <div className="space-y-0.5">
                {skaterLeaders.assists.slice(0, 10).map((player, idx) => (
                  <LeaderRow
                    key={player.bio.playerId}
                    rank={idx + 1}
                    name={player.bio.fullName}
                    team={player.bio.teamAbbrev}
                    value={player.stats.assists}
                    playerId={player.bio.playerId}
                  />
                ))}
              </div>
            </div>
          </div>
          )}
        </section>

        {/* Secondary Leaders */}
        <section className="mb-10">
          <h2 className="text-xl font-bold text-white mb-5">Category Leaders</h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Power Play Goals */}
            <div className="rounded-xl border border-white/[0.06] bg-gradient-to-b from-white/[0.03] to-transparent p-4">
              <h3 className="text-xs font-semibold text-white/50 mb-3 uppercase tracking-wide">Power Play Goals</h3>
              <div className="space-y-0.5">
                {skaterLeaders.powerPlayGoals.slice(0, 5).map((player, idx) => (
                  <LeaderRow
                    key={player.bio.playerId}
                    rank={idx + 1}
                    name={player.bio.lastName}
                    team={player.bio.teamAbbrev}
                    value={player.stats.powerPlayGoals}
                    playerId={player.bio.playerId}
                  />
                ))}
              </div>
            </div>

            {/* Plus/Minus */}
            <div className="rounded-xl border border-white/[0.06] bg-gradient-to-b from-white/[0.03] to-transparent p-4">
              <h3 className="text-xs font-semibold text-white/50 mb-3 uppercase tracking-wide">Plus/Minus</h3>
              <div className="space-y-0.5">
                {skaterLeaders.plusMinus.slice(0, 5).map((player, idx) => (
                  <LeaderRow
                    key={player.bio.playerId}
                    rank={idx + 1}
                    name={player.bio.lastName}
                    team={player.bio.teamAbbrev}
                    value={`+${player.stats.plusMinus}`}
                    playerId={player.bio.playerId}
                  />
                ))}
              </div>
            </div>

            {/* Game Winning Goals */}
            <div className="rounded-xl border border-white/[0.06] bg-gradient-to-b from-white/[0.03] to-transparent p-4">
              <h3 className="text-xs font-semibold text-white/50 mb-3 uppercase tracking-wide">Game Winners</h3>
              <div className="space-y-0.5">
                {skaterLeaders.gameWinningGoals.slice(0, 5).map((player, idx) => (
                  <LeaderRow
                    key={player.bio.playerId}
                    rank={idx + 1}
                    name={player.bio.lastName}
                    team={player.bio.teamAbbrev}
                    value={player.stats.gameWinningGoals}
                    playerId={player.bio.playerId}
                  />
                ))}
              </div>
            </div>

            {/* Shots */}
            <div className="rounded-xl border border-white/[0.06] bg-gradient-to-b from-white/[0.03] to-transparent p-4">
              <h3 className="text-xs font-semibold text-white/50 mb-3 uppercase tracking-wide">Shots</h3>
              <div className="space-y-0.5">
                {skaterLeaders.shots.slice(0, 5).map((player, idx) => (
                  <LeaderRow
                    key={player.bio.playerId}
                    rank={idx + 1}
                    name={player.bio.lastName}
                    team={player.bio.teamAbbrev}
                    value={player.stats.shots}
                    playerId={player.bio.playerId}
                  />
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Goalie Leaders */}
        <section className="mb-10">
          <h2 className="text-xl font-bold text-white mb-5">Goalie Leaders</h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Wins */}
            <div className="rounded-xl border border-white/[0.06] bg-gradient-to-b from-white/[0.03] to-transparent p-4">
              <h3 className="text-xs font-semibold text-white/50 mb-3 uppercase tracking-wide">Wins</h3>
              <div className="space-y-0.5">
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
            <div className="rounded-xl border border-white/[0.06] bg-gradient-to-b from-white/[0.03] to-transparent p-4">
              <h3 className="text-xs font-semibold text-white/50 mb-3 uppercase tracking-wide">Save %</h3>
              <div className="space-y-0.5">
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
            <div className="rounded-xl border border-white/[0.06] bg-gradient-to-b from-white/[0.03] to-transparent p-4">
              <h3 className="text-xs font-semibold text-white/50 mb-3 uppercase tracking-wide">GAA</h3>
              <div className="space-y-0.5">
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
            <div className="rounded-xl border border-white/[0.06] bg-gradient-to-b from-white/[0.03] to-transparent p-4">
              <h3 className="text-xs font-semibold text-white/50 mb-3 uppercase tracking-wide">Shutouts</h3>
              <div className="space-y-0.5">
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

        {/* Full Stats Table */}
        <section className="mb-12">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold text-white">All Skaters</h2>
              <p className="text-sm text-white/40 mt-1">Minimum 5 games played</p>
            </div>
          </div>
          <div className="rounded-xl border border-white/[0.06] bg-gradient-to-b from-white/[0.02] to-transparent overflow-hidden">
            <SkaterStatsTable players={allSkaters} maxRows={50} />
          </div>
        </section>

        {/* Goalie Stats Table */}
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
