"use client";

import type { SkillProfile, PercentileRating } from "@/types/player";

// =============================================================================
// Skill Profile Card Component (GOA%-Style)
// =============================================================================

interface SkillProfileCardProps {
  profile: SkillProfile;
  playerName: string;
  age?: number;
  evTOI?: string;
}

export function SkillProfileCard({ profile, playerName, age, evTOI }: SkillProfileCardProps) {
  const {
    overallRating,
    evenStrength,
    specialTeams,
    talents,
    skillSummary,
    position,
  } = profile;

  const positionLabel = getPositionLabel(position);

  // Prepare radar chart data
  const radarData = [
    { label: "EV OFF", value: evenStrength.offensive.value },
    { label: "PP OFF", value: specialTeams.powerPlayOffense.value },
    { label: "PK DEF", value: specialTeams.penaltyKillDefense?.value ?? 0 },
    { label: "EV DEF", value: evenStrength.defensive.value },
    { label: "EV +/-", value: evenStrength.overall.value },
  ];

  return (
    <div className="card p-0 overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-white/[0.06] bg-gradient-to-r from-emerald-500/10 to-transparent">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-white">Skill Profile</h3>
            <p className="text-xs text-white/50">Percentile Rankings vs. NHL {positionLabel}s</p>
          </div>
          <div className="flex items-center gap-4 text-right">
            {age && (
              <div>
                <span className="text-[10px] text-white/40 block">Age</span>
                <p className="text-sm font-semibold text-white">{age}</p>
              </div>
            )}
            {evTOI && (
              <div>
                <span className="text-[10px] text-white/40 block">EV TOI</span>
                <p className="text-sm font-semibold text-white">{evTOI}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="p-5 space-y-5">
        {/* Overall Rating + Radar Chart Row */}
        <div className="grid grid-cols-2 gap-4">
          {/* Overall Rating */}
          <div className="flex flex-col items-center justify-center py-2">
            <OverallRatingBadge rating={overallRating} />
            <p className="text-[10px] text-white/50 mt-3">Overall Skill Rating</p>
          </div>

          {/* Radar Chart */}
          <div className="flex flex-col items-center">
            <h4 className="text-[10px] font-semibold text-white/50 uppercase tracking-wide mb-2">
              Relative Skill Chart
            </h4>
            <SkillRadarChart data={radarData} />
          </div>
        </div>

        {/* Skill Summary */}
        <p className="text-xs text-white/60 leading-relaxed">{skillSummary}</p>

        {/* Even Strength Impact */}
        <div>
          <h4 className="text-xs font-semibold text-white/60 uppercase tracking-wide mb-3">
            Even Strength Impact
          </h4>
          <div className="grid grid-cols-3 gap-2">
            <PercentileBox label="EV OFF" sublabel="Offensive" rating={evenStrength.offensive} />
            <PercentileBox label="EV DEF" sublabel="Defensive" rating={evenStrength.defensive} />
            <PercentileBox label="EV +/-" sublabel="Overall" rating={evenStrength.overall} />
          </div>
        </div>

        {/* Special Teams Impact */}
        <div>
          <h4 className="text-xs font-semibold text-white/60 uppercase tracking-wide mb-3">
            Special Teams Impact
          </h4>
          <div className="grid grid-cols-3 gap-2">
            <PercentileBox label="PP OFF" sublabel="Power Play" rating={specialTeams.powerPlayOffense} />
            <PercentileBox label="PK DEF" sublabel="Penalty Kill" rating={specialTeams.penaltyKillDefense} showNA={!specialTeams.penaltyKillDefense} />
            <PercentileBox label="PP/EV" sublabel="Combined" rating={specialTeams.combinedPPEV} />
          </div>
        </div>

        {/* Talent Profile */}
        <div>
          <h4 className="text-xs font-semibold text-white/60 uppercase tracking-wide mb-3">
            Talent Profile
          </h4>
          <div className="grid grid-cols-2 gap-2">
            <TalentBar label="Finishing" rating={talents.finishing} />
            <TalentBar label="Playmaking" rating={talents.playmaking} />
            <TalentBar label="Penalty Impact" rating={talents.penaltyImpact} />
            <TalentBar label="Versatility" rating={talents.versatility} />
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center justify-center gap-2 pt-3 border-t border-white/[0.04]">
          <LegendItem color="bg-rose-500/50" label="Replacement" />
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

function SkillRadarChart({ data }: { data: RadarDataPoint[] }) {
  const size = 160;
  const center = size / 2;
  const maxRadius = size / 2 - 24;
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
        <circle key={level} cx={center} cy={center} r={(level / 100) * maxRadius} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
      ))}

      {/* Axis lines */}
      {data.map((_, i) => {
        const angle = startAngle + i * angleStep;
        return <line key={i} x1={center} y1={center} x2={center + maxRadius * Math.cos(angle)} y2={center + maxRadius * Math.sin(angle)} stroke="rgba(255,255,255,0.06)" strokeWidth="1" />;
      })}

      {/* Data polygon */}
      <path d={dataPath} fill="rgba(110, 240, 194, 0.2)" stroke="rgb(110, 240, 194)" strokeWidth="2" strokeLinejoin="round" />

      {/* Axis labels */}
      {dataPoints.map((p, i) => {
        const labelRadius = maxRadius + 14;
        return (
          <text key={i} x={center + labelRadius * Math.cos(p.angle)} y={center + labelRadius * Math.sin(p.angle)} fill="rgba(255,255,255,0.5)" fontSize="8" fontWeight="500" textAnchor="middle" dominantBaseline="middle">
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

function OverallRatingBadge({ rating }: { rating: PercentileRating }) {
  const { value, tier } = rating;

  const tierStyles = {
    elite: "from-sky-400 to-sky-600 shadow-sky-500/40",
    "above-average": "from-emerald-400 to-emerald-600 shadow-emerald-500/40",
    average: "from-white/20 to-white/10 shadow-white/10",
    "below-average": "from-amber-400 to-amber-600 shadow-amber-500/40",
    replacement: "from-rose-400 to-rose-600 shadow-rose-500/40",
  };

  return (
    <div className={`w-20 h-20 rounded-xl bg-gradient-to-br ${tierStyles[tier]} flex flex-col items-center justify-center shadow-lg`}>
      <span className="text-2xl font-black text-white">{value}%</span>
      <span className="text-[8px] uppercase tracking-wide text-white/80 font-semibold">
        {tier.replace("-", " ")}
      </span>
    </div>
  );
}

function PercentileBox({ label, sublabel, rating, showNA = false }: { label: string; sublabel: string; rating: PercentileRating | null; showNA?: boolean }) {
  if (showNA || !rating) {
    return (
      <div className="p-2.5 bg-white/[0.03] rounded-lg text-center">
        <p className="text-lg font-bold text-white/30">N/A</p>
        <p className="text-[10px] text-white/50 font-medium">{label}</p>
        <p className="text-[9px] text-white/30">{sublabel}</p>
      </div>
    );
  }

  const { value, tier } = rating;

  return (
    <div className={`p-2.5 rounded-lg text-center ${getTierBackground(tier)}`}>
      <p className={`text-lg font-bold ${getTierTextColor(tier)}`}>{value}%</p>
      <p className="text-[10px] text-white/50 font-medium">{label}</p>
      <p className="text-[9px] text-white/30">{sublabel}</p>
    </div>
  );
}

function TalentBar({ label, rating }: { label: string; rating: PercentileRating }) {
  const { value, tier } = rating;

  return (
    <div className="p-2.5 bg-white/[0.03] rounded-lg">
      <div className="flex justify-between items-center mb-1.5">
        <span className="text-[10px] text-white/60">{label}</span>
        <span className={`text-xs font-bold ${getTierTextColor(tier)}`}>{value}%</span>
      </div>
      <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
        <div className={`h-full ${getTierBarColor(tier)} rounded-full`} style={{ width: `${value}%` }} />
      </div>
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

function getPositionLabel(position: string): string {
  switch (position) {
    case "D": return "Defensemen";
    case "G": return "Goalie";
    default: return "Forward";
  }
}

function getTierBackground(tier: PercentileRating["tier"]): string {
  switch (tier) {
    case "elite": return "bg-sky-500/15";
    case "above-average": return "bg-emerald-500/15";
    case "average": return "bg-white/[0.04]";
    case "below-average": return "bg-amber-500/10";
    case "replacement": return "bg-rose-500/10";
  }
}

function getTierTextColor(tier: PercentileRating["tier"]): string {
  switch (tier) {
    case "elite": return "text-sky-300";
    case "above-average": return "text-emerald-400";
    case "average": return "text-white/70";
    case "below-average": return "text-amber-400";
    case "replacement": return "text-rose-400";
  }
}

function getTierBarColor(tier: PercentileRating["tier"]): string {
  switch (tier) {
    case "elite": return "bg-sky-400";
    case "above-average": return "bg-emerald-400";
    case "average": return "bg-white/40";
    case "below-average": return "bg-amber-400";
    case "replacement": return "bg-rose-400";
  }
}
