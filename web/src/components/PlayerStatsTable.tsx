"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import type { SkaterCard, GoalieDetailCard } from "@/types/player";
import { TeamLogo } from "./TeamLogo";
import { getPlayerUrl, getGoalieUrl } from "@/lib/playerSlug";

// =============================================================================
// Player Avatar Component
// =============================================================================

function PlayerAvatar({ headshot, name, teamAbbrev, size = 32 }: {
  headshot: string | null;
  name: string;
  teamAbbrev: string;
  size?: number;
}) {
  const [imgError, setImgError] = useState(false);

  if (!headshot || imgError) {
    return (
      <div
        className="rounded-full bg-gradient-to-br from-white/[0.08] to-white/[0.02] flex items-center justify-center overflow-hidden border border-white/[0.08]"
        style={{ width: size, height: size }}
      >
        <TeamLogo teamAbbrev={teamAbbrev} size="xs" />
      </div>
    );
  }

  return (
    <div
      className="rounded-full bg-gradient-to-br from-white/[0.08] to-white/[0.02] overflow-hidden flex-shrink-0 border border-white/[0.08]"
      style={{ width: size, height: size }}
    >
      <Image
        src={headshot}
        alt={name}
        width={size}
        height={size}
        className="object-cover"
        onError={() => setImgError(true)}
        unoptimized
      />
    </div>
  );
}

// =============================================================================
// Premium Table Wrapper Component
// =============================================================================

function PremiumTableWrapper({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-white/[0.08] bg-gradient-to-b from-white/[0.03] to-transparent overflow-hidden">
      <div className="overflow-x-auto">
        {children}
      </div>
    </div>
  );
}

// =============================================================================
// Skater Stats Table
// =============================================================================

interface SkaterTableProps {
  players: SkaterCard[];
  showRank?: boolean;
  showTeam?: boolean;
  compact?: boolean;
  maxRows?: number;
  sortBy?: "points" | "goals" | "assists" | "plusMinus" | "shots" | "gamesPlayed";
  linkToProfile?: boolean;
}

