"use client";

import { useState } from "react";
import type { SeasonProjection, StatProjection } from "@/types/player";

// =============================================================================
// Season Projection Card Component
// =============================================================================

interface SeasonProjectionCardProps {
  projection: SeasonProjection;
  playerName: string;
}

type DistributionStat = "points" | "goals" | "assists";

export function SeasonProjectionCard({ projection, playerName }: SeasonProjectionCardProps) {
  const [selectedStat, setSelectedStat] = useState<DistributionStat>("points");
  const { goals, assists, points, awardProbabilities, milestoneProbabilities, distributionSummary, gamesRemaining } = projection;

  // Get the selected stat projection
  const statProjection = selectedStat === "goals" ? goals : selectedStat === "assists" ? assists : points;

  // Generate histogram data from projection
  const histogramData = generateHistogramData(statProjection);

  return (
    <div className="card p-0 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-5 border-b border-white/[0.06] bg-gradient-to-r from-sky-500/10 to-transparent">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold text-white">Season Projection</h3>
            <p className="text-sm text-white/50 mt-1">End of Season Statistical Forecast</p>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-sky-300">{gamesRemaining}</p>
            <span className="text-xs text-white/40">games remaining</span>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-8">
        {/* End of Season Projections Table */}
        <div>
          <h4 className="text-sm font-semibold text-white/70 uppercase tracking-wide mb-4">
            End of Season Projections
          </h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-white/50 text-xs uppercase tracking-wider border-b border-white/[0.06]">
                  <th className="text-left py-3 pr-6"></th>
                  <th className="text-center py-3 px-4 font-semibold">Goals</th>
                  <th className="text-center py-3 px-4 font-semibold">Assists</th>
                  <th className="text-center py-3 px-4 font-semibold">Points</th>
                </tr>
              </thead>
              <tbody>
                <ProjectionRow label="Average" goals={goals.average} assists={assists.average} points={points.average} highlight />
                <ProjectionRow label="Median" goals={goals.median} assists={assists.median} points={points.median} />
                <ProjectionRow label="Mode" goals={goals.mode} assists={assists.mode} points={points.mode} />
                <ProjectionRow label="Min" goals={goals.min} assists={assists.min} points={points.min} dim />
                <ProjectionRow label="Max" goals={goals.max} assists={assists.max} points={points.max} dim />
                <tr className="border-t border-white/[0.08]">
                  <td className="py-3 pr-6 text-white/50 italic">Current</td>
                  <td className="text-center py-3 px-4 text-emerald-400 font-semibold">{goals.current}</td>
                  <td className="text-center py-3 px-4 text-amber-400 font-semibold">{assists.current}</td>
                  <td className="text-center py-3 px-4 text-sky-300 font-bold">{points.current}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Distribution Chart */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-semibold text-white/70 uppercase tracking-wide">
              Projection Distribution
            </h4>
            <div className="flex items-center gap-2">
              <select
                value={selectedStat}
                onChange={(e) => setSelectedStat(e.target.value as DistributionStat)}
                className="bg-white/[0.05] border border-white/[0.1] rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-sky-400/50"
              >
                <option value="points">Points</option>
                <option value="goals">Goals</option>
                <option value="assists">Assists</option>
              </select>
            </div>
          </div>
          <ProjectionHistogram
            data={histogramData}
            statName={selectedStat}
            current={statProjection.current}
            average={statProjection.average}
          />
          <p className="text-xs text-white/40 mt-3 text-center">
            Probability of finishing season in each range
          </p>
        </div>

        {/* Distribution Summary */}
        <div className="p-5 bg-white/[0.02] rounded-xl border border-white/[0.06]">
          <p className="text-sm text-white/70 leading-relaxed">{distributionSummary}</p>
        </div>

        {/* Awards Watch */}
        <div>
          <h4 className="text-sm font-semibold text-white/70 uppercase tracking-wide mb-4">
            Awards Watch
          </h4>
          <div className="grid grid-cols-3 gap-4">
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
          <h4 className="text-sm font-semibold text-white/70 uppercase tracking-wide mb-4">
            Probability of Reaching...
          </h4>
          <div className="space-y-5">
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
        <div className="pt-5 border-t border-white/[0.06]">
          <p className="text-xs text-white/30 leading-relaxed">
            Projections are based on current season pace and historical patterns. Uses per-game rates extrapolated to 82 games with variance modeling for range estimates.
          </p>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Histogram Component
// =============================================================================

interface HistogramBar {
  range: string;
  rangeStart: number;
  rangeEnd: number;
  probability: number;
}

function generateHistogramData(projection: StatProjection): HistogramBar[] {
  const { min, max, average, median } = projection;
  const range = max - min;
  const numBars = 8;
  const bucketSize = Math.ceil(range / numBars);

  const bars: HistogramBar[] = [];

  for (let i = 0; i < numBars; i++) {
    const rangeStart = min + i * bucketSize;
    const rangeEnd = rangeStart + bucketSize;
    const midpoint = (rangeStart + rangeEnd) / 2;

    // Calculate probability using a normal distribution approximation
    const sigma = (max - min) / 4; // Standard deviation approximation
    const zscore = Math.abs(midpoint - average) / sigma;
    let probability = Math.exp(-0.5 * zscore * zscore);

    // Normalize and scale
    probability = probability * 35 + 2;

    bars.push({
      range: `${Math.round(rangeStart)}-${Math.round(rangeEnd)}`,
      rangeStart: Math.round(rangeStart),
      rangeEnd: Math.round(rangeEnd),
      probability: Math.round(probability * 10) / 10,
    });
  }

  // Normalize probabilities to sum to ~100
  const total = bars.reduce((sum, bar) => sum + bar.probability, 0);
  bars.forEach((bar) => {
    bar.probability = Math.round((bar.probability / total) * 100 * 10) / 10;
  });

  return bars;
}

function ProjectionHistogram({
  data,
  statName,
  current,
  average,
}: {
  data: HistogramBar[];
  statName: string;
  current: number;
  average: number;
}) {
  const maxProb = Math.max(...data.map((d) => d.probability));

  return (
    <div className="bg-white/[0.02] rounded-xl p-5 border border-white/[0.06]">
      {/* Y-axis label */}
      <div className="flex">
        <div className="flex flex-col justify-between text-[10px] text-white/40 pr-3 py-1" style={{ writingMode: "vertical-rl", transform: "rotate(180deg)" }}>
          <span>Probability of Finishing Season In Range</span>
        </div>

        {/* Chart area */}
        <div className="flex-1">
          {/* Y-axis values and bars */}
          <div className="relative">
            {/* Grid lines */}
            <div className="absolute inset-0 flex flex-col justify-between pointer-events-none">
              {[40, 30, 20, 10, 0].map((val) => (
                <div key={val} className="flex items-center">
                  <span className="text-[10px] text-white/30 w-8 text-right pr-2">{val}%</span>
                  <div className="flex-1 border-t border-white/[0.04]" />
                </div>
              ))}
            </div>

            {/* Bars */}
            <div className="flex items-end justify-between gap-2 h-48 pl-10 relative z-10">
              {data.map((bar, i) => {
                const height = (bar.probability / 40) * 100;
                const isHighest = bar.probability === maxProb;
                const containsAverage = bar.rangeStart <= average && bar.rangeEnd >= average;

                return (
                  <div key={i} className="flex-1 flex flex-col items-center justify-end h-full">
                    <div
                      className={`w-full rounded-t-sm transition-all duration-300 ${
                        containsAverage
                          ? "bg-gradient-to-t from-sky-600 to-sky-400"
                          : isHighest
                            ? "bg-gradient-to-t from-white/40 to-white/60"
                            : "bg-gradient-to-t from-white/20 to-white/35"
                      }`}
                      style={{ height: `${Math.max(height, 2)}%` }}
                      title={`${bar.range}: ${bar.probability}%`}
                    />
                  </div>
                );
              })}
            </div>
          </div>

          {/* X-axis labels */}
          <div className="flex justify-between gap-2 mt-3 pl-10">
            {data.map((bar, i) => (
              <div key={i} className="flex-1 text-center">
                <span className="text-[10px] text-white/40 transform -rotate-45 inline-block">
                  {bar.range}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* X-axis title */}
      <div className="text-center mt-4">
        <span className="text-xs text-white/50">Range of Projected {statName.charAt(0).toUpperCase() + statName.slice(1)}</span>
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
  const pointsClass = dim ? "text-white/40" : highlight ? "text-sky-300 font-bold text-lg" : "text-white/80";

  return (
    <tr className={highlight ? "bg-white/[0.02]" : ""}>
      <td className={`py-3 pr-6 ${textClass}`}>{label}</td>
      <td className={`text-center py-3 px-4 ${textClass}`}>{goals}</td>
      <td className={`text-center py-3 px-4 ${textClass}`}>{assists}</td>
      <td className={`text-center py-3 px-4 ${pointsClass}`}>{points}</td>
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
    <div className="p-4 bg-white/[0.03] rounded-xl text-center border border-white/[0.04]">
      <p className={`text-2xl font-bold ${getColorClass(probability)}`}>
        {probability.toFixed(1)}%
      </p>
      <p className="text-sm text-white/70 font-medium mt-2">{label}</p>
      <p className="text-xs text-white/40 mt-0.5">{sublabel}</p>
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
      high: "bg-emerald-500/30 text-emerald-300 border-emerald-500/20",
      mid: "bg-emerald-500/15 text-emerald-400/80 border-emerald-500/10",
      low: "bg-white/[0.04] text-white/40 border-white/[0.04]",
    },
    amber: {
      high: "bg-amber-500/30 text-amber-300 border-amber-500/20",
      mid: "bg-amber-500/15 text-amber-400/80 border-amber-500/10",
      low: "bg-white/[0.04] text-white/40 border-white/[0.04]",
    },
    sky: {
      high: "bg-sky-500/30 text-sky-300 border-sky-500/20",
      mid: "bg-sky-500/15 text-sky-400/80 border-sky-500/10",
      low: "bg-white/[0.04] text-white/40 border-white/[0.04]",
    },
  };

  const getColorClass = (prob: number) => {
    if (prob >= 70) return colorClasses[color].high;
    if (prob >= 30) return colorClasses[color].mid;
    return colorClasses[color].low;
  };

  return (
    <div>
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-white/60 w-16">{label}</span>
        <div className="flex-1 flex gap-2 overflow-x-auto pb-1">
          {entries.map(([milestone, probability]) => (
            <div
              key={milestone}
              className={`flex-shrink-0 px-3 py-2 rounded-lg text-center min-w-[60px] border ${getColorClass(probability)}`}
            >
              <p className="text-xs font-medium opacity-80">{milestone}</p>
              <p className="text-sm font-bold">{probability.toFixed(0)}%</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
