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
      {/* Header with Overall Rating */}
      <div className="px-6 py-5 border-b border-white/[0.06] bg-gradient-to-r from-emerald-500/10 to-transparent">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold text-white">Skill Profile</h3>
            <p className="text-sm text-white/50 mt-1">Percentile Rankings vs. NHL {positionLabel}s</p>
          </div>
          <div className="flex items-center gap-6">
            {age && (
              <div className="text-right">
                <span className="text-xs text-white/40">Age</span>
                <p className="text-lg font-semibold text-white">{age}</p>
              </div>
            )}
            {evTOI && (
              <div className="text-right">
                <span className="text-xs text-white/40">EV TOI</span>
                <p className="text-lg font-semibold text-white">{evTOI}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="p-6 space-y-8">
        {/* Overall Rating + Radar Chart Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Overall Rating - Large Display */}
          <div className="flex flex-col items-center justify-center">
            <OverallRatingBadge rating={overallRating} />
            <p className="text-sm text-white/50 mt-4 mb-2">Overall Skill Rating</p>
            <p className="text-xs text-white/60 leading-relaxed text-center max-w-xs">{skillSummary}</p>
          </div>

          {/* Radar Chart */}
          <div className="flex flex-col items-center">
            <h4 className="text-sm font-semibold text-white/70 uppercase tracking-wide mb-4">
              Relative Skill Chart
            </h4>
            <SkillRadarChart data={radarData} />
            <p className="text-[10px] text-white/40 mt-3 text-center italic">
              Larger enclosed area = More versatile player
            </p>
          </div>
        </div>

        {/* Even Strength Percentiles */}
        <div>
          <h4 className="text-sm font-semibold text-white/70 uppercase tracking-wide mb-4">
            Even Strength Impact
          </h4>
          <div className="grid grid-cols-3 gap-4">
            <PercentileBox
              label="EV OFF"
              sublabel="Offensive"
              rating={evenStrength.offensive}
            />
            <PercentileBox
              label="EV DEF"
              sublabel="Defensive"
              rating={evenStrength.defensive}
            />
            <PercentileBox
              label="EV +/-"
              sublabel="Overall"
              rating={evenStrength.overall}
            />
          </div>
        </div>

        {/* Special Teams Percentiles */}
        <div>
          <h4 className="text-sm font-semibold text-white/70 uppercase tracking-wide mb-4">
            Special Teams Impact
          </h4>
          <div className="grid grid-cols-3 gap-4">
            <PercentileBox
              label="PP OFF"
              sublabel="Power Play"
              rating={specialTeams.powerPlayOffense}
            />
            <PercentileBox
              label="PK DEF"
              sublabel="Penalty Kill"
              rating={specialTeams.penaltyKillDefense}
              showNA={!specialTeams.penaltyKillDefense}
            />
            <PercentileBox
              label="PP/EV"
              sublabel="Combined"
              rating={specialTeams.combinedPPEV}
            />
          </div>
        </div>

        {/* Talent Tools */}
        <div>
          <h4 className="text-sm font-semibold text-white/70 uppercase tracking-wide mb-4">
            Talent Profile
          </h4>
          <div className="grid grid-cols-2 gap-4">
            <TalentBar label="Finishing" rating={talents.finishing} />
            <TalentBar label="Playmaking" rating={talents.playmaking} />
            <TalentBar label="Penalty Impact" rating={talents.penaltyImpact} />
            <TalentBar label="Versatility" rating={talents.versatility} />
          </div>
        </div>

        {/* Legend */}
        <div className="pt-5 border-t border-white/[0.06]">
          <div className="flex items-center justify-center gap-3 flex-wrap">
            <LegendItem color="bg-rose-500/50" label="Replacement" />
            <LegendItem color="bg-amber-500/40" label="Below Avg" />
            <LegendItem color="bg-white/30" label="Average" />
            <LegendItem color="bg-emerald-500/50" label="Above Avg" />
            <LegendItem color="bg-sky-500/60" label="Elite" />
          </div>
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
  const size = 220;
  const center = size / 2;
  const maxRadius = size / 2 - 30;
  const levels = [25, 50, 75, 100];
  const angleStep = (2 * Math.PI) / data.length;
  const startAngle = -Math.PI / 2; // Start from top

  // Calculate points for the data polygon
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
        <circle
          key={level}
          cx={center}
          cy={center}
          r={(level / 100) * maxRadius}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth="1"
        />
      ))}

      {/* Axis lines */}
      {data.map((_, i) => {
        const angle = startAngle + i * angleStep;
        const x2 = center + maxRadius * Math.cos(angle);
        const y2 = center + maxRadius * Math.sin(angle);
        return (
          <line
            key={i}
            x1={center}
            y1={center}
            x2={x2}
            y2={y2}
            stroke="rgba(255,255,255,0.08)"
            strokeWidth="1"
          />
        );
      })}

      {/* Level labels */}
      {levels.map((level) => (
        <text
          key={level}
          x={center + 4}
          y={center - (level / 100) * maxRadius + 4}
          fill="rgba(255,255,255,0.25)"
          fontSize="8"
        >
          {level}
        </text>
      ))}

      {/* Data polygon */}
      <path
        d={dataPath}
        fill="rgba(110, 240, 194, 0.25)"
        stroke="rgb(110, 240, 194)"
        strokeWidth="2.5"
        strokeLinejoin="round"
      />

      {/* Data points */}
      {dataPoints.map((p, i) => (
        <circle
          key={i}
          cx={p.x}
          cy={p.y}
          r="4"
          fill="rgb(110, 240, 194)"
          stroke="rgba(0,0,0,0.3)"
          strokeWidth="1"
        />
      ))}

      {/* Axis labels */}
      {dataPoints.map((p, i) => {
        const labelRadius = maxRadius + 20;
        const labelX = center + labelRadius * Math.cos(p.angle);
        const labelY = center + labelRadius * Math.sin(p.angle);
        return (
          <text
            key={i}
            x={labelX}
            y={labelY}
            fill="rgba(255,255,255,0.6)"
            fontSize="11"
            fontWeight="600"
            textAnchor="middle"
            dominantBaseline="middle"
          >
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
    elite: "from-sky-400 to-sky-600 text-white shadow-sky-500/30",
    "above-average": "from-emerald-400 to-emerald-600 text-white shadow-emerald-500/30",
    average: "from-white/30 to-white/10 text-white shadow-white/10",
    "below-average": "from-amber-400 to-amber-600 text-white shadow-amber-500/30",
    replacement: "from-rose-400 to-rose-600 text-white shadow-rose-500/30",
  };

  return (
    <div
      className={`w-28 h-28 rounded-2xl bg-gradient-to-br ${tierStyles[tier]} flex flex-col items-center justify-center shadow-xl`}
    >
      <span className="text-4xl font-black">{value}%</span>
      <span className="text-[10px] uppercase tracking-wider opacity-80 font-semibold mt-1">
        {tier.replace("-", " ")}
      </span>
    </div>
  );
}

function PercentileBox({
  label,
  sublabel,
  rating,
  showNA = false,
}: {
  label: string;
  sublabel: string;
  rating: PercentileRating | null;
  showNA?: boolean;
}) {
  if (showNA || !rating) {
    return (
      <div className="p-4 bg-white/[0.03] rounded-xl text-center border border-white/[0.04]">
        <p className="text-2xl font-bold text-white/30">N/A</p>
        <p className="text-sm text-white/70 font-medium mt-2">{label}</p>
        <p className="text-xs text-white/40 mt-0.5">{sublabel}</p>
      </div>
    );
  }

  const { value, tier } = rating;
  const bgClass = getTierBackground(tier);
  const textClass = getTierTextColor(tier);

  return (
    <div className={`p-4 rounded-xl text-center border border-white/[0.04] ${bgClass}`}>
      <p className={`text-2xl font-bold ${textClass}`}>{value}%</p>
      <p className="text-sm text-white/70 font-medium mt-2">{label}</p>
      <p className="text-xs text-white/40 mt-0.5">{sublabel}</p>
    </div>
  );
}

function TalentBar({ label, rating }: { label: string; rating: PercentileRating }) {
  const { value, tier } = rating;
  const barColor = getTierBarColor(tier);

  return (
    <div className="p-4 bg-white/[0.03] rounded-xl border border-white/[0.04]">
      <div className="flex justify-between items-center mb-3">
        <span className="text-sm text-white/70 font-medium">{label}</span>
        <span className={`text-lg font-bold ${getTierTextColor(tier)}`}>{value}%</span>
      </div>
      <div className="h-2.5 bg-white/[0.06] rounded-full overflow-hidden">
        <div
          className={`h-full ${barColor} rounded-full transition-all duration-500`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className={`w-4 h-4 rounded ${color}`} />
      <span className="text-xs text-white/50">{label}</span>
    </div>
  );
}

// =============================================================================
// Helper Functions
// =============================================================================

function getPositionLabel(position: string): string {
  switch (position) {
    case "D":
      return "Defensemen";
    case "G":
      return "Goalie";
    default:
      return "Forward";
  }
}

function getTierBackground(tier: PercentileRating["tier"]): string {
  switch (tier) {
    case "elite":
      return "bg-sky-500/20";
    case "above-average":
      return "bg-emerald-500/20";
    case "average":
      return "bg-white/[0.06]";
    case "below-average":
      return "bg-amber-500/15";
    case "replacement":
      return "bg-rose-500/15";
  }
}

function getTierTextColor(tier: PercentileRating["tier"]): string {
  switch (tier) {
    case "elite":
      return "text-sky-300";
    case "above-average":
      return "text-emerald-400";
    case "average":
      return "text-white/80";
    case "below-average":
      return "text-amber-400";
    case "replacement":
      return "text-rose-400";
  }
}

function getTierBarColor(tier: PercentileRating["tier"]): string {
  switch (tier) {
    case "elite":
      return "bg-sky-400";
    case "above-average":
      return "bg-emerald-400";
    case "average":
      return "bg-white/40";
    case "below-average":
      return "bg-amber-400";
    case "replacement":
      return "bg-rose-400";
  }
}
