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

  return (
    <div className="card p-0 overflow-hidden">
      {/* Header with Overall Rating */}
      <div className="px-5 py-4 border-b border-white/[0.06] bg-gradient-to-r from-emerald-500/10 to-transparent">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-white">Skill Profile</h3>
            <p className="text-xs text-white/50 mt-0.5">Percentile Rankings vs. NHL {positionLabel}s</p>
          </div>
          <div className="flex items-center gap-4">
            {age && (
              <div className="text-right">
                <span className="text-xs text-white/40">Age</span>
                <p className="text-sm font-semibold text-white">{age}</p>
              </div>
            )}
            {evTOI && (
              <div className="text-right">
                <span className="text-xs text-white/40">EV TOI</span>
                <p className="text-sm font-semibold text-white">{evTOI}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="p-5 space-y-6">
        {/* Overall Rating - Large Display */}
        <div className="flex items-center gap-6">
          <div className="flex-shrink-0">
            <OverallRatingBadge rating={overallRating} />
          </div>
          <div className="flex-1">
            <p className="text-sm text-white/50 mb-1">Overall Skill Rating</p>
            <p className="text-xs text-white/70 leading-relaxed">{skillSummary}</p>
          </div>
        </div>

        {/* Even Strength Percentiles */}
        <div>
          <h4 className="text-sm font-semibold text-white/70 uppercase tracking-wide mb-3">
            Even Strength Impact
          </h4>
          <div className="grid grid-cols-3 gap-3">
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
          <h4 className="text-sm font-semibold text-white/70 uppercase tracking-wide mb-3">
            Special Teams Impact
          </h4>
          <div className="grid grid-cols-3 gap-3">
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
          <h4 className="text-sm font-semibold text-white/70 uppercase tracking-wide mb-3">
            Talent Profile
          </h4>
          <div className="grid grid-cols-2 gap-3">
            <TalentBar label="Finishing" rating={talents.finishing} />
            <TalentBar label="Playmaking" rating={talents.playmaking} />
            <TalentBar label="Penalty Impact" rating={talents.penaltyImpact} />
            <TalentBar label="Versatility" rating={talents.versatility} />
          </div>
        </div>

        {/* Legend */}
        <div className="pt-4 border-t border-white/[0.06]">
          <div className="flex items-center justify-center gap-2 flex-wrap">
            <LegendItem color="bg-rose-500/40" label="Replacement" />
            <LegendItem color="bg-amber-500/30" label="Below Avg" />
            <LegendItem color="bg-white/20" label="Average" />
            <LegendItem color="bg-emerald-500/40" label="Above Avg" />
            <LegendItem color="bg-sky-500/50" label="Elite" />
          </div>
        </div>
      </div>
    </div>
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
      className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${tierStyles[tier]} flex flex-col items-center justify-center shadow-lg`}
    >
      <span className="text-3xl font-black">{value}%</span>
      <span className="text-[9px] uppercase tracking-wider opacity-80 font-medium">
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
      <div className="p-3 bg-white/[0.03] rounded-lg text-center">
        <p className="text-xl font-bold text-white/30">N/A</p>
        <p className="text-xs text-white/70 font-medium mt-1">{label}</p>
        <p className="text-[10px] text-white/40">{sublabel}</p>
      </div>
    );
  }

  const { value, tier } = rating;
  const bgClass = getTierBackground(tier);
  const textClass = getTierTextColor(tier);

  return (
    <div className={`p-3 rounded-lg text-center ${bgClass}`}>
      <p className={`text-xl font-bold ${textClass}`}>{value}%</p>
      <p className="text-xs text-white/70 font-medium mt-1">{label}</p>
      <p className="text-[10px] text-white/40">{sublabel}</p>
    </div>
  );
}

function TalentBar({ label, rating }: { label: string; rating: PercentileRating }) {
  const { value, tier } = rating;
  const barColor = getTierBarColor(tier);

  return (
    <div className="p-3 bg-white/[0.03] rounded-lg">
      <div className="flex justify-between items-center mb-2">
        <span className="text-xs text-white/70 font-medium">{label}</span>
        <span className={`text-sm font-bold ${getTierTextColor(tier)}`}>{value}%</span>
      </div>
      <div className="h-2 bg-white/[0.06] rounded-full overflow-hidden">
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
    <div className="flex items-center gap-1.5">
      <div className={`w-3 h-3 rounded ${color}`} />
      <span className="text-[10px] text-white/50">{label}</span>
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
