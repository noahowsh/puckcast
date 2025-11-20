import type { Prediction } from "@/types/prediction";
import { getPredictionGrade, normalizeSummaryWithGrade } from "@/lib/prediction";

const percent = (value: number) => Math.round(value * 100);

export function PredictionCard({ prediction }: { prediction: Prediction }) {
  const homePercent = percent(prediction.homeWinProb);
  const awayPercent = percent(prediction.awayWinProb);
  const edgePercent = Math.round(Math.abs(prediction.edge) * 100);
  const favoriteTeam = prediction.modelFavorite === "home" ? prediction.homeTeam : prediction.awayTeam;
  const grade = getPredictionGrade(prediction.edge);
  const summary = normalizeSummaryWithGrade(prediction.summary, grade.label);
  const dayOfInfo = prediction.dayOfInfo;
  const homeGoalie = dayOfInfo?.homeGoalie;
  const awayGoalie = dayOfInfo?.awayGoalie;
  const homeInjuryCount = dayOfInfo?.homeInjuryCount ?? 0;
  const awayInjuryCount = dayOfInfo?.awayInjuryCount ?? 0;
  const totalInjuries = homeInjuryCount + awayInjuryCount;

  return (
    <article className="glass-card group relative p-6 md:p-8 animate-slide-up ice-texture overflow-hidden">
      {/* Animated glow effect on hover */}
      <div className="absolute inset-0 bg-gradient-to-br from-sky-500/0 via-sky-500/5 to-cyan-500/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>

      <div className="relative z-10">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 md:gap-6">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-xs font-bold uppercase tracking-widest text-sky-400">
                {prediction.startTimeEt ?? "TBD"}
              </span>
              <span className={`
                px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider
                ${grade.label === "A" ? "bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg shadow-amber-500/30" : ""}
                ${grade.label === "B" ? "bg-gradient-to-r from-sky-500 to-cyan-500 text-white shadow-lg shadow-sky-500/30" : ""}
                ${grade.label === "C" ? "bg-white/10 text-slate-300" : ""}
              `}>
                Grade {grade.label}
              </span>
            </div>

            <h3 className="text-xl md:text-2xl lg:text-3xl font-bold leading-tight mb-2">
              <span className="text-slate-300">{prediction.awayTeam.name}</span>
              <span className="text-sky-400 font-extrabold mx-2">@</span>
              <span className="text-white">{prediction.homeTeam.name}</span>
            </h3>

            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="px-2 py-1 rounded bg-white/5 text-slate-400 font-mono text-xs">
                {prediction.awayTeam.abbrev}
              </span>
              <span className="text-slate-600">→</span>
              <span className="px-2 py-1 rounded bg-white/5 text-slate-400 font-mono text-xs">
                {prediction.homeTeam.abbrev}
              </span>
            </div>
          </div>

          {/* Edge Indicator */}
          <div className="relative">
            <div className="text-center p-4 rounded-xl bg-gradient-to-br from-sky-500/20 to-cyan-500/20 border border-sky-500/30 shadow-lg shadow-sky-500/20 min-w-[140px]">
              <p className="text-xs font-bold uppercase tracking-widest text-sky-400 mb-1">Model Edge</p>
              <p className="text-3xl md:text-4xl font-extrabold bg-gradient-to-r from-sky-400 to-cyan-400 bg-clip-text text-transparent">
                +{edgePercent}%
              </p>
              <p className="text-xs uppercase tracking-wider mt-1">
                <span className="text-amber-400">{favoriteTeam.abbrev}</span>
                <span className="text-slate-500 mx-1">·</span>
                <span className="text-slate-400">{prediction.modelFavorite === "home" ? "Home" : "Road"}</span>
              </p>
            </div>
            {/* Pulse glow for high confidence */}
            {grade.label === "A" && (
              <div className="absolute inset-0 bg-amber-500/20 rounded-xl blur-xl animate-pulse-glow"></div>
            )}
          </div>
        </div>

        {/* Probability Bars */}
        <div className="mt-8 space-y-4">
          <ProbabilityBar
            label={prediction.homeTeam.name}
            abbrev={prediction.homeTeam.abbrev}
            value={homePercent}
            highlight={prediction.modelFavorite === "home"}
          />
          <ProbabilityBar
            label={prediction.awayTeam.name}
            abbrev={prediction.awayTeam.abbrev}
            value={awayPercent}
            highlight={prediction.modelFavorite === "away"}
          />
        </div>

        {/* Day-of-game info */}
        {dayOfInfo && (
          <div className="mt-6 flex flex-wrap gap-2">
            {homeGoalie && (
              <StatusChip
                label={`🥅 ${homeGoalie.goalieName ?? "Goalie"}`}
                detail={homeGoalie.confirmedStart ? "Starting" : "Projected"}
                tone={homeGoalie.confirmedStart ? "success" : "info"}
              />
            )}
            {awayGoalie && (
              <StatusChip
                label={`🥅 ${awayGoalie.goalieName ?? "Goalie"}`}
                detail={awayGoalie.confirmedStart ? "Starting" : "Projected"}
                tone={awayGoalie.confirmedStart ? "success" : "info"}
              />
            )}
            {totalInjuries > 0 && (
              <StatusChip
                label={`⚠️ ${totalInjuries} Injuries`}
                detail={`${homeInjuryCount}H / ${awayInjuryCount}A`}
                tone="warning"
              />
            )}
          </div>
        )}

        {/* Details */}
        <div className="mt-8 pt-6 border-t border-white/10 space-y-4">
          <div>
            <dt className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-1">Venue</dt>
            <dd className="text-base text-slate-300">{prediction.venue ?? "TBD"}</dd>
          </div>

          <div>
            <dt className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Analysis</dt>
            <dd className="text-base leading-relaxed text-slate-200">{summary}</dd>
            <p className="mt-3 text-xs text-slate-500 italic">{grade.description}</p>
          </div>
        </div>
      </div>
    </article>
  );
}

