import type { GoalieCard } from "@/types/goalie";
import { getGoaliePulse } from "@/lib/data";
import { GoalieTicker } from "@/components/GoalieTicker";

const pulse = getGoaliePulse();
const updatedAt = pulse.updatedAt ? new Date(pulse.updatedAt) : null;
const GOALIE_SUMMARY_ENDPOINT = "https://api.nhle.com/stats/rest/en/goalie/summary?isAggregate=true&limit=-1&cayenneExp=seasonId=20252026";

const trendColors: Record<string, string> = {
  surging: "text-lime-300",
  steady: "text-emerald-200",
  fresh: "text-sky-200",
  "fatigue watch": "text-amber-200",
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
    <div className="relative overflow-hidden">
      <div className="relative mx-auto flex max-w-6xl flex-col gap-12 px-6 pb-16 pt-8 lg:px-12">
        <section className="space-y-4">
          <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Goalie intelligence</p>
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <h1 className="text-4xl font-semibold text-white">Tracking who actually moves tonight&apos;s moneyline.</h1>
              <p className="mt-3 max-w-3xl text-base text-white/75">We blend rolling GSAx, rest advantage, rebound control metrics, and start-likelihood signals from morning skate intel.</p>
            </div>
            <div className="text-xs uppercase tracking-[0.45em] text-white/50">
              {updatedAt ? `Updated ${updatedAt.toLocaleString("en-US", { timeZone: "America/New_York" })}` : "Awaiting goalie report"}
            </div>
          </div>
          <p className="rounded-3xl border border-white/10 bg-white/5 p-4 text-sm text-white/80">{pulse.notes}</p>
          {seasonLeaders.length > 0 && (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {seasonLeaders.map((leader) => (
                <article key={leader.name} className="rounded-3xl border border-white/10 bg-black/20 p-4">
                  <p className="text-xs uppercase tracking-[0.4em] text-white/60">Season leader</p>
                  <p className="mt-1 text-lg font-semibold text-white">{leader.name}</p>
                  <div className="mt-3 flex items-center justify-between text-sm text-white/80">
                    <span>{leader.gamesPlayed} gp</span>
                    <span>{leader.wins} wins</span>
                  </div>
                  <p className="mt-3 text-2xl font-semibold text-white">{formatPercent(leader.savePct)}</p>
                  <p className="text-xs uppercase tracking-[0.4em] text-white/50">SV% · GAA {leader.gaa.toFixed(2)}</p>
                </article>
              ))}
            </div>
          )}
          <GoalieTicker initial={pulse} />
        </section>

        <section className="grid gap-6 md:grid-cols-2">
          {pulse.goalies.map((goalie) => (
            <GoalieCardView key={goalie.name} goalie={goalie} />
          ))}
        </section>

      </div>
    </div>
  );
}

function GoalieCardView({ goalie }: { goalie: GoalieCard }) {
  const startLikelihood = formatPercent(goalie.startLikelihood);
  const trendColor = trendColors[goalie.trend] ?? "text-white";
  return (
    <article className="rounded-[32px] border border-white/10 bg-black/20 p-6 shadow-2xl shadow-black/30">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.5em] text-white/60">{goalie.team}</p>
          <h3 className="mt-1 text-2xl font-semibold text-white">{goalie.name}</h3>
          <p className={`text-sm uppercase tracking-[0.4em] ${trendColor}`}>{goalie.trend}</p>
        </div>
        <div className="text-right text-sm text-white/70">
          <p>Start odds</p>
          <p className="text-2xl font-semibold text-white">{startLikelihood}</p>
          <p className="text-xs uppercase tracking-[0.4em] text-white/50">Rest +{goalie.restDays}d</p>
        </div>
      </div>
      <div className="mt-6 grid grid-cols-2 gap-4 text-sm text-white/80">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
          <p className="text-xs uppercase tracking-[0.4em] text-white/60">Rolling GSAx</p>
          <p className="text-2xl font-semibold text-white">{goalie.rollingGsa.toFixed(1)}</p>
          <p className="text-xs text-white/50">Last 3 starts</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
          <p className="text-xs uppercase tracking-[0.4em] text-white/60">Season GSAx</p>
          <p className="text-2xl font-semibold text-white">{goalie.seasonGsa.toFixed(1)}</p>
          <p className="text-xs text-white/50">League average baseline</p>
        </div>
      </div>
      <p className="mt-5 text-base text-white/90">{goalie.note}</p>
      <div className="mt-5 grid gap-4 text-sm text-white/80 md:grid-cols-2">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-white/50">Strength levers</p>
          <ul className="mt-2 space-y-1">
            {goalie.strengths.map((item) => (
              <li key={item} className="rounded-full bg-white/10 px-3 py-1 text-xs uppercase tracking-[0.3em]">{item}</li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-white/50">Watch-outs</p>
          <ul className="mt-2 space-y-1">
            {goalie.watchouts.map((item) => (
              <li key={item} className="rounded-full bg-white/5 px-3 py-1 text-xs uppercase tracking-[0.3em] text-amber-200">
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
      <p className="mt-5 text-xs uppercase tracking-[0.5em] text-white/50">Next opponent · {goalie.nextOpponent}</p>
    </article>
  );
}
