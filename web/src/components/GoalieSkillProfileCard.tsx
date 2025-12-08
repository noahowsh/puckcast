"use client";

import type { GoalieSeasonStats } from "@/types/player";

// =============================================================================
// Goalie Skill Profile Card Component
// =============================================================================

interface GoalieSkillProfileCardProps {
  stats: GoalieSeasonStats;
  playerName: string;
  allGoalies: { bio: { playerId: number }; stats: GoalieSeasonStats }[];
  age?: number;
}

type Tier = "elite" | "above-average" | "average" | "below-average" | "poor";

export function GoalieSkillProfileCard({ stats, playerName, allGoalies, age }: GoalieSkillProfileCardProps) {
  const qualifiedGoalies = allGoalies.filter(g => g.stats.gamesPlayed >= 10);

  // Calculate percentiles for each skill area
  const savePctPercentile = calculatePercentile(
    stats.savePct,
    qualifiedGoalies.map(g => g.stats.savePct)
  );

  const gaaPercentile = calculatePercentile(
    stats.goalsAgainstAverage,
    qualifiedGoalies.map(g => g.stats.goalsAgainstAverage),
    true // Lower is better
  );

  const shutoutPercentile = calculatePercentile(
    stats.shutouts,
    allGoalies.map(g => g.stats.shutouts)
  );

  const winsPercentile = calculatePercentile(
    stats.wins,
    allGoalies.map(g => g.stats.wins)
  );

  // Calculate workload percentile (shots faced per game)
  const shotsPerGame = stats.gamesPlayed > 0 ? stats.shotsAgainst / stats.gamesPlayed : 0;
  const workloadPercentile = calculatePercentile(
    shotsPerGame,
    allGoalies.filter(g => g.stats.gamesPlayed > 0).map(g => g.stats.shotsAgainst / g.stats.gamesPlayed)
  );

  // Estimate GSAx and consistency
  const gsax = estimateGSAx(stats);
  const gsaxPercentile = calculateGSAxPercentile(gsax);

  // Overall rating
  const overallPercentile = Math.round((savePctPercentile + gaaPercentile + gsaxPercentile + winsPercentile) / 4);
  const overallTier = getTier(overallPercentile);

  // Radar chart data
  const radarData = [
    { label: "SV%", value: savePctPercentile },
    { label: "GAA", value: gaaPercentile },
    { label: "GSAx", value: gsaxPercentile },
    { label: "Wins", value: winsPercentile },
    { label: "SO", value: shutoutPercentile },
  ];

  // Generate skill summary
  const skillSummary = generateSkillSummary(playerName, overallPercentile, savePctPercentile, gsax);

  return (
    <div className="relative bg-gradient-to-b from-[#1a1f2e] to-[#151922] border border-white/[0.06] rounded-xl overflow-hidden">
      {/* Header - Full width gradient */}
      <div className="relative border-b border-white/[0.06]">
        <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/20 via-emerald-500/8 to-transparent" />
        <div className="relative flex items-center justify-between px-6 py-5">
          <div>
            <h3 className="text-lg font-bold text-white">Goalie Skill Profile</h3>
            <p className="text-xs text-white/50 mt-0.5">Percentile Rankings vs. NHL Goalies</p>
          </div>
          <div className="flex items-center gap-5 text-right">
            {age && (
              <div>
                <span className="text-[10px] text-white/40 block">Age</span>
                <p className="text-sm font-semibold text-white">{age}</p>
              </div>
            )}
            <div>
              <span className="text-[10px] text-white/40 block">GP</span>
              <p className="text-sm font-semibold text-white">{stats.gamesPlayed}</p>
            </div>
          </div>
        </div>
      </div>

      <div style={{ padding: '2rem' }} className="space-y-6">
        {/* Overall Rating + Radar Chart Side by Side */}
        <div className="flex items-start gap-8">
          {/* Left: Overall Rating */}
          <div className="flex-shrink-0">
            <OverallRatingDisplay percentile={overallPercentile} tier={overallTier} />
          </div>

          {/* Center: Radar Chart */}
          <div className="flex-1 flex justify-center">
            <GoalieRadarChart data={radarData} />
          </div>
        </div>

        {/* Skill Summary */}
        <p className="text-xs text-white/60 leading-relaxed">{skillSummary}</p>

        {/* Core Metrics */}
        <div>
          <h4 className="text-xs font-semibold text-white/60 uppercase tracking-wide mb-4">
            Core Performance
          </h4>
          <div className="grid grid-cols-3 gap-4">
            <PercentileBox label="SV%" sublabel="Save Pct" percentile={savePctPercentile} />
            <PercentileBox label="GAA" sublabel="Goals Against" percentile={gaaPercentile} />
            <PercentileBox label="GSAx" sublabel="Goals Saved" percentile={gsaxPercentile} />
          </div>
        </div>

        {/* Secondary Metrics */}
        <div>
          <h4 className="text-xs font-semibold text-white/60 uppercase tracking-wide mb-4">
            Additional Metrics
          </h4>
          <div className="grid grid-cols-3 gap-4">
            <PercentileBox label="Wins" sublabel="Win Total" percentile={winsPercentile} />
            <PercentileBox label="SO" sublabel="Shutouts" percentile={shutoutPercentile} />
            <PercentileBox label="Workload" sublabel="Shots/Game" percentile={workloadPercentile} />
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center justify-center gap-3 pt-4 border-t border-white/[0.06]">
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
// Radar Chart Component
// =============================================================================

interface RadarDataPoint {
  label: string;
  value: number;
}

function GoalieRadarChart({ data }: { data: RadarDataPoint[] }) {
  const size = 220;
  const center = size / 2;
  const maxRadius = size / 2 - 35;
  const levels = [25, 50, 75, 100];
  const angleStep = (2 * Math.PI) / data.length;
  const startAngle = -Math.PI / 2;

  const dataPoints = data.map((d, i) => {
    const angle = startAngle + i * angleStep;
    const radius = (d.value / 100) * maxRadius;
    return {
      x: center + radius * Math.cos(angle),
      y: center + radius * Math.sin(angle),
      label: d.label,
      value: d.value,
      angle,
    };
  });

  const dataPath = dataPoints.map((p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`)).join(" ") + " Z";

  return (
    <svg width={size} height={size} className="overflow-visible">
      {/* Background circles */}
      {levels.map((level) => (
        <circle key={level} cx={center} cy={center} r={(level / 100) * maxRadius} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="1" />
      ))}

      {/* Axis lines */}
      {data.map((_, i) => {
        const angle = startAngle + i * angleStep;
        return <line key={i} x1={center} y1={center} x2={center + maxRadius * Math.cos(angle)} y2={center + maxRadius * Math.sin(angle)} stroke="rgba(255,255,255,0.08)" strokeWidth="1" />;
      })}

      {/* Data polygon */}
      <path d={dataPath} fill="rgba(56, 189, 248, 0.25)" stroke="rgb(56, 189, 248)" strokeWidth="2.5" strokeLinejoin="round" />

      {/* Data points */}
      {dataPoints.map((p, i) => (
        <circle key={`point-${i}`} cx={p.x} cy={p.y} r="3" fill="rgb(56, 189, 248)" />
      ))}

      {/* Axis labels */}
      {dataPoints.map((p, i) => {
        const labelRadius = maxRadius + 22;
        return (
          <text key={i} x={center + labelRadius * Math.cos(p.angle)} y={center + labelRadius * Math.sin(p.angle)} fill="rgba(255,255,255,0.7)" fontSize="10" fontWeight="600" textAnchor="middle" dominantBaseline="middle">
            {p.label}
          </text>
        );
      })}
    </svg>
  );
}

// =============================================================================
// Helper Components
// =============================================================================

function OverallRatingDisplay({ percentile, tier }: { percentile: number; tier: Tier }) {
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
      <div className={`w-20 h-20 rounded-full ${colors.bg} ring-2 ${colors.ring} flex flex-col items-center justify-center`}>
        <span className={`text-2xl font-black ${colors.text}`}>{percentile}</span>
        <span className="text-[9px] text-white/40 -mt-0.5">percentile</span>
      </div>
      <div className="text-center">
        <p className={`text-xs font-semibold ${colors.text}`}>{colors.label}</p>
        <p className="text-[10px] text-white/40">Overall</p>
      </div>
    </div>
  );
}

function PercentileBox({ label, sublabel, percentile }: { label: string; sublabel: string; percentile: number }) {
  const tier = getTier(percentile);

  return (
    <div className={`p-4 rounded-lg text-center ${getTierBackground(tier)}`}>
      <p className={`text-xl font-bold ${getTierTextColor(tier)}`}>{percentile}%</p>
      <p className="text-[11px] text-white/50 font-medium mt-1">{label}</p>
      <p className="text-[10px] text-white/30">{sublabel}</p>
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
  const expectedSavePct = 0.907;
  const actualSavePct = stats.savePct;
  const shotsAgainst = stats.shotsAgainst;
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

function getTierBackground(tier: Tier): string {
  switch (tier) {
    case "elite": return "bg-sky-500/15";
    case "above-average": return "bg-emerald-500/15";
    case "average": return "bg-white/[0.04]";
    case "below-average": return "bg-amber-500/10";
    case "poor": return "bg-rose-500/10";
  }
}

function getTierTextColor(tier: Tier): string {
  switch (tier) {
    case "elite": return "text-sky-300";
    case "above-average": return "text-emerald-400";
    case "average": return "text-white/70";
    case "below-average": return "text-amber-400";
    case "poor": return "text-rose-400";
  }
}

function generateSkillSummary(name: string, percentile: number, savePct: number, gsax: number): string {
  const firstName = name.split(" ")[0];
  const tier = getTier(percentile);

  const tierDescriptions = {
    elite: "is performing at an elite level among NHL goalies",
    "above-average": "is playing above league average",
    average: "is performing around league average",
    "below-average": "is struggling below league average",
    poor: "is having a difficult season",
  };

  const gsaxNote = gsax > 5
    ? `, saving ${gsax.toFixed(1)} more goals than expected`
    : gsax < -5
    ? `, allowing ${Math.abs(gsax).toFixed(1)} more goals than expected`
    : "";

  return `${firstName} ${tierDescriptions[tier]}${gsaxNote}. Ranking in the ${percentile}th percentile overall, with save percentage in the ${savePct}th percentile.`;
}
