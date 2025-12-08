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

  // Filter milestones to only show ones not yet achieved (below 100%)
  const filterMilestones = (milestones: Record<number, number>, current: number) => {
    return Object.fromEntries(
      Object.entries(milestones)
        .filter(([threshold, prob]) => parseInt(threshold) > current || prob < 99.9)
        .slice(0, 6) // Show max 6 milestones
    );
  };

  const filteredGoalMilestones = filterMilestones(milestoneProbabilities.goals, goals.current);
  const filteredAssistMilestones = filterMilestones(milestoneProbabilities.assists, assists.current);
  const filteredPointMilestones = filterMilestones(milestoneProbabilities.points, points.current);

  return (
    <div className="relative bg-gradient-to-b from-[#1a1f2e] to-[#151922] border border-white/[0.06] rounded-xl overflow-hidden">
      {/* Header - Full width gradient */}
      <div className="relative border-b border-white/[0.06]">
        <div className="absolute inset-0 bg-gradient-to-r from-sky-500/20 via-sky-500/8 to-transparent" />
        <div className="relative flex items-center justify-between" style={{ padding: '1.25rem 2rem' }}>
          <div>
            <h3 className="text-lg font-bold text-white">Season Projection</h3>
            <p className="text-xs text-white/50 mt-0.5">End of Season Statistical Forecast</p>
          </div>
          <div className="text-right">
            <p className="text-xl font-bold text-sky-300">{gamesRemaining}</p>
            <span className="text-[10px] text-white/40">games remaining</span>
          </div>
        </div>
      </div>

      <div style={{ padding: '2rem' }} className="space-y-8">
        {/* End of Season Projections Table */}
        <div>
          <h4 className="text-xs font-semibold text-white/60 uppercase tracking-wide mb-4">
            End of Season Projections
          </h4>
          <div className="border border-white/[0.06] rounded-lg">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-white/40 text-[10px] uppercase tracking-wider border-b border-white/[0.06]">
                  <th className="text-left py-2.5 px-4"></th>
                  <th className="text-center py-2.5 px-3 w-16">Goals</th>
                  <th className="text-center py-2.5 px-3 w-16">Assists</th>
                  <th className="text-center py-2.5 px-3 w-16">Points</th>
                </tr>
              </thead>
              <tbody className="text-xs">
                <tr className="bg-white/[0.02]">
                  <td className="py-2 px-4 text-white font-medium">Average</td>
                  <td className="text-center py-2 px-3 text-white">{goals.average}</td>
                  <td className="text-center py-2 px-3 text-white">{assists.average}</td>
                  <td className="text-center py-2 px-3 text-sky-300 font-bold">{points.average}</td>
                </tr>
                <tr>
                  <td className="py-2 px-4 text-white/60">Median</td>
                  <td className="text-center py-2 px-3 text-white/70">{goals.median}</td>
                  <td className="text-center py-2 px-3 text-white/70">{assists.median}</td>
                  <td className="text-center py-2 px-3 text-white/80">{points.median}</td>
                </tr>
                <tr>
                  <td className="py-2 px-4 text-white/60">Mode</td>
                  <td className="text-center py-2 px-3 text-white/70">{goals.mode}</td>
                  <td className="text-center py-2 px-3 text-white/70">{assists.mode}</td>
                  <td className="text-center py-2 px-3 text-white/80">{points.mode}</td>
                </tr>
                <tr>
                  <td className="py-2 px-4 text-white/40">Min</td>
                  <td className="text-center py-2 px-3 text-white/40">{goals.min}</td>
                  <td className="text-center py-2 px-3 text-white/40">{assists.min}</td>
                  <td className="text-center py-2 px-3 text-white/50">{points.min}</td>
                </tr>
                <tr>
                  <td className="py-2 px-4 text-white/40">Max</td>
                  <td className="text-center py-2 px-3 text-white/40">{goals.max}</td>
                  <td className="text-center py-2 px-3 text-white/40">{assists.max}</td>
                  <td className="text-center py-2 px-3 text-white/50">{points.max}</td>
                </tr>
                <tr className="border-t border-white/[0.06] bg-white/[0.01]">
                  <td className="py-2 px-4 text-white/50 italic text-[10px]">Current</td>
                  <td className="text-center py-2 px-3 text-emerald-400 font-medium">{goals.current}</td>
                  <td className="text-center py-2 px-3 text-amber-400 font-medium">{assists.current}</td>
                  <td className="text-center py-2 px-3 text-sky-300 font-bold">{points.current}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Distribution Chart */}
        <div className="pt-2">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-xs font-semibold text-white/60 uppercase tracking-wide">
              Projection Distribution
            </h4>
            <select
              value={selectedStat}
              onChange={(e) => setSelectedStat(e.target.value as DistributionStat)}
              className="bg-white/[0.05] border border-white/[0.08] rounded px-2 py-1 text-xs text-white focus:outline-none"
            >
              <option value="points">Points</option>
              <option value="goals">Goals</option>
              <option value="assists">Assists</option>
            </select>
          </div>
          <ProjectionHistogram
            data={histogramData}
            statName={selectedStat}
            average={statProjection.average}
          />
        </div>

        {/* Distribution Summary */}
        <p className="text-xs text-white/60 leading-relaxed">{distributionSummary}</p>

        {/* Awards Watch */}
        <div className="pt-2">
          <h4 className="text-xs font-semibold text-white/60 uppercase tracking-wide mb-4">
            Awards Watch
          </h4>
          <div className="grid grid-cols-3 gap-4">
            <AwardProbability label="Art Ross" sublabel="Most Points" probability={awardProbabilities.mostPoints} />
            <AwardProbability label="Rocket" sublabel="Most Goals" probability={awardProbabilities.mostGoals} />
            <AwardProbability label="Playmaker" sublabel="Most Assists" probability={awardProbabilities.mostAssists} />
          </div>
        </div>

        {/* Milestone Probabilities - Only show if there are milestones to reach */}
        {(Object.keys(filteredGoalMilestones).length > 0 ||
          Object.keys(filteredAssistMilestones).length > 0 ||
          Object.keys(filteredPointMilestones).length > 0) && (
          <div className="pt-2">
            <h4 className="text-xs font-semibold text-white/60 uppercase tracking-wide mb-4">
              Probability of Reaching...
            </h4>
            <div className="space-y-4">
              {Object.keys(filteredGoalMilestones).length > 0 && (
                <MilestoneRow label="Goals" milestones={filteredGoalMilestones} color="emerald" />
              )}
              {Object.keys(filteredAssistMilestones).length > 0 && (
                <MilestoneRow label="Assists" milestones={filteredAssistMilestones} color="amber" />
              )}
              {Object.keys(filteredPointMilestones).length > 0 && (
                <MilestoneRow label="Points" milestones={filteredPointMilestones} color="sky" />
              )}
            </div>
          </div>
        )}

        {/* Footer */}
        <p className="text-[10px] text-white/30 leading-relaxed pt-6 border-t border-white/[0.06]">
          Projections based on current pace extrapolated to 82 games with variance modeling.
        </p>
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
  const { min, max, average } = projection;
  const range = max - min;
  const numBars = 7;
  const bucketSize = Math.ceil(range / numBars);

  const bars: HistogramBar[] = [];

  for (let i = 0; i < numBars; i++) {
    const rangeStart = min + i * bucketSize;
    const rangeEnd = rangeStart + bucketSize;
    const midpoint = (rangeStart + rangeEnd) / 2;

    const sigma = (max - min) / 4;
    const zscore = Math.abs(midpoint - average) / sigma;
    let probability = Math.exp(-0.5 * zscore * zscore);
    probability = probability * 35 + 2;

    bars.push({
      range: `${Math.round(rangeStart)}-${Math.round(rangeEnd)}`,
      rangeStart: Math.round(rangeStart),
      rangeEnd: Math.round(rangeEnd),
      probability: Math.round(probability * 10) / 10,
    });
  }

  const total = bars.reduce((sum, bar) => sum + bar.probability, 0);
  bars.forEach((bar) => {
    bar.probability = Math.round((bar.probability / total) * 100 * 10) / 10;
  });

  return bars;
}

