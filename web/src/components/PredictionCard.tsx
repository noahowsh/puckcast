import type { Prediction } from "@/types/prediction";
import { getPredictionGrade, normalizeSummaryWithGrade } from "@/lib/prediction";

const percent = (value: number) => Math.round(value * 100);

function ShareButton({ prediction, grade }: { prediction: Prediction; grade: { label: string } }) {
  const homePercent = percent(prediction.homeWinProb);
  const awayPercent = percent(prediction.awayWinProb);
  const favoriteTeam = prediction.modelFavorite === "home" ? prediction.homeTeam : prediction.awayTeam;
  const favoritePercent = prediction.modelFavorite === "home" ? homePercent : awayPercent;

  const tweetText = encodeURIComponent(
    `🏒 ${prediction.awayTeam.abbrev} @ ${prediction.homeTeam.abbrev}\n\n` +
    `📊 PuckCast.ai picks ${favoriteTeam.abbrev} (${favoritePercent}%)\n` +
    `Grade: ${grade.label} | Edge: +${Math.round(Math.abs(prediction.edge) * 100)}%\n\n` +
    `#NHL #HockeyTwitter`
  );
  const tweetUrl = `https://twitter.com/intent/tweet?text=${tweetText}&url=https://puckcast.ai/predictions`;

  const handleCopyLink = async () => {
    const shareText = `${prediction.awayTeam.abbrev} @ ${prediction.homeTeam.abbrev} - PuckCast picks ${favoriteTeam.abbrev} (${favoritePercent}%) Grade ${grade.label}`;
    await navigator.clipboard.writeText(`${shareText} https://puckcast.ai/predictions`);
  };

  return (
    <div className="flex items-center gap-2">
      <a
        href={tweetUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="chip text-[11px] hover:bg-sky-500/20 hover:border-sky-500/40 hover:text-sky-300 transition-colors cursor-pointer"
        title="Share on X"
      >
        𝕏 Share
      </a>
      <button
        onClick={handleCopyLink}
        className="chip text-[11px] hover:bg-sky-500/20 hover:border-sky-500/40 hover:text-sky-300 transition-colors cursor-pointer"
        title="Copy to clipboard"
      >
        📋 Copy
      </button>
    </div>
  );
}

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
    <article className="card group animate-slide-up ice-texture">
      {/* Animated glow effect on hover */}
      <div className="absolute inset-0 bg-gradient-to-br from-sky-500/0 via-sky-500/5 to-cyan-500/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>

      <div className="relative z-10 flex flex-col gap-5">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-5">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-3">
              <span className="chip text-[11px] font-semibold">
                {prediction.startTimeEt ?? "TBD"}
              </span>
              <span
                className={`
                px-3 py-1.5 rounded-full text-[11px] font-bold uppercase tracking-[0.18em]
                ${grade.label === "A" ? "bg-sky-500 text-white shadow-lg shadow-sky-500/30" : ""}
                ${grade.label === "B" ? "bg-sky-500/70 text-white shadow-lg shadow-sky-500/20" : ""}
                ${grade.label === "C" ? "bg-white/10 text-white/80" : ""}
              `}
              >
                Grade {grade.label}
              </span>
            </div>

            <h3 className="text-xl md:text-2xl font-extrabold leading-snug mb-3">
              <span className="text-white/90">{prediction.awayTeam.name}</span>
              <span className="text-sky-400 font-extrabold mx-2">@</span>
              <span className="text-white">{prediction.homeTeam.name}</span>
            </h3>

            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="chip text-[11px]">
                {prediction.awayTeam.abbrev}
              </span>
              <span className="text-white/30">→</span>
              <span className="chip text-[11px]">
                {prediction.homeTeam.abbrev}
              </span>
            </div>
          </div>

          {/* Edge Indicator */}
          <div className="relative flex-shrink-0">
            <div className="text-center px-5 py-4 rounded-xl bg-gradient-to-br from-sky-500/18 to-cyan-500/18 border border-sky-500/30 shadow-lg shadow-sky-500/20 min-w-[130px]">
              <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-sky-300 mb-2">Model Edge</p>
              <p className="text-3xl font-extrabold bg-gradient-to-r from-sky-400 to-cyan-400 bg-clip-text text-transparent leading-tight">
                +{edgePercent}%
              </p>
              <p className="text-[11px] uppercase tracking-[0.18em] mt-2 text-white/70">
                <span className="text-sky-400 font-semibold">{favoriteTeam.abbrev}</span>
                <span className="text-white/30 mx-1">·</span>
                <span className="text-white/60">{prediction.modelFavorite === "home" ? "Home" : "Road"}</span>
              </p>
            </div>
            {/* Pulse glow for high confidence */}
            {grade.label === "A" && (
              <div className="absolute inset-0 bg-sky-500/20 rounded-xl blur-xl animate-pulse-glow"></div>
            )}
          </div>
        </div>

        {/* Probability Bars */}
        <div className="space-y-3">
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
          <div className="flex flex-wrap gap-1.5">
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
        <div className="pt-5 border-t border-white/10 flex flex-col gap-4">
          <div>
            <dt className="stat-label mb-2">Venue</dt>
            <dd className="text-sm text-white/80">{prediction.venue ?? "TBD"}</dd>
          </div>

          <div>
            <dt className="stat-label mb-2">Analysis</dt>
            <dd className="text-sm leading-relaxed text-white/80">{summary}</dd>
            <p className="mt-3 text-xs text-white/50 italic">{grade.description}</p>
          </div>

          {/* Share */}
          <div className="pt-3 border-t border-white/5">
            <ShareButton prediction={prediction} grade={grade} />
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
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-3">
          <span className={`chip text-[11px] font-mono ${
            highlight ? "bg-sky-500/20 text-sky-400 border-sky-500/40 font-bold" : ""
          }`}>
            {abbrev}
          </span>
          <span className={highlight ? "font-bold text-white" : "text-white/70"}>
            {label}
          </span>
        </div>
        <span className={`text-base font-bold tabular-nums ${
          highlight ? "text-sky-400" : "text-white/50"
        }`}>
          {value}%
        </span>
      </div>

      {/* Animated probability bar */}
      <div className="prob-bar">
        <div
          className={`prob-bar-segment ${
            highlight
              ? "bg-gradient-to-r from-sky-500 via-cyan-500 to-sky-400"
              : "bg-gradient-to-r from-white/10 to-white/5"
          }`}
          style={{ width: `${value}%` }}
        />
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
    success: "border-sky-500/60 bg-sky-500/15 text-sky-200",
    warning: "border-white/20 bg-white/10 text-white/80",
    info: "border-sky-500/60 bg-sky-500/15 text-sky-200",
    neutral: "border-white/15 bg-white/8 text-white/80",
  };

  return (
    <div className={`chip ${toneStyles[tone]}`}>
      <span>{label}</span>
      {detail && (
        <>
          <span className="text-white/30">·</span>
          <span className="text-white/60">{detail}</span>
        </>
      )}
    </div>
  );
}
