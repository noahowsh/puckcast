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
    <div className="relative min-h-screen bg-slate-950">
      {/* Premium background gradient */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-b from-slate-900/50 via-slate-950 to-slate-950" />
      </div>

      <div className="relative mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        {/* Header */}
        <section className="mb-24 lg:mb-32">
          <div className="mx-auto max-w-4xl text-center">
            <div className="mb-6 inline-flex items-center gap-2.5 rounded-full border border-sky-500/20 bg-sky-500/5 px-4 py-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-sky-400">Slate Intelligence</span>
            </div>

            <h1 className="mb-6 text-5xl font-bold tracking-tight text-white sm:text-6xl lg:text-7xl">
              Tonight's Predictions
            </h1>

            <p className="mx-auto mb-8 max-w-2xl text-lg leading-relaxed text-slate-300 sm:text-xl">
              Full-game projections with lineup context, rolling form, and NHL API features.
              Everything you need to scan the slate in seconds.
            </p>

            {updatedAt && (
              <p className="text-sm text-slate-500">
                Last updated {updatedAt.toLocaleString("en-US", { timeZone: "America/New_York" })} ET
              </p>
            )}
          </div>
        </section>

        {/* Summary Stats */}
        <section className="mb-24 lg:mb-32">
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <SummaryCard
              label="Avg Model Edge"
              value={`${(summary.avgEdge * 100).toFixed(1)} pts`}
              detail="vs coin flip"
            />
            <SummaryCard
              label="A-Grade Plays"
              value={`${summary.aGrades}`}
              detail=">60% confidence"
            />
            <SummaryCard
              label="B-Tier Edges"
              value={`${summary.bPlusEdges}`}
              detail=">5% win delta"
            />
            <SummaryCard
              label="True Toss-Ups"
              value={`${summary.tossUps}`}
              detail="<2% delta"
            />
          </div>
        </section>

        {/* Live Ticker */}
        <section className="mb-24 lg:mb-32">
          <div className="overflow-hidden rounded-xl border border-slate-800/50 bg-slate-900/30 shadow-xl shadow-black/20">
            <PredictionTicker initial={payload} />
          </div>
        </section>

        {todaysPredictions.length > 0 ? (
          <>
            {/* High Confidence & Upsets */}
            <section className="mb-24 grid gap-6 lg:mb-32 lg:grid-cols-2 lg:gap-8">
              {/* Top Edges */}
              <div className="rounded-xl border border-slate-800/50 bg-slate-900/30 p-6 backdrop-blur-sm lg:p-8">
                <div className="mb-6">
                  <h2 className="text-2xl font-bold text-white">Largest Probability Gaps</h2>
                  <p className="mt-1 text-sm text-slate-400">High-confidence set</p>
                </div>

                <div className="space-y-3">
                  {topEdges.map((game) => {
                    const grade = getPredictionGrade(game.edge);
                    const summary = normalizeSummaryWithGrade(game.summary, grade.label);
                    return (
                      <div
                        key={game.id}
                        className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-4 backdrop-blur-sm"
                      >
                        <div className="flex items-baseline justify-between gap-2">
                          <p className="text-base font-semibold text-white">
                            {game.awayTeam.abbrev} @ {game.homeTeam.abbrev}
                          </p>
                          <div className="flex items-center gap-2">
                            <span className="rounded bg-sky-500/20 px-2 py-0.5 text-xs font-semibold text-sky-400">
                              {grade.label}
                            </span>
                            <span className="text-sm text-slate-400">
                              {(Math.abs(game.edge) * 100).toFixed(1)} pts
                            </span>
                          </div>
                        </div>
                        <p className="mt-1 text-xs text-slate-500">
                          Starts {game.startTimeEt ?? "TBD"}
                        </p>
                        <p className="mt-3 text-sm leading-relaxed text-slate-300">{summary}</p>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Upset Radar */}
              <div className="rounded-xl border border-slate-800/50 bg-slate-900/30 p-6 backdrop-blur-sm lg:p-8">
                <div className="mb-6">
                  <h2 className="text-2xl font-bold text-white">Upset Radar</h2>
                  <p className="mt-1 text-sm text-slate-400">Road teams poised to win</p>
                </div>

                <div className="space-y-3">
                  {upsetRadar.length ? (
                    upsetRadar.map((game) => {
                      const grade = getPredictionGrade(game.edge);
                      const summary = normalizeSummaryWithGrade(game.summary, grade.label);
                      return (
                        <div
                          key={game.id}
                          className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-4 backdrop-blur-sm"
                        >
                          <div className="flex items-center justify-between text-sm">
                            <span className="font-medium text-white">
                              {game.awayTeam.name}
                            </span>
                            <span className="text-sky-400">
                              {numberFmt(game.awayWinProb)}
                            </span>
                          </div>
                          <p className="mt-1 text-xs text-slate-500">
                            {formatTime(game.startTimeUtc)} ET
                          </p>
                          <p className="mt-3 text-sm leading-relaxed text-slate-300">{summary}</p>
                        </div>
                      );
                    })
                  ) : (
                    <div className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-6 text-center backdrop-blur-sm">
                      <p className="text-sm text-slate-400">
                        No &gt;55% road favorites on the board right now.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </section>

            {/* Game-by-Game Table */}
            <section className="mb-24 lg:mb-32">
              <div className="mb-8 text-center lg:mb-10">
                <h2 className="mb-3 text-3xl font-bold text-white lg:text-4xl">Game-by-Game Sheet</h2>
                <p className="text-sm text-slate-400 lg:text-base">
                  Sorted by start time — win %, edge, and confidence score
                </p>
              </div>

              <div className="overflow-hidden rounded-xl border border-slate-800/50 bg-slate-900/30">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="border-b border-slate-800 bg-slate-800/50">
                      <tr className="text-left text-sm text-slate-400">
                        <th className="p-4 font-medium">Matchup</th>
                        <th className="p-4 font-medium">Home %</th>
                        <th className="p-4 font-medium">Road %</th>
                        <th className="p-4 font-medium">Edge</th>
                        <th className="p-4 font-medium">Visual</th>
                        <th className="p-4 font-medium">Grade</th>
                        <th className="p-4 font-medium">Start</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {todaysPredictions
                        .slice()
                        .sort((a, b) => (a.startTimeUtc ?? "").localeCompare(b.startTimeUtc ?? ""))
                        .map((game) => (
                          <tr key={game.id} className="hover:bg-slate-800/30">
                            <td className="p-4 font-medium text-white">
                              {game.awayTeam.abbrev} @ {game.homeTeam.abbrev}
                            </td>
                            <td className="p-4 text-slate-300">{numberFmt(game.homeWinProb)}</td>
                            <td className="p-4 text-slate-300">{numberFmt(game.awayWinProb)}</td>
                            <td className="p-4 text-slate-300">{(game.edge * 100).toFixed(1)} pts</td>
                            <td className="p-4">
                              <EdgeVisual value={game.edge} />
                            </td>
                            <td className="p-4">
                              <span className="rounded bg-sky-500/20 px-2 py-0.5 text-xs font-semibold text-sky-400">
                                {getPredictionGrade(game.edge).label}
                              </span>
                            </td>
                            <td className="p-4 text-sm text-slate-400">{game.startTimeEt ?? "TBD"}</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </section>
          </>
        ) : (
          <div className="rounded-xl border border-slate-800/50 bg-slate-900/30 p-12 text-center backdrop-blur-sm lg:p-16">
            <p className="text-lg text-slate-400">
              No predictions yet. The nightly sync will post the next slate soon.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function SummaryCard({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="rounded-xl border border-slate-800/50 bg-slate-900/30 p-6 backdrop-blur-sm">
      <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{label}</p>
      <p className="mt-3 text-2xl font-bold text-white lg:text-3xl">{value}</p>
      <p className="mt-1.5 text-sm text-slate-500">{detail}</p>
    </div>
  );
}

function EdgeVisual({ value }: { value: number }) {
  const pct = Math.min(Math.abs(value) * 200, 100);
  return (
    <div className="h-2 w-20 rounded-full bg-slate-800">
      <div
        className="h-full rounded-full bg-sky-500"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}
