import type { PredictionsPayload, Prediction } from "@/types/prediction";
import { getPredictionsPayload, selectCurrentSlate } from "@/lib/data";
import { PredictionTicker } from "@/components/PredictionTicker";
import { getPredictionGrade, normalizeSummaryWithGrade } from "@/lib/prediction";

const payload: PredictionsPayload = getPredictionsPayload();
const todaysPredictions = selectCurrentSlate(payload.games);
const updatedAt = payload.generatedAt ? new Date(payload.generatedAt) : null;

const formatTime = (iso?: string | null) => {
  if (!iso) return "TBD";
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    hour: "numeric",
    minute: "numeric",
  }).format(new Date(iso));
};

const numberFmt = (num: number) => `${(num * 100).toFixed(1)}%`;

function summarize(predictions: Prediction[]) {
  if (!predictions.length) {
    return {
      avgEdge: 0,
      aGrades: 0,
      tossUps: 0,
      bPlusEdges: 0,
    };
  }

  const edges = predictions.map((game) => Math.abs(game.edge));
  const avgEdge = edges.reduce((acc, curr) => acc + curr, 0) / predictions.length;
  const aGrades = predictions.filter((game) => getPredictionGrade(game.edge).label.startsWith("A")).length;
  const tossUps = predictions.filter((game) => Math.abs(game.edge) < 0.02).length;
  const bPlusEdges = predictions.filter((game) => {
    const label = getPredictionGrade(game.edge).label;
    return ["A+", "A", "A-", "B+", "B"].includes(label);
  }).length;

  return { avgEdge, aGrades, tossUps, bPlusEdges };
}

const summary = summarize(todaysPredictions);
const topEdges = [...todaysPredictions]
  .sort((a, b) => Math.abs(b.edge) - Math.abs(a.edge))
  .slice(0, 4);
const upsetRadar = todaysPredictions
  .filter((game) => game.modelFavorite === "away" && game.awayWinProb >= 0.55)
  .slice(0, 3);

