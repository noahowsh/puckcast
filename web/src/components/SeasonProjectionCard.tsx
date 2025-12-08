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

  // Filter milestones to show meaningful targets:
  // - Only milestones above current value
  // - Exclude 100% probability (already guaranteed)
  // - Extend range until probability drops below 3%
  const filterMilestones = (milestones: Record<number, number>, current: number, projected: number) => {
    const entries = Object.entries(milestones)
      .map(([k, v]) => [parseInt(k), v] as [number, number])
      .filter(([threshold, prob]) => threshold > current && prob < 99.5) // Above current, not guaranteed
      .sort((a, b) => a[0] - b[0]);

    // Include milestones until probability drops below 3%
    const meaningful = entries.filter(([threshold, prob]) => {
      // Always include if above 3% probability
      if (prob >= 3) return true;
      // Include one stretch goal beyond projected
      if (threshold <= projected * 1.3 && prob >= 1) return true;
      return false;
    });

    return Object.fromEntries(meaningful.slice(0, 6));
  };

  const filteredGoalMilestones = filterMilestones(milestoneProbabilities.goals, goals.current, goals.average);
  const filteredAssistMilestones = filterMilestones(milestoneProbabilities.assists, assists.current, assists.average);
  const filteredPointMilestones = filterMilestones(milestoneProbabilities.points, points.current, points.average);

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

      <div style={{ padding: '2rem' }}>
        {/* End of Season Projections Table */}
        <div>
          <h4 className="text-xs font-semibold text-white/60 uppercase tracking-wide mb-4">
            End of Season Projections
          </h4>
          <div className="bg-white/[0.02] rounded-lg overflow-hidden text-xs">
            {/* Header */}
            <div className="grid grid-cols-[80px_1fr_1fr_1fr] border-b border-white/[0.06]">
              <div className="py-3 px-4"></div>
              <div className="py-3 px-2 text-center">
                <span className="text-[10px] font-bold text-white/40 uppercase tracking-wide">Goals</span>
              </div>
              <div className="py-3 px-2 text-center">
                <span className="text-[10px] font-bold text-white/40 uppercase tracking-wide">Assists</span>
              </div>
              <div className="py-3 px-2 text-center">
                <span className="text-[10px] font-bold text-white/40 uppercase tracking-wide">Points</span>
              </div>
            </div>
            {/* Average Row */}
            <div className="grid grid-cols-[80px_1fr_1fr_1fr] border-b border-white/[0.04] bg-white/[0.02]">
              <div className="py-2.5 px-4 text-white font-medium">Average</div>
              <div className="py-2.5 px-2 text-center text-white">{goals.average}</div>
              <div className="py-2.5 px-2 text-center text-white">{assists.average}</div>
              <div className="py-2.5 px-2 text-center text-sky-300 font-bold">{points.average}</div>
            </div>
            {/* Median Row */}
            <div className="grid grid-cols-[80px_1fr_1fr_1fr] border-b border-white/[0.04]">
              <div className="py-2.5 px-4 text-white/60">Median</div>
              <div className="py-2.5 px-2 text-center text-white/70">{goals.median}</div>
              <div className="py-2.5 px-2 text-center text-white/70">{assists.median}</div>
              <div className="py-2.5 px-2 text-center text-white/80">{points.median}</div>
            </div>
            {/* Mode Row */}
            <div className="grid grid-cols-[80px_1fr_1fr_1fr] border-b border-white/[0.04]">
              <div className="py-2.5 px-4 text-white/60">Mode</div>
              <div className="py-2.5 px-2 text-center text-white/70">{goals.mode}</div>
              <div className="py-2.5 px-2 text-center text-white/70">{assists.mode}</div>
              <div className="py-2.5 px-2 text-center text-white/80">{points.mode}</div>
            </div>
            {/* Min Row */}
            <div className="grid grid-cols-[80px_1fr_1fr_1fr] border-b border-white/[0.04]">
              <div className="py-2.5 px-4 text-white/40">Min</div>
              <div className="py-2.5 px-2 text-center text-white/40">{goals.min}</div>
              <div className="py-2.5 px-2 text-center text-white/40">{assists.min}</div>
              <div className="py-2.5 px-2 text-center text-white/50">{points.min}</div>
            </div>
            {/* Max Row */}
            <div className="grid grid-cols-[80px_1fr_1fr_1fr] border-b border-white/[0.04]">
              <div className="py-2.5 px-4 text-white/40">Max</div>
              <div className="py-2.5 px-2 text-center text-white/40">{goals.max}</div>
              <div className="py-2.5 px-2 text-center text-white/40">{assists.max}</div>
              <div className="py-2.5 px-2 text-center text-white/50">{points.max}</div>
            </div>
            {/* Current Row */}
            <div className="grid grid-cols-[80px_1fr_1fr_1fr] bg-white/[0.01]">
              <div className="py-2.5 px-4 text-white/50 italic text-[10px]">Current</div>
              <div className="py-2.5 px-2 text-center text-emerald-400 font-medium">{goals.current}</div>
              <div className="py-2.5 px-2 text-center text-amber-400 font-medium">{assists.current}</div>
              <div className="py-2.5 px-2 text-center text-sky-300 font-bold">{points.current}</div>
            </div>
          </div>
        </div>

        {/* Distribution Chart */}
        <div style={{ marginTop: '2.5rem' }}>
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
        <p style={{ marginTop: '2rem' }} className="text-xs text-white/60 leading-relaxed">{distributionSummary}</p>

        {/* Awards Watch */}
        <div style={{ marginTop: '2.5rem' }}>
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
          <div style={{ marginTop: '2.5rem' }}>
            <h4 className="text-xs font-semibold text-white/60 uppercase tracking-wide mb-4">
              Milestone Tracker
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
        <p style={{ marginTop: '2.5rem', paddingTop: '1.5rem' }} className="text-[10px] text-white/30 leading-relaxed border-t border-white/[0.06]">
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
    <div className="flex items-center gap-4">
      <span className="text-[11px] font-medium text-white/50 w-12 flex-shrink-0">{label}</span>
      <div
        className="flex-1 grid gap-2"
        style={{ gridTemplateColumns: `repeat(${Math.min(entries.length, 6)}, 1fr)` }}
      >
        {entries.map(([milestone, probability]) => (
          <div key={milestone} className={`py-2 rounded text-center ${getColorClass(probability)}`}>
            <p className="text-[10px] font-medium opacity-80">{milestone}</p>
            <p className="text-[11px] font-bold">{probability.toFixed(0)}%</p>
          </div>
        ))}
      </div>
    </div>
  );
}