export function SkaterStatsTable({
  players,
  showRank = true,
  showTeam = true,
  compact = false,
  maxRows,
  sortBy = "points",
  linkToProfile = true,
}: SkaterTableProps) {
  const sortedPlayers = [...players].sort((a, b) => {
    switch (sortBy) {
      case "goals":
        return b.stats.goals - a.stats.goals;
      case "assists":
        return b.stats.assists - a.stats.assists;
      case "plusMinus":
        return b.stats.plusMinus - a.stats.plusMinus;
      case "shots":
        return b.stats.shots - a.stats.shots;
      case "gamesPlayed":
        return b.stats.gamesPlayed - a.stats.gamesPlayed;
      default:
        return b.stats.points - a.stats.points;
    }
  });

  const displayPlayers = maxRows ? sortedPlayers.slice(0, maxRows) : sortedPlayers;

  return (
    <PremiumTableWrapper>
      <table className="w-full" style={{ minWidth: compact ? "650px" : "850px" }}>
        <thead>
          <tr className="text-left text-[10px] text-white/50 uppercase tracking-wider border-b border-white/[0.06]" style={{ background: "rgba(255,255,255,0.02)" }}>
            {showRank && (
              <th className="py-3 pl-4 pr-2 font-semibold w-12">#</th>
            )}
            <th className="py-3 px-3 font-semibold" style={{ minWidth: "180px" }}>Player</th>
            {showTeam && <th className="py-3 px-2 font-semibold">Team</th>}
            <th className="py-3 px-2 text-center font-semibold">POS</th>
            <th className="py-3 px-2 text-center font-semibold">GP</th>
            <th className="py-3 px-2 text-center font-semibold">G</th>
            <th className="py-3 px-2 text-center font-semibold">A</th>
            <th className="py-3 px-2 text-center font-semibold text-sky-400">PTS</th>
            <th className="py-3 px-2 text-center font-semibold">+/-</th>
            {!compact && (
              <>
                <th className="py-3 px-2 text-center font-semibold">PPG</th>
                <th className="py-3 px-2 text-center font-semibold">SOG</th>
                <th className="py-3 px-2 text-center font-semibold">S%</th>
                <th className="py-3 pr-4 pl-2 text-center font-semibold">TOI</th>
              </>
            )}
          </tr>
        </thead>
        <tbody>
          {displayPlayers.map((player, idx) => {
            const { bio, stats } = player;
            const isTopThree = idx < 3;
            const isEven = idx % 2 === 0;

            const row = (
              <tr
                key={bio.playerId}
                className={`
                  ${linkToProfile ? "hover:bg-white/[0.04] cursor-pointer" : ""}
                  ${isEven ? "bg-transparent" : "bg-white/[0.015]"}
                  transition-colors duration-150 border-b border-white/[0.03] last:border-b-0
                `}
              >
                {showRank && (
                  <td className="py-2.5 pl-4 pr-2">
                    <div className={`
                      w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold
                      ${isTopThree
                        ? "bg-gradient-to-br from-amber-400/20 to-amber-500/10 text-amber-400 border border-amber-400/20"
                        : "bg-white/[0.03] text-white/40 border border-white/[0.04]"
                      }
                    `}>
                      {idx + 1}
                    </div>
                  </td>
                )}
                <td className="py-2.5 px-3">
                  <div className="flex items-center gap-2.5">
                    <PlayerAvatar headshot={bio.headshot} name={bio.fullName} teamAbbrev={bio.teamAbbrev} size={32} />
                    <span className="font-medium text-white text-sm truncate">{bio.fullName}</span>
                  </div>
                </td>
                {showTeam && (
                  <td className="py-2.5 px-2">
                    <div className="flex items-center gap-2">
                      <TeamLogo teamAbbrev={bio.teamAbbrev} size="xs" />
                      <span className="text-xs font-medium text-white/60">{bio.teamAbbrev}</span>
                    </div>
                  </td>
                )}
                <td className="py-2.5 px-2 text-center">
                  <span className="text-[10px] font-medium text-white/50 bg-white/[0.05] px-2 py-1 rounded">{bio.position}</span>
                </td>
                <td className="py-2.5 px-2 text-center text-xs text-white/60 font-medium">{stats.gamesPlayed}</td>
                <td className="py-2.5 px-2 text-center text-xs text-white font-bold">{stats.goals}</td>
                <td className="py-2.5 px-2 text-center text-xs text-white font-bold">{stats.assists}</td>
                <td className="py-2.5 px-2 text-center">
                  <span className="text-xs font-bold text-sky-300 bg-sky-500/15 px-2 py-1 rounded border border-sky-400/20">{stats.points}</span>
                </td>
                <td className={`py-2.5 px-2 text-center text-xs font-bold ${stats.plusMinus > 0 ? "text-emerald-400" : stats.plusMinus < 0 ? "text-rose-400" : "text-white/50"}`}>
                  {stats.plusMinus > 0 ? `+${stats.plusMinus}` : stats.plusMinus}
                </td>
                {!compact && (
                  <>
                    <td className="py-2.5 px-2 text-center text-xs text-white/60">{stats.powerPlayGoals}</td>
                    <td className="py-2.5 px-2 text-center text-xs text-white/60">{stats.shots}</td>
                    <td className="py-2.5 px-2 text-center text-xs text-white/60">
                      {stats.shootingPct > 0 ? `${(stats.shootingPct * 100).toFixed(1)}%` : "—"}
                    </td>
                    <td className="py-2.5 pr-4 pl-2 text-center text-xs text-white/60">{stats.timeOnIcePerGame}</td>
                  </>
                )}
              </tr>
            );

            if (linkToProfile) {
              return (
                <Link key={bio.playerId} href={getPlayerUrl(bio.playerId, bio.fullName)} className="contents">
                  {row}
                </Link>
              );
            }
            return row;
          })}
        </tbody>
      </table>
    </PremiumTableWrapper>
  );
}

// =============================================================================
// Goalie Stats Table
// =============================================================================

