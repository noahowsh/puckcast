import type { GoalieCard } from "@/types/goalie";
import { getGoaliePulse } from "@/lib/data";
import { GoalieTicker } from "@/components/GoalieTicker";

const pulse = getGoaliePulse();
const updatedAt = pulse.updatedAt ? new Date(pulse.updatedAt) : null;
const GOALIE_SUMMARY_ENDPOINT = "https://api.nhle.com/stats/rest/en/goalie/summary?isAggregate=true&limit=-1&cayenneExp=seasonId=20252026";

const trendColors: Record<string, string> = {
  surging: "text-sky-400",
  steady: "text-sky-400",
  fresh: "text-sky-400",
  "fatigue watch": "text-slate-400",
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
  return (
    <div className="relative min-h-screen bg-slate-950">
      {/* Subtle background gradient */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-b from-sky-950/20 via-slate-950 to-slate-950" />
      </div>

      <div className="relative mx-auto max-w-7xl px-6 py-16 lg:px-8">
        {/* Header */}
        <section className="mb-20">
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-sky-500/20 bg-sky-500/5 px-3 py-1">
            <span className="text-xs font-medium text-sky-400">Goalie Intelligence</span>
          </div>
          <h1 className="mb-4 text-4xl font-bold text-white lg:text-5xl">Goalie tracking & analysis</h1>
          <p className="max-w-3xl text-lg text-slate-300">
            Blending rolling GSAx, rest advantage, rebound control metrics, and start-likelihood signals from morning skate intel.
          </p>
          {updatedAt && (
            <p className="mt-2 text-sm text-slate-500">
              Updated {updatedAt.toLocaleString("en-US", { timeZone: "America/New_York" })} ET
            </p>
          )}
        </section>

        {/* Notes */}
        <section className="mb-20">
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
            <p className="text-sm text-slate-300">{pulse.notes}</p>
          </div>
        </section>

        {/* Season Leaders */}
        {seasonLeaders.length > 0 && (
          <section className="mb-20">
            <h2 className="mb-8 text-2xl font-bold text-white">Season Leaders</h2>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {seasonLeaders.map((leader) => (
                <article key={leader.name} className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
                  <p className="text-sm font-medium text-slate-400">Top Save %</p>
                  <p className="mt-2 text-lg font-semibold text-white">{leader.name}</p>
                  <div className="mt-3 flex items-center gap-4 text-sm text-slate-400">
                    <span>{leader.gamesPlayed} GP</span>
                    <span>{leader.wins} W</span>
                  </div>
                  <p className="mt-4 text-2xl font-bold text-sky-400">{formatPercent(leader.savePct)}</p>
                  <p className="mt-1 text-sm text-slate-500">SV% · GAA {leader.gaa.toFixed(2)}</p>
                </article>
              ))}
            </div>
          </section>
        )}

        {/* Live Ticker */}
        <section className="mb-20">
          <GoalieTicker initial={pulse} />
        </section>

        {/* Goalie Cards */}
        <section className="mb-20">
          <h2 className="mb-8 text-2xl font-bold text-white">Detailed Analysis</h2>
          <div className="grid gap-6 md:grid-cols-2">
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
  const trendColor = trendColors[goalie.trend] ?? "text-white";
  return (
    <article className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-400">{goalie.team}</p>
          <h3 className="mt-1 text-2xl font-bold text-white">{goalie.name}</h3>
          <p className={`mt-1 text-sm font-medium ${trendColor}`}>{goalie.trend}</p>
        </div>
        <div className="text-right">
          <p className="text-sm text-slate-400">Start Odds</p>
          <p className="mt-1 text-2xl font-bold text-white">{startLikelihood}</p>
          <p className="mt-1 text-xs text-slate-500">Rest +{goalie.restDays}d</p>
        </div>
      </div>
      <div className="mt-6 grid grid-cols-2 gap-4">
        <div className="rounded-lg border border-slate-800/50 bg-slate-950/50 p-4">
          <p className="text-sm font-medium text-slate-400">Rolling GSAx</p>
          <p className="mt-2 text-2xl font-bold text-white">{goalie.rollingGsa.toFixed(1)}</p>
          <p className="mt-1 text-xs text-slate-500">Last 3 starts</p>
        </div>
        <div className="rounded-lg border border-slate-800/50 bg-slate-950/50 p-4">
          <p className="text-sm font-medium text-slate-400">Season GSAx</p>
          <p className="mt-2 text-2xl font-bold text-white">{goalie.seasonGsa.toFixed(1)}</p>
          <p className="mt-1 text-xs text-slate-500">League average</p>
        </div>
      </div>
      <p className="mt-6 text-sm text-slate-300">{goalie.note}</p>
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <div>
          <p className="mb-2 text-sm font-medium text-slate-400">Strengths</p>
          <ul className="space-y-2">
            {goalie.strengths.map((item) => (
              <li key={item} className="rounded-lg bg-sky-500/10 px-3 py-2 text-xs text-sky-400">{item}</li>
            ))}
          </ul>
        </div>
        <div>
          <p className="mb-2 text-sm font-medium text-slate-400">Watch-outs</p>
          <ul className="space-y-2">
            {goalie.watchouts.map((item) => (
              <li key={item} className="rounded-lg bg-slate-800/50 px-3 py-2 text-xs text-slate-400">
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
      <p className="mt-6 text-xs text-slate-500">Next opponent: {goalie.nextOpponent}</p>
    </article>
  );
}