function ProjectionHistogram({
  data,
  statName,
  average,
}: {
  data: HistogramBar[];
  statName: string;
  average: number;
}) {
  const maxProb = Math.max(...data.map((d) => d.probability));

  return (
    <div className="bg-white/[0.02] rounded-lg p-5">
      {/* Bars */}
      <div className="flex items-end justify-between gap-2 h-32 mb-3">
        {data.map((bar, i) => {
          const height = (bar.probability / maxProb) * 100;
          const containsAverage = bar.rangeStart <= average && bar.rangeEnd >= average;

          return (
            <div key={i} className="flex-1 flex flex-col items-center justify-end h-full">
              <span className="text-[9px] text-white/50 mb-1">{bar.probability.toFixed(0)}%</span>
              <div
                className={`w-full rounded-t transition-all ${
                  containsAverage
                    ? "bg-gradient-to-t from-sky-600 to-sky-400"
                    : "bg-gradient-to-t from-white/20 to-white/40"
                }`}
                style={{ height: `${Math.max(height, 8)}%` }}
              />
            </div>
          );
        })}
      </div>
      {/* X-axis labels */}
      <div className="flex justify-between gap-1.5">
        {data.map((bar, i) => (
          <div key={i} className="flex-1 text-center">
            <span className="text-[8px] text-white/40">{bar.range}</span>
          </div>
        ))}
      </div>
      <p className="text-[9px] text-white/40 text-center mt-2">
        Range of Projected {statName.charAt(0).toUpperCase() + statName.slice(1)}
      </p>
    </div>
  );
}

