"use client";

import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import type { SkaterCard, GoalieDetailCard } from "@/types/player";
import { TeamLogo } from "./TeamLogo";

// =============================================================================
// Skater Card Component
// =============================================================================

interface SkaterCardProps {
  player: SkaterCard;
  rank?: number;
  highlightStat?: "points" | "goals" | "assists" | "plusMinus";
  compact?: boolean;
  showTeam?: boolean;
  linkToProfile?: boolean;
}

export function PlayerCardView({
  player,
  rank,
  highlightStat = "points",
  compact = false,
  showTeam = true,
  linkToProfile = true,
}: SkaterCardProps) {
  const { bio, stats } = player;
  const [imgError, setImgError] = useState(false);

  const positionLabel = getPositionLabel(bio.position);
  const highlightValue = getHighlightValue(stats, highlightStat);
  const highlightLabel = getHighlightLabel(highlightStat);

  const content = (
    <article className={`card transition-all duration-200 ${linkToProfile ? "hover:border-white/20 cursor-pointer" : ""} ${compact ? "p-3" : "p-4"}`}>
      <div className="flex items-center gap-3">
        {/* Rank Badge */}
        {rank !== undefined && (
          <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-white/[0.06] flex items-center justify-center">
            <span className="text-sm font-bold text-white/80">#{rank}</span>
          </div>
        )}

        {/* Player Headshot or Team Logo */}
        <div className="relative flex-shrink-0">
          {bio.headshot && !imgError ? (
            <Image
              src={bio.headshot}
              alt={bio.fullName}
              width={compact ? 40 : 48}
              height={compact ? 40 : 48}
              className="rounded-full object-cover bg-white/[0.03]"
              onError={() => setImgError(true)}
            />
          ) : (
            <div className={`${compact ? "w-10 h-10" : "w-12 h-12"} rounded-full bg-white/[0.06] flex items-center justify-center`}>
              <TeamLogo teamAbbrev={bio.teamAbbrev} size="sm" />
            </div>
          )}
          {/* Position badge */}
          <span className="absolute -bottom-1 -right-1 text-[10px] font-bold bg-white/10 text-white/70 px-1.5 py-0.5 rounded">
            {bio.position}
          </span>
        </div>

        {/* Player Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className={`font-semibold text-white truncate ${compact ? "text-sm" : "text-base"}`}>
              {bio.fullName}
            </h3>
            {bio.jerseyNumber && (
              <span className="text-xs text-white/40">#{bio.jerseyNumber}</span>
            )}
          </div>
          <div className="flex items-center gap-2 mt-0.5">
            {showTeam && (
              <>
                <TeamLogo teamAbbrev={bio.teamAbbrev} size="xs" />
                <span className="text-xs text-white/60">{bio.teamAbbrev}</span>
                <span className="text-white/30">•</span>
              </>
            )}
            <span className="text-xs text-white/60">{positionLabel}</span>
          </div>
        </div>

        {/* Highlight Stat */}
        <div className="flex-shrink-0 text-right">
          <p className={`font-bold text-white ${compact ? "text-xl" : "text-2xl"}`}>
            {highlightValue}
          </p>
          <p className="text-[10px] text-white/50 uppercase tracking-wide">{highlightLabel}</p>
        </div>
      </div>

      {/* Expanded Stats Row */}
      {!compact && (
        <div className="grid grid-cols-5 gap-2 mt-4 pt-4 border-t border-white/[0.06]">
          <StatMini label="GP" value={stats.gamesPlayed} />
          <StatMini label="G" value={stats.goals} />
          <StatMini label="A" value={stats.assists} />
          <StatMini label="P" value={stats.points} highlight />
          <StatMini label="+/-" value={stats.plusMinus} colored />
        </div>
      )}
    </article>
  );

  if (linkToProfile) {
    return (
      <Link href={`/players/${bio.playerId}`} className="block">
        {content}
      </Link>
    );
  }

  return content;
}

// =============================================================================
// Goalie Card Component
// =============================================================================

interface GoalieCardProps {
  goalie: GoalieDetailCard;
  rank?: number;
  highlightStat?: "wins" | "savePct" | "goalsAgainstAverage" | "shutouts";
  compact?: boolean;
  showTeam?: boolean;
  linkToProfile?: boolean;
}