export default function PredictionsPage() {
  return (
    <div className="relative overflow-hidden">
      <div className="relative mx-auto flex max-w-6xl flex-col gap-12 px-6 pb-16 pt-8 lg:px-12">
        <section>
          <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Slate intelligence</p>
          <div className="mt-3 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <h1 className="text-4xl font-semibold text-white">Full-game projections without opening a spreadsheet.</h1>
              <p className="mt-3 max-w-3xl text-base text-white/75">
                Lineup context, rolling form, NHL API features—everything that powers the dashboard now lives in this tab so you can
                scan the nearest slate in seconds.
              </p>
            </div>
            <div className="text-xs uppercase tracking-[0.45em] text-white/50">
              {updatedAt ? `Updated ${updatedAt.toLocaleString("en-US", { timeZone: "America/New_York" })}` : "Awaiting model run"}
            </div>
          </div>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <SummaryCard label="Avg model edge" value={`${(summary.avgEdge * 100).toFixed(1)} pts`} detail="vs coin flip" />
            <SummaryCard label="A-grade plays" value={`${summary.aGrades}`} detail={">60% confidence"} />
            <SummaryCard label="B-tier edges" value={`${summary.bPlusEdges}`} detail={">5% win delta"} />
            <SummaryCard label="True toss-ups" value={`${summary.tossUps}`} detail="<2% delta" />
          </div>
          <div className="mt-6">
            <PredictionTicker initial={payload} />
          </div>
        </section>

        {todaysPredictions.length > 0 ? (
          <>
            <section className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
              <div className="rounded-[32px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30">
                <p className="text-sm uppercase tracking-[0.4em] text-white/60">High-confidence set</p>
                <h2 className="mt-3 text-2xl font-semibold text-white">Largest probability gaps on the slate</h2>
                <div className="mt-6 space-y-4">
                  {topEdges.map((game) => {
                    const grade = getPredictionGrade(game.edge);
                    const summary = normalizeSummaryWithGrade(game.summary, grade.label);
                    return (
                      <div key={game.id} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                        <div className="flex flex-wrap items-baseline justify-between gap-2">
                          <p className="text-lg font-semibold text-white">
                            {game.awayTeam.abbrev} @ {game.homeTeam.abbrev}
                          </p>
                          <span className="text-sm uppercase tracking-[0.4em] text-lime-300">
                            {grade.label} · {(Math.abs(game.edge) * 100).toFixed(1)} pts edge
                          </span>
                        </div>
                        <p className="mt-1 text-sm text-white/60">Starts {game.startTimeEt ?? "TBD"}</p>
                        <p className="mt-3 text-base text-white/85">{summary}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
              <div className="rounded-[32px] border border-white/10 bg-gradient-to-br from-amber-200/20 via-rose-200/10 to-transparent p-8 shadow-2xl shadow-black/30">
                <p className="text-sm uppercase tracking-[0.4em] text-amber-200">Upset radar</p>
                <h2 className="mt-3 text-2xl font-semibold text-white">Road teams live to flip the script</h2>
                <div className="mt-6 space-y-4">
                  {upsetRadar.length ? (
                    upsetRadar.map((game) => {
                      const grade = getPredictionGrade(game.edge);
                      const summary = normalizeSummaryWithGrade(game.summary, grade.label);
                      return (
                        <div key={game.id} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                          <div className="flex items-center justify-between text-sm text-white/70">
                            <span>
                              {game.awayTeam.name} ({numberFmt(game.awayWinProb)})
                            </span>
                            <span>{formatTime(game.startTimeUtc)}</span>
                          </div>
                          <p className="mt-2 text-base text-white">{summary}</p>
                        </div>
                      );
                    })
                  ) : (
                    <p className="rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-white/70">
                      No &gt;55% road leans on the board right now.
                    </p>
                  )}
                </div>
              </div>
            </section>

            <section className="rounded-[36px] border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/30">
              <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
                <div>
                  <p className="text-sm uppercase tracking-[0.4em] text-white/50">Game-by-game sheet</p>
                  <h2 className="text-2xl font-semibold text-white">Shareable output from the nightly publish.</h2>
                  <p className="mt-1 text-sm text-white/70">Sorted by start time — win %, edge, and confidence score.</p>
                </div>
                <p className="text-xs uppercase tracking-[0.4em] text-white/40">All times ET</p>
              </div>
              <div className="mt-6 overflow-x-auto">
                <table className="min-w-full divide-y divide-white/10 text-sm">
                  <thead className="text-white/60">
                    <tr>
                      <th className="py-3 pr-4 text-left">Matchup</th>
                      <th className="py-3 px-4 text-left">Home %</th>
                      <th className="py-3 px-4 text-left">Road %</th>
                      <th className="py-3 px-4 text-left">Edge</th>
                      <th className="py-3 px-4 text-left">Δ</th>
                      <th className="py-3 px-4 text-left">Confidence</th>
                      <th className="py-3 px-4 text-left">Start</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 text-white/90">
                    {todaysPredictions
                      .slice()
                      .sort((a, b) => (a.startTimeUtc ?? "").localeCompare(b.startTimeUtc ?? ""))
                      .map((game) => (
                        <tr key={game.id}>
                          <td className="py-3 pr-4 font-medium text-white">
                            {game.awayTeam.abbrev} @ {game.homeTeam.abbrev}
                          </td>
                          <td className="py-3 px-4">{numberFmt(game.homeWinProb)}</td>
                          <td className="py-3 px-4">{numberFmt(game.awayWinProb)}</td>
                          <td className="py-3 px-4">{(game.edge * 100).toFixed(1)} pts</td>
                          <td className="py-3 px-4"><EdgeVisual value={game.edge} /></td>
                          <td className="py-3 px-4">{getPredictionGrade(game.edge).label}</td>
                          <td className="py-3 px-4">{game.startTimeEt ?? "TBD"}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        ) : (
          <div className="rounded-[32px] border border-white/10 bg-white/5 p-10 text-center text-white/70">
            No predictions yet. The nightly sync will post the next slate soon.
          </div>
        )}
      </div>
    </div>
  );
}

function SummaryCard({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="rounded-3xl border border-white/10 bg-black/20 p-5">
      <p className="text-xs uppercase tracking-[0.5em] text-white/60">{label}</p>
      <p className="mt-3 text-3xl font-semibold text-white">{value}</p>
      <p className="text-xs uppercase tracking-[0.4em] text-white/50">{detail}</p>
    </div>
  );
}

function EdgeVisual({ value }: { value: number }) {
  const pct = Math.min(Math.abs(value) * 200, 100);
  return (
    <div className="h-2 w-24 rounded-full bg-white/10">
      <div
        className={`h-full rounded-full ${value >= 0 ? "bg-gradient-to-r from-lime-300 to-emerald-400" : "bg-gradient-to-r from-rose-300 to-orange-400"}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}
