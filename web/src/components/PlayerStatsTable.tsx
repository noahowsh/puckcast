"use client";

import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import type { SkaterCard, GoalieDetailCard } from "@/types/player";
import { TeamLogo } from "./TeamLogo";

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
    // Fallback to team logo
    return (
      <div
        className="rounded-full bg-white/[0.05] flex items-center justify-center overflow-hidden"
        style={{ width: size, height: size }}
      >
        <TeamLogo teamAbbrev={teamAbbrev} size="xs" />
      </div>
    );
  }

  return (
    <div
      className="rounded-full bg-white/[0.05] overflow-hidden flex-shrink-0"
      style={{ width: size, height: size }}
    >
      <Image
        src={headshot}
        alt={name}
        width={size}
        height={size}
        className="object-cover"
        onError={() => setImgError(true)}
      />
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
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="text-left text-xs text-white/50 uppercase tracking-wider border-b border-white/[0.06]">
            {showRank && <th className="py-3 px-2 w-10">#</th>}
            <th className="py-3 px-2">Player</th>
            {showTeam && <th className="py-3 px-2 w-16">Team</th>}
            <th className="py-3 px-2 w-10 text-center">Pos</th>
            <th className="py-3 px-2 w-12 text-center">GP</th>
            <th className="py-3 px-2 w-10 text-center">G</th>
            <th className="py-3 px-2 w-10 text-center">A</th>
            <th className="py-3 px-2 w-10 text-center font-semibold text-white/70">P</th>
            <th className="py-3 px-2 w-12 text-center">+/-</th>
            {!compact && (
              <>
                <th className="py-3 px-2 w-12 text-center">PPG</th>
                <th className="py-3 px-2 w-12 text-center">S</th>
                <th className="py-3 px-2 w-14 text-center">S%</th>
                <th className="py-3 px-2 w-14 text-center">TOI</th>
              </>
            )}
          </tr>
        </thead>
        <tbody>
          {displayPlayers.map((player, idx) => {
            const { bio, stats } = player;
            const row = (
              <tr
                key={bio.playerId}
                className={`border-b border-white/[0.04] ${linkToProfile ? "hover:bg-white/[0.03] cursor-pointer transition-colors" : ""}`}
              >
                {showRank && (
                  <td className="py-3 px-2 text-sm text-white/50 font-medium">{idx + 1}</td>
                )}
                <td className="py-3 px-2">
                  <div className="flex items-center gap-2.5">
                    <PlayerAvatar headshot={bio.headshot} name={bio.fullName} teamAbbrev={bio.teamAbbrev} size={28} />
                    <div className="flex flex-col">
                      <span className="font-medium text-white text-sm leading-tight">{bio.fullName}</span>
                      {bio.jerseyNumber && (
                        <span className="text-[10px] text-white/40">#{bio.jerseyNumber}</span>
                      )}
                    </div>
                  </div>
                </td>
                {showTeam && (
                  <td className="py-3 px-2">
                    <div className="flex items-center gap-1.5">
                      <TeamLogo teamAbbrev={bio.teamAbbrev} size="xs" />
                      <span className="text-xs text-white/60">{bio.teamAbbrev}</span>
                    </div>
                  </td>
                )}
                <td className="py-3 px-2 text-center">
                  <span className="text-xs text-white/60 font-medium">{bio.position}</span>
                </td>
                <td className="py-3 px-2 text-center text-sm text-white/70">{stats.gamesPlayed}</td>
                <td className="py-3 px-2 text-center text-sm text-white">{stats.goals}</td>
                <td className="py-3 px-2 text-center text-sm text-white">{stats.assists}</td>
                <td className="py-3 px-2 text-center text-sm font-semibold text-sky-300">{stats.points}</td>
                <td className={`py-3 px-2 text-center text-sm font-medium ${stats.plusMinus > 0 ? "text-emerald-400" : stats.plusMinus < 0 ? "text-rose-400" : "text-white/60"}`}>
                  {stats.plusMinus > 0 ? `+${stats.plusMinus}` : stats.plusMinus}
                </td>
                {!compact && (
                  <>
                    <td className="py-3 px-2 text-center text-sm text-white/70">{stats.powerPlayGoals}</td>
                    <td className="py-3 px-2 text-center text-sm text-white/70">{stats.shots}</td>
                    <td className="py-3 px-2 text-center text-sm text-white/70">
                      {stats.shootingPct > 0 ? `${(stats.shootingPct * 100).toFixed(1)}%` : "—"}
                    </td>
                    <td className="py-3 px-2 text-center text-sm text-white/70">{stats.timeOnIcePerGame}</td>
                  </>
                )}
              </tr>
            );

            if (linkToProfile) {
              return (
                <Link key={bio.playerId} href={`/players/${bio.playerId}`} className="contents">
                  {row}
                </Link>
              );
            }
            return row;
          })}
        </tbody>
      </table>
    </div>
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
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="text-left text-xs text-white/50 uppercase tracking-wider border-b border-white/[0.06]">
            {showRank && <th className="py-3 px-2 w-10">#</th>}
            <th className="py-3 px-2">Goalie</th>
            {showTeam && <th className="py-3 px-2 w-16">Team</th>}
            <th className="py-3 px-2 w-12 text-center">GP</th>
            <th className="py-3 px-2 w-12 text-center">GS</th>
            <th className="py-3 px-2 w-10 text-center font-semibold text-white/70">W</th>
            <th className="py-3 px-2 w-10 text-center">L</th>
            <th className="py-3 px-2 w-12 text-center">OTL</th>
            <th className="py-3 px-2 w-14 text-center font-semibold text-white/70">SV%</th>
            <th className="py-3 px-2 w-14 text-center">GAA</th>
            {!compact && (
              <>
                <th className="py-3 px-2 w-10 text-center">SO</th>
                <th className="py-3 px-2 w-14 text-center">SA</th>
                <th className="py-3 px-2 w-14 text-center">SV</th>
              </>
            )}
          </tr>
        </thead>
        <tbody>
          {displayGoalies.map((goalie, idx) => {
            const { bio, stats } = goalie;
            const row = (
              <tr
                key={bio.playerId}
                className={`border-b border-white/[0.04] ${linkToProfile ? "hover:bg-white/[0.03] cursor-pointer transition-colors" : ""}`}
              >
                {showRank && (
                  <td className="py-3 px-2 text-sm text-white/50 font-medium">{idx + 1}</td>
                )}
                <td className="py-3 px-2">
                  <div className="flex items-center gap-2.5">
                    <PlayerAvatar headshot={bio.headshot} name={bio.fullName} teamAbbrev={bio.teamAbbrev} size={28} />
                    <div className="flex flex-col">
                      <span className="font-medium text-white text-sm leading-tight">{bio.fullName}</span>
                      {bio.jerseyNumber && (
                        <span className="text-[10px] text-white/40">#{bio.jerseyNumber}</span>
                      )}
                    </div>
                  </div>
                </td>
                {showTeam && (
                  <td className="py-3 px-2">
                    <div className="flex items-center gap-1.5">
                      <TeamLogo teamAbbrev={bio.teamAbbrev} size="xs" />
                      <span className="text-xs text-white/60">{bio.teamAbbrev}</span>
                    </div>
                  </td>
                )}
                <td className="py-3 px-2 text-center text-sm text-white/70">{stats.gamesPlayed}</td>
                <td className="py-3 px-2 text-center text-sm text-white/70">{stats.gamesStarted}</td>
                <td className="py-3 px-2 text-center text-sm font-semibold text-emerald-400">{stats.wins}</td>
                <td className="py-3 px-2 text-center text-sm text-white/70">{stats.losses}</td>
                <td className="py-3 px-2 text-center text-sm text-white/70">{stats.otLosses}</td>
                <td className="py-3 px-2 text-center text-sm font-semibold text-sky-300">
                  {formatSavePct(stats.savePct)}
                </td>
                <td className={`py-3 px-2 text-center text-sm font-medium ${stats.goalsAgainstAverage < 2.5 ? "text-emerald-400" : stats.goalsAgainstAverage > 3.2 ? "text-rose-400" : "text-white"}`}>
                  {stats.goalsAgainstAverage.toFixed(2)}
                </td>
                {!compact && (
                  <>
                    <td className="py-3 px-2 text-center text-sm text-white">{stats.shutouts}</td>
                    <td className="py-3 px-2 text-center text-sm text-white/70">{stats.shotsAgainst}</td>
                    <td className="py-3 px-2 text-center text-sm text-white/70">{stats.saves}</td>
                  </>
                )}
              </tr>
            );

            if (linkToProfile) {
              return (
                <Link key={bio.playerId} href={`/goalies/${bio.playerId}`} className="contents">
                  {row}
                </Link>
              );
            }
            return row;
          })}
        </tbody>
      </table>
    </div>
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
  team: string;
  value: string | number;
  playerId: number;
  isGoalie?: boolean;
}

export function LeaderRow({ rank, name, team, value, playerId, isGoalie = false }: LeaderRowProps) {
  const href = isGoalie ? `/goalies/${playerId}` : `/players/${playerId}`;

  return (
    <Link href={href} className="block">
      <div className="flex items-center gap-3 py-2 px-3 rounded-lg hover:bg-white/[0.04] transition-colors cursor-pointer">
        <span className={`w-6 text-sm font-bold ${rank <= 3 ? "text-amber-400" : "text-white/40"}`}>
          {rank}
        </span>
        <TeamLogo teamAbbrev={team} size="xs" />
        <span className="flex-1 text-sm font-medium text-white truncate">{name}</span>
        <span className="text-sm font-bold text-sky-300">{value}</span>
      </div>
    </Link>
  );
}

// =============================================================================
// Helper Functions
// =============================================================================

function formatSavePct(value: number): string {
  // Handle percentages that might come as decimals (0.915) or whole numbers (91.5)
  if (value > 1) {
    // Already a percentage like 91.5
    return `.${Math.round(value * 10)}`;
  }
  // Decimal like 0.915
  return `.${Math.round(value * 1000)}`;
}