export function GoalieCardView({
  goalie,
  rank,
  highlightStat = "wins",
  compact = false,
  showTeam = true,
  linkToProfile = true,
}: GoalieCardProps) {
  const { bio, stats } = goalie;
  const [imgError, setImgError] = useState(false);

  const highlightValue = getGoalieHighlightValue(stats, highlightStat);
  const highlightLabel = getGoalieHighlightLabel(highlightStat);

  const content = (
    <article className={`card transition-all duration-200 ${linkToProfile ? "hover:border-white/20 cursor-pointer" : ""} ${compact ? "p-3" : "p-4"}`}>
      <div className="flex items-center gap-3">
        {/* Rank Badge */}
        {rank !== undefined && (
          <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-white/[0.06] flex items-center justify-center">
            <span className="text-sm font-bold text-white/80">#{rank}</span>
          </div>
        )}

        {/* Player Headshot or Team Logo */}
        <div className="relative flex-shrink-0">
          {bio.headshot && !imgError ? (
            <Image
              src={bio.headshot}
              alt={bio.fullName}
              width={compact ? 40 : 48}
              height={compact ? 40 : 48}
              className="rounded-full object-cover bg-white/[0.03]"
              onError={() => setImgError(true)}
            />
          ) : (
            <div className={`${compact ? "w-10 h-10" : "w-12 h-12"} rounded-full bg-white/[0.06] flex items-center justify-center`}>
              <TeamLogo teamAbbrev={bio.teamAbbrev} size="sm" />
            </div>
          )}
          {/* Position badge */}
          <span className="absolute -bottom-1 -right-1 text-[10px] font-bold bg-sky-500/20 text-sky-300 px-1.5 py-0.5 rounded">
            G
          </span>
        </div>

        {/* Player Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className={`font-semibold text-white truncate ${compact ? "text-sm" : "text-base"}`}>
              {bio.fullName}
            </h3>
            {bio.jerseyNumber && (
              <span className="text-xs text-white/40">#{bio.jerseyNumber}</span>
            )}
          </div>
          <div className="flex items-center gap-2 mt-0.5">
            {showTeam && (
              <>
                <TeamLogo teamAbbrev={bio.teamAbbrev} size="xs" />
                <span className="text-xs text-white/60">{bio.teamAbbrev}</span>
                <span className="text-white/30">•</span>
              </>
            )}
            <span className="text-xs text-white/60">Goaltender</span>
          </div>
        </div>

        {/* Highlight Stat */}
        <div className="flex-shrink-0 text-right">
          <p className={`font-bold text-white ${compact ? "text-xl" : "text-2xl"}`}>
            {highlightValue}
          </p>
          <p className="text-[10px] text-white/50 uppercase tracking-wide">{highlightLabel}</p>
        </div>
      </div>

      {/* Expanded Stats Row */}
      {!compact && (
        <div className="grid grid-cols-5 gap-2 mt-4 pt-4 border-t border-white/[0.06]">
          <StatMini label="GP" value={stats.gamesPlayed} />
          <StatMini label="W" value={stats.wins} highlight />
          <StatMini label="L" value={stats.losses} />
          <StatMini label="SV%" value={formatSavePct(stats.savePct)} />
          <StatMini label="GAA" value={stats.goalsAgainstAverage.toFixed(2)} />
        </div>
      )}
    </article>
  );

  if (linkToProfile) {
    return (
      <Link href={`/goalies/${bio.playerId}`} className="block">
        {content}
      </Link>
    );
  }

  return content;
}

// =============================================================================
// Mini Stat Component
// =============================================================================

function StatMini({
  label,
  value,
  highlight = false,
  colored = false,
}: {
  label: string;
  value: string | number;
  highlight?: boolean;
  colored?: boolean;
}) {
  const numValue = typeof value === "number" ? value : parseFloat(value);
  const colorClass = colored && !isNaN(numValue)
    ? numValue > 0
      ? "text-emerald-400"
      : numValue < 0
        ? "text-rose-400"
        : "text-white"
    : highlight
      ? "text-sky-300"
      : "text-white";

  const displayValue = colored && typeof value === "number" && value > 0 ? `+${value}` : value;

  return (
    <div className="text-center">
      <p className={`text-sm font-semibold ${colorClass}`}>{displayValue}</p>
      <p className="text-[10px] text-white/40 uppercase">{label}</p>
    </div>
  );
}

// =============================================================================
// Helper Functions
// =============================================================================

function getPositionLabel(position: string): string {
  const labels: Record<string, string> = {
    C: "Center",
    L: "Left Wing",
    R: "Right Wing",
    D: "Defenseman",
    G: "Goaltender",
  };
  return labels[position] || position;
}

function getHighlightValue(stats: SkaterCard["stats"], stat: string): string {
  switch (stat) {
    case "points":
      return String(stats.points);
    case "goals":
      return String(stats.goals);
    case "assists":
      return String(stats.assists);
    case "plusMinus":
      return stats.plusMinus >= 0 ? `+${stats.plusMinus}` : String(stats.plusMinus);
    default:
      return String(stats.points);
  }
}

function getHighlightLabel(stat: string): string {
  const labels: Record<string, string> = {
    points: "Points",
    goals: "Goals",
    assists: "Assists",
    plusMinus: "+/-",
  };
  return labels[stat] || "PTS";
}

function getGoalieHighlightValue(stats: GoalieDetailCard["stats"], stat: string): string {
  switch (stat) {
    case "wins":
      return String(stats.wins);
    case "savePct":
      return formatSavePct(stats.savePct);
    case "goalsAgainstAverage":
      return stats.goalsAgainstAverage.toFixed(2);
    case "shutouts":
      return String(stats.shutouts);
    default:
      return String(stats.wins);
  }
}

function getGoalieHighlightLabel(stat: string): string {
  const labels: Record<string, string> = {
    wins: "Wins",
    savePct: "SV%",
    goalsAgainstAverage: "GAA",
    shutouts: "SO",
  };
  return labels[stat] || "W";
}

function formatSavePct(value: number): string {
  if (value >= 1) return value.toFixed(3);
  return `.${(value * 1000).toFixed(0)}`;
}

// =============================================================================
// Exports
// =============================================================================

export { PlayerCardView as SkaterCard };
export { GoalieCardView as GoalieCard };
