"use client";

import type { GoalieSeasonStats } from "@/types/player";

// =============================================================================
// Goalie Performance Card Component (GSAx-Style Analytics)
// =============================================================================

interface GoaliePerformanceCardProps {
  stats: GoalieSeasonStats;
  playerName: string;
  allGoalies: { bio: { playerId: number }; stats: GoalieSeasonStats }[];
  pulseData?: {
    rollingGsa: number;
    seasonGsa: number;
    trend: string;
  } | null;
}

export function GoaliePerformanceCard({ stats, playerName, allGoalies, pulseData }: GoaliePerformanceCardProps) {
  // Calculate league percentiles
  const qualifiedGoalies = allGoalies.filter(g => g.stats.gamesPlayed >= 10);

  const savePctPercentile = calculatePercentile(
    stats.savePct,
    qualifiedGoalies.map(g => g.stats.savePct)
  );

  const gaaPercentile = calculatePercentile(
    stats.goalsAgainstAverage,
    qualifiedGoalies.map(g => g.stats.goalsAgainstAverage),
    true // Lower is better
  );

  const winsPercentile = calculatePercentile(
    stats.wins,
    allGoalies.map(g => g.stats.wins)
  );

  // Calculate GSAx from pulse data or estimate
  const seasonGSAx = pulseData?.seasonGsa ?? estimateGSAx(stats);
  const gsaxPercentile = calculateGSAxPercentile(seasonGSAx);

  // Get tier for overall rating
  const overallPercentile = Math.round((savePctPercentile + gaaPercentile + gsaxPercentile) / 3);
  const overallTier = getTier(overallPercentile);

  // Calculate consistency (based on variance in performance)
  const consistencyRating = getConsistencyRating(stats);

  return (
    <div className="relative bg-gradient-to-b from-[#1a1f2e] to-[#151922] border border-white/[0.06] rounded-xl overflow-hidden">
      {/* Header - Full width gradient */}
      <div className="relative border-b border-white/[0.06]">
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/20 via-cyan-500/8 to-transparent" />
        <div className="relative flex items-center justify-between px-6 py-5">
          <div>
            <h3 className="text-lg font-bold text-white">Goalie Performance</h3>
            <p className="text-xs text-white/50 mt-0.5">Advanced Goaltending Analytics</p>
          </div>
          <div className="flex items-center gap-5 text-right">
            <div>
              <span className="text-[10px] text-white/40 block">GP</span>
              <p className="text-sm font-semibold text-white">{stats.gamesPlayed}</p>
            </div>
            <div>
              <span className="text-[10px] text-white/40 block">GS</span>
              <p className="text-sm font-semibold text-white">{stats.gamesStarted}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="p-8 space-y-6">
        {/* Overall Rating + Key Metrics */}
        <div className="flex gap-6">
          {/* Overall Rating Circle */}
          <div className="flex flex-col items-center justify-center w-28 flex-shrink-0">
            <OverallRating percentile={overallPercentile} tier={overallTier} />
          </div>

          {/* Key Performance Metrics */}
          <div className="flex-1 grid grid-cols-2 gap-4">
            <MetricBox
              label="Save %"
              value={formatSavePct(stats.savePct)}
              percentile={savePctPercentile}
            />
            <MetricBox
              label="GAA"
              value={stats.goalsAgainstAverage.toFixed(2)}
              percentile={gaaPercentile}
            />
            <MetricBox
              label="GSAx"
              value={seasonGSAx > 0 ? `+${seasonGSAx.toFixed(1)}` : seasonGSAx.toFixed(1)}
              percentile={gsaxPercentile}
              highlight={seasonGSAx > 5 || seasonGSAx < -5}
            />
            <MetricBox
              label="Wins"
              value={stats.wins.toString()}
              percentile={winsPercentile}
            />
          </div>
        </div>

        {/* Performance Breakdown */}
        <div>
          <h4 className="text-xs font-semibold text-white/60 uppercase tracking-wide mb-4">
            Performance Breakdown
          </h4>
          <div className="space-y-3">
            <PercentileBar label="Save Percentage" percentile={savePctPercentile} />
            <PercentileBar label="Goals Against Avg" percentile={gaaPercentile} />
            <PercentileBar label="Goals Saved Above Expected" percentile={gsaxPercentile} />
            <PercentileBar label="Win Contribution" percentile={winsPercentile} />
          </div>
        </div>

        {/* Workload & Consistency */}
        <div>
          <h4 className="text-xs font-semibold text-white/60 uppercase tracking-wide mb-4">
            Workload & Consistency
          </h4>
          <div className="grid grid-cols-3 gap-3">
            <WorkloadBox
              label="Shots Faced"
              value={stats.shotsAgainst.toString()}
              sublabel={`${(stats.shotsAgainst / stats.gamesPlayed).toFixed(1)}/game`}
            />
            <WorkloadBox
              label="Consistency"
              value={consistencyRating.label}
              sublabel={consistencyRating.description}
              tier={consistencyRating.tier}
            />
            <WorkloadBox
              label="Shutouts"
              value={stats.shutouts.toString()}
              sublabel={`${((stats.shutouts / stats.gamesStarted) * 100).toFixed(0)}% of starts`}
            />
          </div>
        </div>

        {/* Performance Summary */}
        <p className="text-xs text-white/60 leading-relaxed">
          {generatePerformanceSummary(playerName, stats, overallPercentile, seasonGSAx)}
        </p>

        {/* Legend */}
        <div className="flex items-center justify-center gap-2 pt-5 border-t border-white/[0.06]">
          <LegendItem color="bg-rose-500/50" label="Poor" />
          <LegendItem color="bg-amber-500/40" label="Below Avg" />
          <LegendItem color="bg-white/25" label="Average" />
          <LegendItem color="bg-emerald-500/50" label="Above Avg" />
          <LegendItem color="bg-sky-500/60" label="Elite" />
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Helper Components
// =============================================================================

type Tier = "elite" | "above-average" | "average" | "below-average" | "poor";

function OverallRating({ percentile, tier }: { percentile: number; tier: Tier }) {
  const tierColors = {
    elite: { ring: "ring-sky-400/40", text: "text-sky-300", bg: "bg-sky-500/10", label: "Elite" },
    "above-average": { ring: "ring-emerald-400/40", text: "text-emerald-400", bg: "bg-emerald-500/10", label: "Above Avg" },
    average: { ring: "ring-white/20", text: "text-white/70", bg: "bg-white/[0.04]", label: "Average" },
    "below-average": { ring: "ring-amber-400/40", text: "text-amber-400", bg: "bg-amber-500/10", label: "Below Avg" },
    poor: { ring: "ring-rose-400/40", text: "text-rose-400", bg: "bg-rose-500/10", label: "Poor" },
  };

  const colors = tierColors[tier];

  return (
    <div className="flex flex-col items-center gap-2">
      <div className={`w-24 h-24 rounded-full ${colors.bg} ring-2 ${colors.ring} flex flex-col items-center justify-center`}>
        <span className={`text-3xl font-black ${colors.text}`}>{percentile}</span>
        <span className="text-[10px] text-white/40 -mt-0.5">percentile</span>
      </div>
      <div className="text-center">
        <p className={`text-xs font-semibold ${colors.text}`}>{colors.label}</p>
        <p className="text-[10px] text-white/40">Overall</p>
      </div>
    </div>
  );
}

function MetricBox({
  label,
  value,
  percentile,
  highlight = false
}: {
  label: string;
  value: string;
  percentile: number;
  highlight?: boolean;
}) {
  const tier = getTier(percentile);
  const tierColors = {
    elite: "text-sky-300",
    "above-average": "text-emerald-400",
    average: "text-white/70",
    "below-average": "text-amber-400",
    poor: "text-rose-400",
  };

  return (
    <div className="p-3 bg-white/[0.03] rounded-lg">
      <div className="flex items-baseline justify-between mb-1">
        <span className="text-[10px] text-white/50 uppercase">{label}</span>
        <span className="text-[10px] text-white/40">{percentile}%ile</span>
      </div>
      <p className={`text-xl font-bold ${tierColors[tier]} ${highlight ? "animate-pulse" : ""}`}>
        {value}
      </p>
    </div>
  );
}

function PercentileBar({ label, percentile }: { label: string; percentile: number }) {
  const tier = getTier(percentile);
  const barColors = {
    elite: "bg-sky-400",
    "above-average": "bg-emerald-400",
    average: "bg-white/40",
    "below-average": "bg-amber-400",
    poor: "bg-rose-400",
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-1.5">
        <span className="text-[10px] text-white/60">{label}</span>
        <span className="text-xs font-semibold text-white/80">{percentile}%</span>
      </div>
      <div className="h-2 bg-white/[0.06] rounded-full overflow-hidden">
        <div
          className={`h-full ${barColors[tier]} rounded-full transition-all`}
          style={{ width: `${percentile}%` }}
        />
      </div>
    </div>
  );
}

function WorkloadBox({
  label,
  value,
  sublabel,
  tier
}: {
  label: string;
  value: string;
  sublabel: string;
  tier?: Tier;
}) {
  const tierColors = tier ? {
    elite: "text-sky-300",
    "above-average": "text-emerald-400",
    average: "text-white",
    "below-average": "text-amber-400",
    poor: "text-rose-400",
  } : { average: "text-white" };

  return (
    <div className="p-3 bg-white/[0.03] rounded-lg text-center">
      <p className={`text-lg font-bold ${tierColors[tier || "average"]}`}>{value}</p>
      <p className="text-[10px] text-white/50 mt-0.5">{label}</p>
      <p className="text-[9px] text-white/30 mt-0.5">{sublabel}</p>
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1">
      <div className={`w-2.5 h-2.5 rounded ${color}`} />
      <span className="text-[9px] text-white/40">{label}</span>
    </div>
  );
}

// =============================================================================
// Helper Functions
// =============================================================================

function calculatePercentile(value: number, allValues: number[], lowerIsBetter = false): number {
  if (allValues.length === 0) return 50;

  const sorted = [...allValues].sort((a, b) => a - b);
  const index = sorted.findIndex(v => v >= value);

  let percentile = (index / sorted.length) * 100;

  if (lowerIsBetter) {
    percentile = 100 - percentile;
  } else {
    percentile = 100 - ((sorted.length - index) / sorted.length) * 100;
  }

  return Math.round(Math.max(1, Math.min(99, percentile)));
}

function calculateGSAxPercentile(gsax: number): number {
  // Rough GSAx percentile based on typical NHL distribution
  if (gsax >= 15) return 99;
  if (gsax >= 10) return 95;
  if (gsax >= 5) return 85;
  if (gsax >= 2) return 70;
  if (gsax >= 0) return 55;
  if (gsax >= -2) return 45;
  if (gsax >= -5) return 30;
  if (gsax >= -10) return 15;
  return 5;
}

function estimateGSAx(stats: GoalieSeasonStats): number {
  // Estimate GSAx from save percentage vs league average (~.907)
  const expectedSavePct = 0.907;
  const actualSavePct = stats.savePct;
  const shotsAgainst = stats.shotsAgainst;

  // GSAx = (Actual SV% - Expected SV%) * Shots Against
  const gsax = (actualSavePct - expectedSavePct) * shotsAgainst;

  return Math.round(gsax * 10) / 10;
}

function getTier(percentile: number): Tier {
  if (percentile >= 85) return "elite";
  if (percentile >= 65) return "above-average";
  if (percentile >= 35) return "average";
  if (percentile >= 15) return "below-average";
  return "poor";
}

function formatSavePct(savePct: number): string {
  if (savePct >= 1) return savePct.toFixed(3);
  return `.${Math.round(savePct * 1000)}`;
}

function getConsistencyRating(stats: GoalieSeasonStats): { label: string; description: string; tier: Tier } {
  // Estimate consistency based on shutouts and GAA variance
  const shutoutRate = stats.gamesStarted > 0 ? stats.shutouts / stats.gamesStarted : 0;
  const gaaQuality = stats.goalsAgainstAverage < 2.5 ? 1 : stats.goalsAgainstAverage < 3.0 ? 0.5 : 0;

  const consistencyScore = (shutoutRate * 0.3 + gaaQuality * 0.7) * 100;

  if (consistencyScore >= 60) return { label: "Elite", description: "Very reliable", tier: "elite" };
  if (consistencyScore >= 45) return { label: "Solid", description: "Dependable", tier: "above-average" };
  if (consistencyScore >= 30) return { label: "Average", description: "Typical variance", tier: "average" };
  if (consistencyScore >= 15) return { label: "Streaky", description: "Hot/cold runs", tier: "below-average" };
  return { label: "Volatile", description: "Unpredictable", tier: "poor" };
}

function generatePerformanceSummary(
  name: string,
  stats: GoalieSeasonStats,
  percentile: number,
  gsax: number
): string {
  const tier = getTier(percentile);
  const firstName = name.split(" ")[0];

  const tierDescriptions = {
    elite: "is performing at an elite level",
    "above-average": "is playing above league average",
    average: "is performing around league average",
    "below-average": "is struggling below league average",
    poor: "is having a difficult season",
  };

  const gsaxNote = gsax > 5
    ? `saving ${gsax.toFixed(1)} more goals than expected`
    : gsax < -5
    ? `allowing ${Math.abs(gsax).toFixed(1)} more goals than expected`
    : "performing close to expected levels";

  return `${firstName} ${tierDescriptions[tier]} this season, ${gsaxNote}. With a ${formatSavePct(stats.savePct)} save percentage across ${stats.gamesPlayed} games, ${firstName} ranks in the ${percentile}th percentile among NHL goalies.`;
}
