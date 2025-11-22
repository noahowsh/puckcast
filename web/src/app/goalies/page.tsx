import type { GoalieCard } from "@/types/goalie";
import { getGoaliePulse } from "@/lib/data";
import { GoalieTicker } from "@/components/GoalieTicker";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { TeamLogo } from "@/components/TeamLogo";

const pulse = getGoaliePulse();
const updatedAt = pulse.updatedAt ? new Date(pulse.updatedAt) : null;
const GOALIE_SUMMARY_ENDPOINT = "https://api.nhle.com/stats/rest/en/goalie/summary?isAggregate=true&limit=-1&cayenneExp=seasonId=20252026";

const trendConfig: Record<string, { color: string; icon: string }> = {
  surging: { color: "text-emerald-300", icon: "UP" },
  steady: { color: "text-sky-300", icon: "->" },
  fresh: { color: "text-cyan-300", icon: "NEW" },
  "fatigue watch": { color: "text-amber-300", icon: "WARN" },
};

const formatPercent = (value: number) => `${(value * 100).toFixed(0)}%`;

type GoalieSeasonLeader = {
  name: string;
  gamesPlayed: number;
  wins: number;
  savePct: number;
  gaa: number;
};

async function fetchGoalieSeasonLeaders(): Promise<GoalieSeasonLeader[]> {
  try {
    const res = await fetch(GOALIE_SUMMARY_ENDPOINT, { next: { revalidate: 3600 } });
    if (!res.ok) return [];
    const payload = (await res.json()) as { data: any[] };
    return payload.data
      .filter((entry) => entry.gamesPlayed >= 5 && typeof entry.savePct === "number")
      .sort((a, b) => b.savePct - a.savePct)
      .slice(0, 4)
      .map((entry) => ({
        name: entry.goalieFullName as string,
        gamesPlayed: entry.gamesPlayed as number,
        wins: entry.wins as number,
        savePct: entry.savePct as number,
        gaa: entry.goalsAgainstAverage as number,
      }));
  } catch (err) {
    console.error("Failed to fetch goalie summary", err);
    return [];
  }
}

export default async function GoaliePage() {
  const seasonLeaders = await fetchGoalieSeasonLeaders();
  const updatedDisplay = updatedAt
    ? updatedAt.toLocaleString("en-US", { timeZone: "America/New_York" })
    : null;

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

        {/* Season Leaders */}
        {seasonLeaders.length > 0 && (
          <section className="mb-12">
            <h2 className="text-2xl font-bold text-white mb-6">Season leaders</h2>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {seasonLeaders.map((leader, idx) => (
                <StatCard
                  key={leader.name}
                  label={`Top Save % #${idx + 1}`}
                  value={formatPercent(leader.savePct)}
                  change={{ value: `${leader.gamesPlayed} GP | ${leader.wins} W`, isPositive: true }}
                  className="bg-white/[0.03] border-white/10"
                />
              ))}
            </div>
          </section>
        )}

        {/* Live Ticker */}
        <section className="mb-12">
          <h3 className="text-xl font-bold text-white mb-4">Live goalie updates</h3>
          <GoalieTicker initial={pulse} />
        </section>

        {/* Goalie Cards */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Detailed analysis</h2>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
            {pulse.goalies.map((goalie) => (
              <GoalieCardView key={goalie.name} goalie={goalie} />
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

function GoalieCardView({ goalie }: { goalie: GoalieCard }) {
  const startLikelihood = formatPercent(goalie.startLikelihood);
  const trendStyle = trendConfig[goalie.trend] || { color: "text-white", icon: "" };
  const gsaxPositive = goalie.rollingGsa > 0;

  return (
    <article className="card">
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
