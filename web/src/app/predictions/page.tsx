import { getPredictionsPayload, selectCurrentSlate } from "@/lib/data";

const predictions = getPredictionsPayload();
const todaysGames = selectCurrentSlate(predictions.games);

const formatTime = (timeStr: string | null) => {
  if (!timeStr) return "TBD";
  return timeStr;
};

const formatProb = (prob: number) => `${Math.round(prob * 100)}%`;

const getGradeColor = (grade: string) => {
  if (grade.startsWith("A")) return "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
  if (grade.startsWith("B")) return "text-sky-400 bg-sky-500/10 border-sky-500/20";
  return "text-slate-400 bg-slate-500/10 border-slate-500/20";
};

const updatedTimestamp = predictions.generatedAt ? new Date(predictions.generatedAt) : null;
const updatedDisplay = updatedTimestamp
  ? new Intl.DateTimeFormat("en-US", {
      timeZone: "America/New_York",
      hour: "numeric",
      minute: "numeric",
      month: "short",
      day: "numeric",
    }).format(updatedTimestamp)
  : null;

export default function PredictionsPage() {
  // Sort games by edge (highest confidence first)
  const sortedGames = [...todaysGames].sort((a, b) => b.edge - a.edge);

  return (
    <div className="min-h-screen bg-slate-950 px-6 py-12">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-12">
          <h1 className="mb-3 text-4xl font-bold text-white sm:text-5xl">Daily Predictions</h1>
          <div className="flex flex-wrap items-center gap-4 text-lg text-slate-400">
            <span>{sortedGames.length} games</span>
            {updatedDisplay && (
              <>
                <span>•</span>
                <span>Updated {updatedDisplay} ET</span>
              </>
            )}
          </div>
        </div>

        {/* Grade Legend */}
        <div className="mb-8 flex flex-wrap gap-3">
          <div className="inline-flex items-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-3 py-1.5">
            <span className="text-sm font-semibold text-emerald-400">A+/A/A-</span>
            <span className="text-xs text-slate-500">High confidence (10+ pts edge)</span>
          </div>
          <div className="inline-flex items-center gap-2 rounded-lg border border-sky-500/20 bg-sky-500/10 px-3 py-1.5">
            <span className="text-sm font-semibold text-sky-400">B+/B/B-</span>
            <span className="text-xs text-slate-500">Medium confidence (5-10 pts edge)</span>
          </div>
          <div className="inline-flex items-center gap-2 rounded-lg border border-slate-500/20 bg-slate-500/10 px-3 py-1.5">
            <span className="text-sm font-semibold text-slate-400">C+/C</span>
            <span className="text-xs text-slate-500">Low confidence (&lt;5 pts edge)</span>
          </div>
        </div>

        {/* Games List */}
        {sortedGames.length > 0 ? (
          <div className="space-y-4">
            {sortedGames.map((game) => {
              const favorite = game.modelFavorite === "home" ? game.homeTeam : game.awayTeam;
              const underdog = game.modelFavorite === "home" ? game.awayTeam : game.homeTeam;
              const favoriteProb = game.modelFavorite === "home" ? game.homeWinProb : game.awayWinProb;
              const underdogProb = 1 - favoriteProb;

              return (
                <div
                  key={game.id}
                  className="overflow-hidden rounded-lg border border-slate-800/50 bg-slate-900/30 transition-all hover:border-slate-700 hover:bg-slate-900/50"
                >
                  <div className="p-6">
                    {/* Game Header */}
                    <div className="mb-4 flex flex-wrap items-center justify-between gap-4">
                      <div className="flex items-center gap-3">
                        <span className={`inline-flex items-center rounded-md border px-2.5 py-1 text-sm font-semibold ${getGradeColor(game.confidenceGrade)}`}>
                          {game.confidenceGrade}
                        </span>
                        <span className="text-sm font-medium text-slate-500">{formatTime(game.startTimeEt)}</span>
                        {game.venue && (
                          <span className="hidden text-sm text-slate-600 sm:inline">• {game.venue}</span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium uppercase tracking-wide text-slate-500">Edge</span>
                        <span className="text-2xl font-bold text-white">+{Math.round(game.edge * 100)}</span>
                      </div>
                    </div>

                    {/* Matchup */}
                    <div className="grid gap-3 sm:grid-cols-2">
                      {/* Favorite */}
                      <div className="flex items-center justify-between rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-4">
                        <div>
                          <div className="mb-1 text-xs font-medium uppercase tracking-wide text-emerald-400">
                            Model Favorite
                          </div>
                          <div className="text-2xl font-bold text-white">{favorite.name}</div>
                          <div className="mt-1 text-xs text-slate-500">{favorite.abbrev}</div>
                        </div>
                        <div className="text-right">
                          <div className="text-3xl font-bold text-emerald-400">{formatProb(favoriteProb)}</div>
                          <div className="mt-1 text-xs text-slate-500">win prob</div>
                        </div>
                      </div>

                      {/* Underdog */}
                      <div className="flex items-center justify-between rounded-lg border border-slate-700/50 bg-slate-800/30 p-4">
                        <div>
                          <div className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">
                            Underdog
                          </div>
                          <div className="text-2xl font-bold text-white">{underdog.name}</div>
                          <div className="mt-1 text-xs text-slate-500">{underdog.abbrev}</div>
                        </div>
                        <div className="text-right">
                          <div className="text-3xl font-bold text-slate-400">{formatProb(underdogProb)}</div>
                          <div className="mt-1 text-xs text-slate-500">win prob</div>
                        </div>
                      </div>
                    </div>

                    {/* Summary */}
                    {game.summary && (
                      <div className="mt-4 rounded-lg bg-slate-800/30 p-3">
                        <p className="text-sm leading-relaxed text-slate-300">{game.summary}</p>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="rounded-lg border border-slate-800/50 bg-slate-900/30 p-16 text-center">
            <p className="text-xl text-slate-400">No games scheduled today. Check back tomorrow.</p>
          </div>
        )}

        {/* Footer Note */}
        <div className="mt-12 rounded-lg border border-slate-800/50 bg-slate-900/20 p-6">
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">About These Predictions</h3>
          <p className="text-sm leading-relaxed text-slate-500">
            Predictions are generated using a logistic regression model trained on the full 2023-24 NHL season.
            Win probabilities represent the model's confidence based on current standings, rest days, and team performance metrics.
            Confidence grades indicate the edge over a 50/50 baseline.
          </p>
        </div>
      </div>
    </div>
  );
}