// =============================================================================
// Helper Components
// =============================================================================

function AwardProbability({ label, sublabel, probability }: { label: string; sublabel: string; probability: number }) {
  const getColorClass = (prob: number) => {
    if (prob >= 20) return "text-emerald-400";
    if (prob >= 5) return "text-amber-400";
    if (prob >= 1) return "text-white/70";
    return "text-white/40";
  };

  return (
    <div className="p-4 bg-white/[0.03] rounded-lg text-center">
      <p className={`text-xl font-bold ${getColorClass(probability)}`}>
        {probability.toFixed(1)}%
      </p>
      <p className="text-[11px] text-white/60 font-medium mt-1.5">{label}</p>
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
    .sort((a, b) => a[0] - b[0]);

  const colorClasses = {
    emerald: { high: "bg-emerald-500/30 text-emerald-300", mid: "bg-emerald-500/15 text-emerald-400/70", low: "bg-white/[0.04] text-white/40" },
    amber: { high: "bg-amber-500/30 text-amber-300", mid: "bg-amber-500/15 text-amber-400/70", low: "bg-white/[0.04] text-white/40" },
    sky: { high: "bg-sky-500/30 text-sky-300", mid: "bg-sky-500/15 text-sky-400/70", low: "bg-white/[0.04] text-white/40" },
  };

  const getColorClass = (prob: number) => {
    if (prob >= 70) return colorClasses[color].high;
    if (prob >= 30) return colorClasses[color].mid;
    return colorClasses[color].low;
  };

  return (
    <div className="flex items-center gap-3">
      <span className="text-[11px] font-medium text-white/50 w-14">{label}</span>
      <div className="flex-1 flex gap-2 overflow-x-auto">
        {entries.map(([milestone, probability]) => (
          <div key={milestone} className={`flex-shrink-0 px-2.5 py-1.5 rounded text-center min-w-[48px] ${getColorClass(probability)}`}>
            <p className="text-[10px] font-medium opacity-80">{milestone}</p>
            <p className="text-[11px] font-bold">{probability.toFixed(0)}%</p>
          </div>
        ))}
      </div>
    </div>
  );
}