function ProbabilityBar({
  label,
  abbrev,
  value,
  highlight,
}: {
  label: string;
  abbrev: string;
  value: number;
  highlight: boolean;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <span className={`font-mono text-xs px-2 py-0.5 rounded ${
            highlight ? "bg-sky-500/20 text-sky-400 font-bold" : "bg-white/5 text-slate-400"
          }`}>
            {abbrev}
          </span>
          <span className={highlight ? "font-bold text-white" : "text-slate-400"}>
            {label}
          </span>
        </div>
        <span className={`text-lg font-bold tabular-nums ${
          highlight ? "text-sky-400 neon-text" : "text-slate-500"
        }`}>
          {value}%
        </span>
      </div>

      {/* Animated probability bar */}
      <div className="relative h-3 w-full overflow-hidden rounded-full bg-white/5 border border-white/10">
        <div
          className={`
            h-full rounded-full transition-all duration-1000 ease-out
            ${highlight
              ? "bg-gradient-to-r from-sky-500 via-cyan-500 to-sky-400 shadow-lg shadow-sky-500/50"
              : "bg-gradient-to-r from-slate-600 to-slate-700"
            }
          `}
          style={{ width: `${value}%` }}
        >
          {/* Inner shine effect */}
          <div className="h-full w-full bg-gradient-to-b from-white/20 to-transparent"></div>
        </div>
      </div>
    </div>
  );
}

type StatusTone = "success" | "warning" | "info" | "neutral";

function StatusChip({
  label,
  detail,
  tone = "neutral",
}: {
  label: string;
  detail?: string;
  tone?: StatusTone;
}) {
  const toneStyles: Record<StatusTone, string> = {
    success: "border-emerald-500/50 bg-emerald-500/10 text-emerald-300 shadow-emerald-500/20",
    warning: "border-amber-500/50 bg-amber-500/10 text-amber-300 shadow-amber-500/20",
    info: "border-sky-500/50 bg-sky-500/10 text-sky-300 shadow-sky-500/20",
    neutral: "border-white/20 bg-white/5 text-slate-300",
  };

  return (
    <div className={`inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-xs font-semibold shadow-lg ${toneStyles[tone]}`}>
      <span>{label}</span>
      {detail && (
        <>
          <span className="text-white/30">·</span>
          <span className="text-white/60 text-xs">{detail}</span>
        </>
      )}
    </div>
  );
}