interface GoalieTableProps {
  goalies: GoalieDetailCard[];
  showRank?: boolean;
  showTeam?: boolean;
  compact?: boolean;
  maxRows?: number;
  sortBy?: "wins" | "savePct" | "goalsAgainstAverage" | "shutouts" | "gamesPlayed";
  linkToProfile?: boolean;
}

export function GoalieStatsTable({
  goalies,
  showRank = true,
  showTeam = true,
  compact = false,
  maxRows,
  sortBy = "wins",
  linkToProfile = true,
}: GoalieTableProps) {
  const sortedGoalies = [...goalies].sort((a, b) => {
    switch (sortBy) {
      case "savePct":
        return b.stats.savePct - a.stats.savePct;
      case "goalsAgainstAverage":
        return a.stats.goalsAgainstAverage - b.stats.goalsAgainstAverage;
      case "shutouts":
        return b.stats.shutouts - a.stats.shutouts;
      case "gamesPlayed":
        return b.stats.gamesPlayed - a.stats.gamesPlayed;
      default:
        return b.stats.wins - a.stats.wins;
    }
  });

  const displayGoalies = maxRows ? sortedGoalies.slice(0, maxRows) : sortedGoalies;

  return (
    <PremiumTableWrapper>
      <table className="w-full" style={{ minWidth: compact ? "600px" : "800px" }}>
        <thead>
          <tr className="text-left text-[10px] text-white/50 uppercase tracking-wider border-b border-white/[0.06]" style={{ background: "rgba(255,255,255,0.02)" }}>
            {showRank && (
              <th className="py-3 pl-4 pr-2 font-semibold w-12">#</th>
            )}
            <th className="py-3 px-3 font-semibold" style={{ minWidth: "160px" }}>Goalie</th>
            {showTeam && <th className="py-3 px-2 font-semibold">Team</th>}
            <th className="py-3 px-2 text-center font-semibold">GP</th>
            <th className="py-3 px-2 text-center font-semibold">GS</th>
            <th className="py-3 px-2 text-center font-semibold text-emerald-400">W</th>
            <th className="py-3 px-2 text-center font-semibold">L</th>
            <th className="py-3 px-2 text-center font-semibold">OT</th>
            <th className="py-3 px-2 text-center font-semibold text-sky-400">SV%</th>
            <th className="py-3 px-2 text-center font-semibold text-amber-400">GAA</th>
            {!compact && (
              <>
                <th className="py-3 px-2 text-center font-semibold">SO</th>
                <th className="py-3 px-2 text-center font-semibold">SA</th>
                <th className="py-3 pr-4 pl-2 text-center font-semibold">SV</th>
              </>
            )}
          </tr>
        </thead>
        <tbody>
          {displayGoalies.map((goalie, idx) => {
            const { bio, stats } = goalie;
            const isTopThree = idx < 3;
            const isEven = idx % 2 === 0;

            const row = (
              <tr
                key={bio.playerId}
                className={`
                  ${linkToProfile ? "hover:bg-white/[0.04] cursor-pointer" : ""}
                  ${isEven ? "bg-transparent" : "bg-white/[0.015]"}
                  transition-colors duration-150 border-b border-white/[0.03] last:border-b-0
                `}
              >
                {showRank && (
                  <td className="py-2.5 pl-4 pr-2">
                    <div className={`
                      w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold
                      ${isTopThree
                        ? "bg-gradient-to-br from-amber-400/20 to-amber-500/10 text-amber-400 border border-amber-400/20"
                        : "bg-white/[0.03] text-white/40 border border-white/[0.04]"
                      }
                    `}>
                      {idx + 1}
                    </div>
                  </td>
                )}
                <td className="py-2.5 px-3">
                  <div className="flex items-center gap-2.5">
                    <PlayerAvatar headshot={bio.headshot} name={bio.fullName} teamAbbrev={bio.teamAbbrev} size={32} />
                    <span className="font-medium text-white text-sm truncate">{bio.fullName}</span>
                  </div>
                </td>
                {showTeam && (
                  <td className="py-2.5 px-2">
                    <div className="flex items-center gap-2">
                      <TeamLogo teamAbbrev={bio.teamAbbrev} size="xs" />
                      <span className="text-xs font-medium text-white/60">{bio.teamAbbrev}</span>
                    </div>
                  </td>
                )}
                <td className="py-2.5 px-2 text-center text-xs text-white/60 font-medium">{stats.gamesPlayed}</td>
                <td className="py-2.5 px-2 text-center text-xs text-white/60">{stats.gamesStarted}</td>
                <td className="py-2.5 px-2 text-center">
                  <span className="text-xs font-bold text-emerald-400 bg-emerald-500/15 px-2 py-1 rounded border border-emerald-400/20">{stats.wins}</span>
                </td>
                <td className="py-2.5 px-2 text-center text-xs text-white/60">{stats.losses}</td>
                <td className="py-2.5 px-2 text-center text-xs text-white/60">{stats.otLosses}</td>
                <td className="py-2.5 px-2 text-center">
                  <span className="text-xs font-bold text-sky-300 bg-sky-500/15 px-2 py-1 rounded border border-sky-400/20">
                    {formatSavePct(stats.savePct)}
                  </span>
                </td>
                <td className={`py-2.5 px-2 text-center text-xs font-bold ${stats.goalsAgainstAverage < 2.5 ? "text-emerald-400" : stats.goalsAgainstAverage > 3.2 ? "text-rose-400" : "text-amber-400"}`}>
                  {stats.goalsAgainstAverage.toFixed(2)}
                </td>
                {!compact && (
                  <>
                    <td className="py-2.5 px-2 text-center text-xs text-white font-semibold">{stats.shutouts}</td>
                    <td className="py-2.5 px-2 text-center text-xs text-white/60">{stats.shotsAgainst}</td>
                    <td className="py-2.5 pr-4 pl-2 text-center text-xs text-white/60">{stats.saves}</td>
                  </>
                )}
              </tr>
            );

            if (linkToProfile) {
              return (
                <Link key={bio.playerId} href={getGoalieUrl(bio.playerId, bio.fullName)} className="contents">
                  {row}
                </Link>
              );
            }
            return row;
          })}
        </tbody>
      </table>
    </PremiumTableWrapper>
  );
}

