"use client";

import type { SeasonProjection, StatProjection } from "@/types/player";

// =============================================================================
// Season Projection Card Component
// =============================================================================

interface SeasonProjectionCardProps {
  projection: SeasonProjection;
  playerName: string;
}

export function SeasonProjectionCard({ projection, playerName }: SeasonProjectionCardProps) {
  const { goals, assists, points, awardProbabilities, milestoneProbabilities, distributionSummary, gamesRemaining } = projection;

  return (
    <div className="card p-0 overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-white/[0.06] bg-gradient-to-r from-sky-500/10 to-transparent">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-white">Season Projection</h3>
            <p className="text-xs text-white/50 mt-0.5">End of Season Statistical Forecast</p>
          </div>
          <div className="text-right">
            <span className="text-xs text-white/40">{gamesRemaining} games remaining</span>
          </div>
        </div>
      </div>

      <div className="p-5 space-y-6">
        {/* End of Season Projections Table */}
        <div>
          <h4 className="text-sm font-semibold text-white/70 uppercase tracking-wide mb-3">
            End of Season Projections
          </h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-white/50 text-xs uppercase tracking-wider">
                  <th className="text-left py-2 pr-4"></th>
                  <th className="text-center py-2 px-3">Goals</th>
                  <th className="text-center py-2 px-3">Assists</th>
                  <th className="text-center py-2 px-3">Points</th>
                </tr>
              </thead>
              <tbody>
                <ProjectionRow label="Average" goals={goals.average} assists={assists.average} points={points.average} highlight />
                <ProjectionRow label="Median" goals={goals.median} assists={assists.median} points={points.median} />
                <ProjectionRow label="Mode" goals={goals.mode} assists={assists.mode} points={points.mode} />
                <ProjectionRow label="Min" goals={goals.min} assists={assists.min} points={points.min} dim />
                <ProjectionRow label="Max" goals={goals.max} assists={assists.max} points={points.max} dim />
                <tr className="border-t border-white/[0.08]">
                  <td className="py-2 pr-4 text-white/50 italic text-xs">Current</td>
                  <td className="text-center py-2 px-3 text-white/60">{goals.current}</td>
                  <td className="text-center py-2 px-3 text-white/60">{assists.current}</td>
                  <td className="text-center py-2 px-3 text-sky-300/70">{points.current}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Distribution Summary */}
        <div className="p-4 bg-white/[0.02] rounded-lg border border-white/[0.04]">
          <p className="text-sm text-white/70 leading-relaxed">{distributionSummary}</p>
        </div>

        {/* Awards Watch */}
        <div>
          <h4 className="text-sm font-semibold text-white/70 uppercase tracking-wide mb-3">
            Awards Watch
          </h4>
          <div className="grid grid-cols-3 gap-3">
            <AwardProbability
              label="Art Ross"
              sublabel="Most Points"
              probability={awardProbabilities.mostPoints}
            />
            <AwardProbability
              label="Rocket"
              sublabel="Most Goals"
              probability={awardProbabilities.mostGoals}
            />
            <AwardProbability
              label="Playmaker"
              sublabel="Most Assists"
              probability={awardProbabilities.mostAssists}
            />
          </div>
        </div>

        {/* Milestone Probabilities */}
        <div>
          <h4 className="text-sm font-semibold text-white/70 uppercase tracking-wide mb-3">
            Probability of Reaching...
          </h4>
          <div className="space-y-4">
            <MilestoneRow
              label="Goals"
              milestones={milestoneProbabilities.goals}
              color="emerald"
            />
            <MilestoneRow
              label="Assists"
              milestones={milestoneProbabilities.assists}
              color="amber"
            />
            <MilestoneRow
              label="Points"
              milestones={milestoneProbabilities.points}
              color="sky"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-white/[0.06]">
          <p className="text-[10px] text-white/30 leading-relaxed">
            Projections are based on current season pace and historical patterns. Uses per-game rates extrapolated to 82 games with variance modeling for range estimates.
          </p>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Helper Components
// =============================================================================

function ProjectionRow({
  label,
  goals,
  assists,
  points,
  highlight = false,
  dim = false,
}: {
  label: string;
  goals: number;
  assists: number;
  points: number;
  highlight?: boolean;
  dim?: boolean;
}) {
  const textClass = dim ? "text-white/40" : highlight ? "text-white font-semibold" : "text-white/70";
  const pointsClass = dim ? "text-white/40" : highlight ? "text-sky-300 font-bold" : "text-white/80";

  return (
    <tr className={highlight ? "bg-white/[0.02]" : ""}>
      <td className={`py-2 pr-4 ${textClass}`}>{label}</td>
      <td className={`text-center py-2 px-3 ${textClass}`}>{goals}</td>
      <td className={`text-center py-2 px-3 ${textClass}`}>{assists}</td>
      <td className={`text-center py-2 px-3 ${pointsClass}`}>{points}</td>
    </tr>
  );
}

function AwardProbability({
  label,
  sublabel,
  probability,
}: {
  label: string;
  sublabel: string;
  probability: number;
}) {
  const getColorClass = (prob: number) => {
    if (prob >= 20) return "text-emerald-400";
    if (prob >= 5) return "text-amber-400";
    if (prob >= 1) return "text-white/70";
    return "text-white/40";
  };

  return (
    <div className="p-3 bg-white/[0.03] rounded-lg text-center">
      <p className={`text-xl font-bold ${getColorClass(probability)}`}>
        {probability.toFixed(1)}%
      </p>
      <p className="text-xs text-white/70 font-medium mt-1">{label}</p>
      <p className="text-[10px] text-white/40">{sublabel}</p>
    </div>
  );
}

function MilestoneRow({
  label,
  milestones,
  color,
}: {
  label: string;
  milestones: Record<number, number>;
  color: "emerald" | "amber" | "sky";
}) {
  const entries = Object.entries(milestones)
    .map(([k, v]) => [parseInt(k), v] as [number, number])
    .sort((a, b) => a[0] - b[0])
    .slice(0, 8); // Show up to 8 milestones

  const colorClasses = {
    emerald: {
      high: "bg-emerald-500/30 text-emerald-300",
      mid: "bg-emerald-500/15 text-emerald-400/80",
      low: "bg-white/[0.04] text-white/40",
    },
    amber: {
      high: "bg-amber-500/30 text-amber-300",
      mid: "bg-amber-500/15 text-amber-400/80",
      low: "bg-white/[0.04] text-white/40",
    },
    sky: {
      high: "bg-sky-500/30 text-sky-300",
      mid: "bg-sky-500/15 text-sky-400/80",
      low: "bg-white/[0.04] text-white/40",
    },
  };

  const getColorClass = (prob: number) => {
    if (prob >= 70) return colorClasses[color].high;
    if (prob >= 30) return colorClasses[color].mid;
    return colorClasses[color].low;
  };

  return (
    <div>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-medium text-white/60 w-14">{label}</span>
        <div className="flex-1 flex gap-1.5 overflow-x-auto pb-1">
          {entries.map(([milestone, probability]) => (
            <div
              key={milestone}
              className={`flex-shrink-0 px-2 py-1.5 rounded text-center min-w-[52px] ${getColorClass(probability)}`}
            >
              <p className="text-[10px] font-medium">{milestone}</p>
              <p className="text-xs font-bold">{probability.toFixed(0)}%</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
