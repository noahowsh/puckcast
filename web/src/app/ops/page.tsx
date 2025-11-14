import { buildStatusSnapshot } from "@/lib/status";

export const revalidate = 60;

export default function OpsPage() {
  const snapshot = buildStatusSnapshot();
  return (
    <div className="relative overflow-hidden">
      <div className="relative mx-auto flex max-w-5xl flex-col gap-8 px-6 pb-16 pt-8 lg:px-10">
        <header className="space-y-3">
          <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Ops control</p>
          <h1 className="text-4xl font-semibold text-white">Is everything synced?</h1>
          <p className="max-w-3xl text-white/70">Quick read on predictions, goalie pulse, standings, and deploy metadata. Snapshots refresh every minute.</p>
        </header>

        <div className="grid gap-4 md:grid-cols-2">
          <StatusCard title="Predictions" metric={`${snapshot.predictions.games} games`} timestamp={snapshot.predictions.generatedAt} staleMinutes={snapshot.predictions.staleMinutes}>
            <p className="text-sm text-white/70">Generated at {renderDate(snapshot.predictions.generatedAt)}</p>
          </StatusCard>
          <StatusCard title="Goalies" metric={`${snapshot.goalies.projectedStarters} starters`} timestamp={snapshot.goalies.updatedAt} staleMinutes={snapshot.goalies.staleMinutes}>
            <p className="text-sm text-white/70">Projected games: {snapshot.goalies.projectedGames}</p>
          </StatusCard>
          <StatusCard title="Standings" metric={`${snapshot.standings.teams} teams`} timestamp={snapshot.standings.generatedAt} staleMinutes={snapshot.standings.staleMinutes}>
            <p className="text-sm text-white/70">Last sync {renderDate(snapshot.standings.generatedAt)}</p>
          </StatusCard>
          <StatusCard title="Deploy" metric={snapshot.deploy.env ?? "local"} timestamp={null} staleMinutes={null}>
            <p className="text-sm text-white/70">Commit {snapshot.deploy.commit ?? "—"}</p>
            <p className="text-sm text-white/70">Branch {snapshot.deploy.branch ?? "—"}</p>
          </StatusCard>
        </div>
      </div>
    </div>
  );
}

function StatusCard({ title, metric, timestamp, staleMinutes, children }: { title: string; metric: string; timestamp: string | null; staleMinutes: number | null; children?: React.ReactNode }) {
  const staleLabel = staleMinutes == null ? "—" : `${staleMinutes}m old`;
  const statusColor = staleMinutes != null && staleMinutes > 180 ? "text-rose-300" : "text-lime-200";

  return (
    <article className="rounded-[32px] border border-white/10 bg-white/5 p-5 shadow-2xl shadow-black/30">
      <div className="flex items-center justify-between">
        <p className="text-sm uppercase tracking-[0.4em] text-white/50">{title}</p>
        <p className={`text-xs uppercase tracking-[0.4em] ${statusColor}`}>{staleLabel}</p>
      </div>
      <p className="mt-3 text-3xl font-semibold text-white">{metric}</p>
      <p className="text-sm text-white/60">{timestamp ? `Updated ${renderDate(timestamp)}` : "Awaiting refresh"}</p>
      <div className="mt-3 text-sm text-white/80">{children}</div>
    </article>
  );
}

function renderDate(value: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleString("en-US", { timeZone: "America/New_York", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}
