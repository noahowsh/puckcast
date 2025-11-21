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
  surging: { color: "text-green-400", icon: "📈" },
  steady: { color: "text-sky-400", icon: "➡️" },
  fresh: { color: "text-cyan-400", icon: "✨" },
  "fatigue watch": { color: "text-amber-400", icon: "⚠️" },
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
      <div className="container" style={{ paddingTop: '8rem' }}>
        <PageHeader
          title="Goalie Intelligence"
          description="Rolling GSAx, rest advantage analysis, start-likelihood signals, and comprehensive goalie tracking for every NHL netminder."
          icon={
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          }
        />

        {updatedDisplay && (
          <div className="mb-8 text-center">
            <p className="text-sm text-slate-500">
              Last updated {updatedDisplay} ET
            </p>
          </div>
        )}

        {/* Notes */}
        {pulse.notes && (
          <section className="mb-16">
            <div className="card bg-sky-500/5 border-sky-500/20">
              <p className="text-slate-300 leading-relaxed">{pulse.notes}</p>
            </div>
          </section>
        )}

        {/* Season Leaders */}
        {seasonLeaders.length > 0 && (
          <section className="mb-16">
            <h2 className="text-2xl font-bold text-white mb-8">Season Leaders</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 stagger-animation">
              {seasonLeaders.map((leader, idx) => (
                <div key={leader.name} className="stat-card">
                  <div className="flex items-center justify-between mb-3">
                    <div className="stat-label">Top Save %</div>
                    <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-sky-500/20 to-cyan-500/20 border border-sky-500/30">
                      <span className="text-sm font-bold text-sky-400">#{idx + 1}</span>
                    </div>
                  </div>
                  <div className="text-lg font-bold text-white mb-2">{leader.name}</div>
                  <div className="flex items-center gap-3 text-sm text-slate-400 mb-4">
                    <span>{leader.gamesPlayed} GP</span>
                    <span>•</span>
                    <span>{leader.wins} W</span>
                  </div>
                  <div className="stat-value text-3xl">{formatPercent(leader.savePct)}</div>
                  <div className="text-sm text-slate-400 mt-2">GAA {leader.gaa.toFixed(2)}</div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Live Ticker */}
        <section className="mb-16">
          <h3 className="text-xl font-bold text-white mb-6">Live Goalie Updates</h3>
          <div className="card-elevated">
            <GoalieTicker initial={pulse} />
          </div>
        </section>

        {/* Goalie Cards */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold text-white mb-8">Detailed Analysis</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
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
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center gap-3">
          <TeamLogo teamAbbrev={goalie.team} size="md" />
          <div>
            <h3 className="text-xl font-bold text-white">{goalie.name}</h3>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-sm text-slate-400">{goalie.team}</span>
              <span className="text-slate-600">•</span>
              <span className={`text-sm font-semibold ${trendStyle.color}`}>
                {trendStyle.icon} {goalie.trend}
              </span>
            </div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-slate-400 uppercase font-semibold mb-1">Start Odds</div>
          <div className="text-2xl font-bold text-white">{startLikelihood}</div>
          <div className="text-xs text-slate-500 mt-1">Rest: +{goalie.restDays}d</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="card-flat">
          <div className="stat-label mb-2">Rolling GSAx</div>
          <div className={`stat-value text-2xl ${gsaxPositive ? "text-green-400" : "text-red-400"}`}>
            {gsaxPositive ? "+" : ""}{goalie.rollingGsa.toFixed(1)}
          </div>
          <div className="text-xs text-slate-500 mt-1">Last 3 starts</div>
        </div>
        <div className="card-flat">
          <div className="stat-label mb-2">Season GSAx</div>
          <div className="stat-value text-2xl">{goalie.seasonGsa > 0 ? "+" : ""}{goalie.seasonGsa.toFixed(1)}</div>
          <div className="text-xs text-slate-500 mt-1">Full season</div>
        </div>
      </div>

      <p className="text-sm text-slate-300 leading-relaxed mb-6">{goalie.note}</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <div className="text-sm font-semibold text-slate-400 mb-3">Strengths</div>
          <ul className="space-y-2">
            {goalie.strengths.map((item) => (
              <li
                key={item}
                className="flex items-start gap-2 rounded-lg bg-green-500/10 border border-green-500/20 px-3 py-2 text-xs text-green-400"
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
          <div className="text-sm font-semibold text-slate-400 mb-3">Watch-outs</div>
          <ul className="space-y-2">
            {goalie.watchouts.map((item) => (
              <li
                key={item}
                className="flex items-start gap-2 rounded-lg bg-slate-800/50 border border-slate-700 px-3 py-2 text-xs text-slate-400"
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

      <div className="pt-4 border-t border-slate-800">
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-400">Next opponent</span>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-white">{goalie.nextOpponent}</span>
            <TeamLogo teamAbbrev={goalie.nextOpponent} size="xs" />
          </div>
        </div>
      </div>
    </article>
  );
}
