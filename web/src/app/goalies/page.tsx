import { getGoaliePulse } from "@/lib/data";
import { GoalieTicker } from "@/components/GoalieTicker";
import type { GoalieMatchup, GoalieHeatEntry, GoalieRestEntry, GoalieSeasonLeader, GoalieStarter } from "@/types/goalie";

const pulse = getGoaliePulse();

const fmtPct = (value: number | null | undefined, digits = 1) =>
  typeof value === "number" ? `${(value * 100).toFixed(digits)}%` : "—";

const fmtRest = (value: number | null | undefined) => (typeof value === "number" ? `${value}d rest` : "On alert");

const fmtDate = (value: string | null | undefined) => (value ? new Date(value).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "—");

export default function GoaliePage() {
  const updated = new Date(pulse.updatedAt).toLocaleString("en-US", {
    timeZone: "America/New_York",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });

  const quickStats = buildQuickStats();

  return (
    <div className="relative overflow-hidden">
      <div className="relative mx-auto flex max-w-6xl flex-col gap-12 px-6 pb-16 pt-8 lg:px-12">
        <section className="space-y-4">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Goalie command center</p>
              <h1 className="text-4xl font-semibold text-white">Automatically surfaced starters, heaters, and rest edges.</h1>
              <p className="mt-3 max-w-3xl text-base text-white/75">Data ingests NHL Stats play-by-play every morning at 6 AM ET to project likely starters, momentum, and bench freshness for tonight&apos;s slate.</p>
            </div>
            <div className="text-right text-xs uppercase tracking-[0.4em] text-white/50">
              <p>Updated {updated}</p>
              <p className="text-white/40">Target: {pulse.targetDate}</p>
            </div>
          </div>
          <p className="rounded-3xl border border-white/10 bg-white/5 p-4 text-sm text-white/80">{pulse.notes}</p>
          <div className="grid gap-4 md:grid-cols-3">
            {quickStats.map((stat) => (
              <article key={stat.label} className="rounded-3xl border border-white/10 bg-black/30 p-4">
                <p className="text-xs uppercase tracking-[0.4em] text-white/50">{stat.label}</p>
                <p className="mt-2 text-2xl font-semibold text-white">{stat.value}</p>
                <p className="text-xs uppercase tracking-[0.4em] text-white/40">{stat.detail}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Tonight&apos;s probable starters</p>
              <p className="text-white/60">Confidence blends recent usage, rest, and last five starts for every team on the slate.</p>
            </div>
            <p className="text-xs uppercase tracking-[0.4em] text-white/40">{pulse.tonight.games.length} games</p>
          </div>
          {pulse.tonight.games.length === 0 ? (
            <div className="rounded-3xl border border-white/10 bg-white/5 p-6 text-white/70">No NHL games on the schedule today.</div>
          ) : (
            <div className="space-y-4">
              {pulse.tonight.games.map((game) => (
                <MatchupCard key={game.gameId} game={game} />
              ))}
            </div>
          )}
        </section>

        <section className="grid gap-6 lg:grid-cols-3">
          <article className="rounded-[36px] border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/30 lg:col-span-2">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Heat check</p>
              <p className="text-xs uppercase tracking-[0.4em] text-white/40">Rolling save% vs season baseline</p>
            </div>
            <div className="mt-6 grid gap-6 md:grid-cols-2">
              <HeatColumn title="Trending up" accent="text-lime-200" data={pulse.heatCheck.surging} />
              <HeatColumn title="Cooling off" accent="text-rose-200" data={pulse.heatCheck.cooling} />
            </div>
          </article>
          <GoalieTicker initial={pulse} />
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <article className="rounded-[36px] border border-white/10 bg-gradient-to-br from-black/40 via-slate-900/60 to-slate-950 p-6 shadow-2xl shadow-black/40">
            <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Rest watch</p>
            <p className="text-sm text-white/70">Who&apos;s the freshest — and who&apos;s riding fumes.</p>
            <div className="mt-5 space-y-4">
              {pulse.restWatch.map((entry) => (
                <RestRow key={entry.name} entry={entry} />
              ))}
            </div>
          </article>
          <article className="rounded-[36px] border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/30">
            <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Season leaders</p>
            <div className="mt-5 space-y-4">
              {pulse.seasonLeaders.map((leader) => (
                <LeaderCard key={leader.name} leader={leader} />
              ))}
            </div>
          </article>
        </section>
      </div>
    </div>
  );
}

function MatchupCard({ game }: { game: GoalieMatchup }) {
  return (
    <article className="rounded-[36px] border border-white/10 bg-black/20 p-6 shadow-2xl shadow-black/30">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-white/50">{game.startTimeEt}</p>
          <p className="text-xl font-semibold text-white">{game.matchup}</p>
        </div>
        <p className="text-xs uppercase tracking-[0.4em] text-white/40">Projected starters</p>
      </div>
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <StarterColumn label="Away" goalie={game.away} />
        <StarterColumn label="Home" goalie={game.home} />
      </div>
    </article>
  );
}

function StarterColumn({ label, goalie }: { label: string; goalie: GoalieStarter | null }) {
  if (!goalie) {
    return (
      <div className="rounded-3xl border border-dashed border-white/20 bg-white/5 p-4 text-white/50">
        <p className="text-xs uppercase tracking-[0.4em]">{label}</p>
        <p className="mt-2 text-base">TBD — monitor morning skate</p>
      </div>
    );
  }

  return (
    <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-black/40 to-slate-900/40 p-4 text-white">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-white/50">{label}</p>
          <p className="text-lg font-semibold">{goalie.team}</p>
        </div>
        <div className="text-right text-xs uppercase tracking-[0.4em] text-lime-200">
          {goalie.startLikelihood != null ? `${Math.round(goalie.startLikelihood * 100)}% lock` : "TBD"}
        </div>
      </div>
      <p className="mt-2 text-2xl font-semibold">{goalie.name}</p>
      <p className="text-sm text-white/70">
        {fmtRest(goalie.restDays)} · last vs {goalie.lastOpponent ?? "TBD"}
      </p>
      <div className="mt-4 grid grid-cols-3 gap-3 text-center text-sm">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-white/50">Rolling SV%</p>
          <p className="text-base">{fmtPct(goalie.rollingSavePct)}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-white/50">Season SV%</p>
          <p className="text-base">{fmtPct(goalie.seasonSavePct)}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-white/50">Record</p>
          <p className="text-base">{goalie.record}</p>
        </div>
      </div>
    </div>
  );
}

function HeatColumn({ title, accent, data }: { title: string; accent: string; data: GoalieHeatEntry[] }) {
  if (data.length === 0) {
    return <p className="text-white/60">No goalies have enough data yet.</p>;
  }

  return (
    <div className="space-y-3">
      <p className={`text-xs uppercase tracking-[0.4em] ${accent}`}>{title}</p>
      {data.map((entry) => (
        <div key={entry.name} className="rounded-3xl border border-white/10 bg-black/30 p-4">
          <div className="flex items-center justify-between text-white">
            <p className="text-base font-semibold">{entry.name}</p>
            <p className="text-xs uppercase tracking-[0.4em] text-white/50">{entry.team}</p>
          </div>
          <p className="text-sm text-white/70">Last opp: {entry.lastOpponent ?? "TBD"}</p>
          <div className="mt-3 grid grid-cols-3 text-center text-sm">
            <div>
              <p className="text-xs uppercase tracking-[0.4em] text-white/50">Rolling</p>
              <p className="text-base">{fmtPct(entry.rollingSavePct)}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.4em] text-white/50">Season</p>
              <p className="text-base">{fmtPct(entry.seasonSavePct)}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.4em] text-white/50">Δ SV%</p>
              <p className="text-base">{entry.deltaSavePct ? `${(entry.deltaSavePct * 100).toFixed(1)} pts` : "—"}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function RestRow({ entry }: { entry: GoalieRestEntry }) {
  return (
    <div className="flex items-center justify-between rounded-3xl border border-white/10 bg-black/20 px-4 py-3 text-white">
      <div>
        <p className="text-sm font-semibold">{entry.name}</p>
        <p className="text-xs uppercase tracking-[0.4em] text-white/50">{entry.team}</p>
      </div>
      <div className="text-right">
        <p className="text-lime-200">{fmtRest(entry.restDays)}</p>
        <p className="text-xs text-white/50">Last start {fmtDate(entry.lastStart)}</p>
      </div>
    </div>
  );
}

function LeaderCard({ leader }: { leader: GoalieSeasonLeader }) {
  return (
    <div className="rounded-3xl border border-white/10 bg-black/20 p-4 text-white">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold">{leader.name}</p>
          <p className="text-xs uppercase tracking-[0.4em] text-white/50">{leader.team}</p>
        </div>
        <p className="text-xs uppercase tracking-[0.4em] text-white/50">{leader.games} GP</p>
      </div>
      <div className="mt-3 grid grid-cols-3 text-center text-sm">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-white/50">SV%</p>
          <p className="text-base">{fmtPct(leader.savePct, 2)}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-white/50">GAA</p>
          <p className="text-base">{leader.gaa.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-white/50">Record</p>
          <p className="text-base">{leader.record}</p>
        </div>
      </div>
    </div>
  );
}

function buildQuickStats() {
  const totalGames = pulse.tonight.games.length;
  const bestStarter = selectBestStarter();
  const freshest = pulse.restWatch[0];
  return [
    {
      label: "Tonight's slate",
      value: totalGames ? `${totalGames} games` : "Off day",
      detail: totalGames ? "projected starters listed" : "no games scheduled",
    },
    {
      label: "Most locked-in",
      value: bestStarter ? `${bestStarter.name}` : "TBD",
      detail: bestStarter ? `${Math.round((bestStarter.startLikelihood ?? 0) * 100)}% odds` : "awaiting confirmations",
    },
    {
      label: "Freshest crease",
      value: freshest ? freshest.name : "—",
      detail: freshest ? fmtRest(freshest.restDays) : "pending",
    },
  ];
}

function selectBestStarter(): GoalieStarter | null {
  const candidates: GoalieStarter[] = [];
  pulse.tonight.games.forEach((game) => {
    if (game.home) candidates.push(game.home);
    if (game.away) candidates.push(game.away);
  });
  if (!candidates.length) return null;
  return candidates.reduce((best, current) => {
    const currentScore = current.startLikelihood ?? 0;
    const bestScore = best.startLikelihood ?? 0;
    return currentScore > bestScore ? current : best;
  });
}
