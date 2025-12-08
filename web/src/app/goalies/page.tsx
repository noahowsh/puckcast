import type { GoalieCard } from "@/types/goalie";
import { getGoaliePulse } from "@/lib/data";
import { fetchGoalieLeaders, fetchGoalieStats } from "@/lib/playerHub";
import { GoalieTicker } from "@/components/GoalieTicker";
import { PageHeader } from "@/components/PageHeader";
import { TeamLogo } from "@/components/TeamLogo";
import { GoalieStatsTable, LeaderRow } from "@/components/PlayerStatsTable";
import { GoalieCardView } from "@/components/PlayerCard";

export const revalidate = 3600; // Revalidate every hour

const pulse = getGoaliePulse();
const updatedAt = pulse.updatedAt ? new Date(pulse.updatedAt) : null;

const trendConfig: Record<string, { color: string; icon: string }> = {
  surging: { color: "text-emerald-300", icon: "UP" },
  steady: { color: "text-sky-300", icon: "->" },
  fresh: { color: "text-cyan-300", icon: "NEW" },
  "fatigue watch": { color: "text-amber-300", icon: "WARN" },
};

const formatPercent = (value: number) => `${(value * 100).toFixed(0)}%`;

export default async function GoaliePage() {
  const [goalieLeaders, allGoalies] = await Promise.all([
    fetchGoalieLeaders(),
    fetchGoalieStats(3),
  ]);

  const updatedDisplay = updatedAt
    ? updatedAt.toLocaleString("en-US", { timeZone: "America/New_York" })
    : new Date().toLocaleString("en-US", { timeZone: "America/New_York" });

  return (
    <div className="min-h-screen">
      <div className="container" style={{ paddingTop: "8rem" }}>
        <PageHeader
          title="Goalie Intelligence"
          description="Rolling GSAx, rest advantage, start-likelihood signals, and trending form for every NHL netminder."
          icon={
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          }
        />

        {updatedDisplay && (
          <div className="mb-8">
            <span className="chip text-xs font-semibold text-white/80">Last updated {updatedDisplay} ET</span>
          </div>
        )}

        {/* Notes */}
        {pulse.notes && (
          <section className="mb-12">
            <div className="card bg-sky-500/5 border-sky-500/20">
              <p className="text-white/80 leading-relaxed">{pulse.notes}</p>
            </div>
          </section>
        )}

        {/* League Leaders Grid */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">League Leaders</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Wins */}
            <div className="card p-4">
              <h3 className="text-sm font-semibold text-white/70 mb-3 uppercase tracking-wide flex items-center gap-2">
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
            <div className="card p-4">
              <h3 className="text-sm font-semibold text-white/70 mb-3 uppercase tracking-wide flex items-center gap-2">
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
            <div className="card p-4">
              <h3 className="text-sm font-semibold text-white/70 mb-3 uppercase tracking-wide flex items-center gap-2">
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
            <div className="card p-4">
              <h3 className="text-sm font-semibold text-white/70 mb-3 uppercase tracking-wide flex items-center gap-2">
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
          <h2 className="text-2xl font-bold text-white mb-6">Top Performers</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {goalieLeaders.wins.slice(0, 4).map((goalie, idx) => (
              <GoalieCardView key={goalie.bio.playerId} goalie={goalie} rank={idx + 1} />
            ))}
          </div>
        </section>

        {/* Live Ticker */}
        <section className="mb-12">
          <h3 className="text-xl font-bold text-white mb-4">Live goalie updates</h3>
          <GoalieTicker initial={pulse} />
        </section>

        {/* Goalie Intelligence Cards */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Detailed analysis</h2>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
            {pulse.goalies.map((goalie) => (
              <GoalieIntelCard key={goalie.name} goalie={goalie} />
            ))}
          </div>
        </section>

        {/* Full Stats Table */}
        <section className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white">All Goalies</h2>
            <span className="text-sm text-white/50">Minimum 3 games played</span>
          </div>
          <div className="card p-0 overflow-hidden">
            <GoalieStatsTable goalies={allGoalies} maxRows={40} />
          </div>
        </section>
      </div>
    </div>
  );
}

function GoalieIntelCard({ goalie }: { goalie: GoalieCard }) {
  const startLikelihood = formatPercent(goalie.startLikelihood);
  const trendStyle = trendConfig[goalie.trend] || { color: "text-white", icon: "" };
  const gsaxPositive = goalie.rollingGsa > 0;

  return (
    <article className="card hover:border-white/20 transition-all duration-200">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between mb-4">
            <div className="flex items-center gap-3">
              <TeamLogo teamAbbrev={goalie.team} size="md" />
              <div>
                <h3 className="text-xl font-bold text-white">{goalie.name}</h3>
                <div className="flex items-center gap-2 mt-1 text-sm">
                  <span className="text-white/70">{goalie.team}</span>
                  <span className="text-white/40">-</span>
                  <span className={`font-semibold ${trendStyle.color}`}>
                    {trendStyle.icon} {goalie.trend}
                  </span>
                </div>
              </div>
        </div>
        <div className="text-right">
          <div className="text-xs uppercase tracking-[0.2em] text-white/50 mb-1">Start odds</div>
          <div className="text-2xl font-bold text-white">{startLikelihood}</div>
          <div className="text-xs text-white/60 mt-1">Rest: +{goalie.restDays}d</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="card-flat">
          <div className="stat-label mb-2">Rolling GSAx</div>
          <div className={`stat-value text-2xl ${gsaxPositive ? "text-emerald-300" : "text-rose-300"}`}>
            {gsaxPositive ? "+" : ""}
            {goalie.rollingGsa.toFixed(1)}
          </div>
          <div className="text-xs text-white/60 mt-1">Last 3 starts</div>
        </div>
        <div className="card-flat">
          <div className="stat-label mb-2">Season GSAx</div>
          <div className="stat-value text-2xl">{goalie.seasonGsa > 0 ? "+" : ""}{goalie.seasonGsa.toFixed(1)}</div>
          <div className="text-xs text-white/60 mt-1">Full season</div>
        </div>
      </div>

      <p className="text-sm text-white/80 leading-relaxed mb-6">{goalie.note}</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <div className="text-sm font-semibold text-white/70 mb-3">Strengths</div>
          <ul className="space-y-2">
            {goalie.strengths.map((item) => (
              <li
                key={item}
                className="flex items-start gap-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 px-3 py-2 text-xs text-emerald-200"
              >
                <svg className="w-3 h-3 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <div className="text-sm font-semibold text-white/70 mb-3">Watch-outs</div>
          <ul className="space-y-2">
            {goalie.watchouts.map((item) => (
              <li
                key={item}
                className="flex items-start gap-2 rounded-lg bg-white/[0.03] border border-white/10 px-3 py-2 text-xs text-white/70"
              >
                <svg className="w-3 h-3 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="pt-4 border-t border-white/10">
        <div className="flex items-center justify-between text-sm">
          <span className="text-white/70">Next opponent</span>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-white">{goalie.nextOpponent}</span>
            <TeamLogo teamAbbrev={goalie.nextOpponent} size="xs" />
          </div>
        </div>
      </div>
    </article>
  );
}