// =============================================================================
// Leader Card Grid Component
// =============================================================================

interface LeaderSectionProps {
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
}

export function LeaderSection({ title, icon, children }: LeaderSectionProps) {
  return (
    <section className="mb-8">
      <div className="flex items-center gap-2 mb-4">
        {icon && <span className="text-sky-400">{icon}</span>}
        <h2 className="text-xl font-bold text-white">{title}</h2>
      </div>
      {children}
    </section>
  );
}

// =============================================================================
// Compact Leader Row Component
// =============================================================================

interface LeaderRowProps {
  rank: number;
  name: string;
  fullName?: string; // Full name for slug generation (optional for backwards compatibility)
  team: string;
  value: string | number;
  playerId: number;
  headshot?: string | null;
  isGoalie?: boolean;
}

export function LeaderRow({ rank, name, fullName, team, value, playerId, headshot, isGoalie = false }: LeaderRowProps) {
  // Use fullName if provided, otherwise fall back to name for slug generation
  const playerName = fullName || name;
  const href = isGoalie ? getGoalieUrl(playerId, playerName) : getPlayerUrl(playerId, playerName);

  return (
    <Link href={href} className="block">
      <div className="flex items-center gap-3 py-2.5 px-3 rounded-lg hover:bg-white/[0.06] transition-colors cursor-pointer">
        <span className={`w-5 text-xs font-bold ${rank <= 3 ? "text-amber-400" : "text-white/40"}`}>
          {rank}
        </span>
        <PlayerAvatar headshot={headshot || null} name={name} teamAbbrev={team} size={28} />
        <span className="flex-1 text-sm font-medium text-white truncate">{name}</span>
        <span className="text-base font-bold text-sky-300">{value}</span>
      </div>
    </Link>
  );
}

// =============================================================================
// Helper Functions
// =============================================================================

function formatSavePct(value: number): string {
  if (value > 1) {
    return `.${Math.round(value * 10)}`;
  }
  return `.${Math.round(value * 1000)}`;
}
