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
        className="rounded-full bg-gradient-to-br from-white/[0.08] to-white/[0.02] flex items-center justify-center overflow-hidden border border-white/[0.06]"
        style={{ width: size, height: size }}
      >
        <TeamLogo teamAbbrev={teamAbbrev} size="xs" />
      </div>
    );
  }

  return (
    <div
      className="rounded-full bg-gradient-to-br from-white/[0.08] to-white/[0.02] overflow-hidden flex-shrink-0 border border-white/[0.06]"
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
          <tr className="text-left text-[11px] text-white/40 uppercase tracking-wider bg-white/[0.02]">
            {showRank && <th className="py-3.5 px-3 w-10 font-medium">#</th>}
            <th className="py-3.5 px-3 font-medium">Player</th>
            {showTeam && <th className="py-3.5 px-3 w-16 font-medium">Team</th>}
            <th className="py-3.5 px-3 w-12 text-center font-medium">Pos</th>
            <th className="py-3.5 px-3 w-12 text-center font-medium">GP</th>
            <th className="py-3.5 px-3 w-12 text-center font-medium">G</th>
            <th className="py-3.5 px-3 w-12 text-center font-medium">A</th>
            <th className="py-3.5 px-3 w-12 text-center font-semibold text-sky-400/70">PTS</th>
            <th className="py-3.5 px-3 w-14 text-center font-medium">+/-</th>
            {!compact && (
              <>
                <th className="py-3.5 px-3 w-12 text-center font-medium">PPG</th>
                <th className="py-3.5 px-3 w-12 text-center font-medium">SOG</th>
                <th className="py-3.5 px-3 w-14 text-center font-medium">S%</th>
                <th className="py-3.5 px-3 w-16 text-center font-medium">TOI/G</th>
              </>
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-white/[0.04]">
          {displayPlayers.map((player, idx) => {
            const { bio, stats } = player;
            const isTopThree = idx < 3;
            const row = (
              <tr
                key={bio.playerId}
                className={`${linkToProfile ? "hover:bg-white/[0.04] cursor-pointer transition-all duration-150" : ""} ${idx % 2 === 0 ? "bg-transparent" : "bg-white/[0.01]"}`}
              >
                {showRank && (
                  <td className="py-3 px-3">
                    <span className={`text-sm font-semibold ${isTopThree ? "text-amber-400" : "text-white/40"}`}>
                      {idx + 1}
                    </span>
                  </td>
                )}
                <td className="py-3 px-3">
                  <div className="flex items-center gap-3">
                    <PlayerAvatar headshot={bio.headshot} name={bio.fullName} teamAbbrev={bio.teamAbbrev} size={36} />
                    <div className="flex flex-col">
                      <span className="font-semibold text-white text-sm leading-tight">{bio.fullName}</span>
                      {bio.jerseyNumber && (
                        <span className="text-[10px] text-white/35 mt-0.5">#{bio.jerseyNumber}</span>
                      )}
                    </div>
                  </div>
                </td>
                {showTeam && (
                  <td className="py-3 px-3">
                    <div className="flex items-center gap-2">
                      <TeamLogo teamAbbrev={bio.teamAbbrev} size="xs" />
                      <span className="text-xs font-medium text-white/50">{bio.teamAbbrev}</span>
                    </div>
                  </td>
                )}
                <td className="py-3 px-3 text-center">
                  <span className="text-xs font-medium text-white/50 bg-white/[0.04] px-2 py-0.5 rounded">{bio.position}</span>
                </td>
                <td className="py-3 px-3 text-center text-sm text-white/60 font-medium">{stats.gamesPlayed}</td>
                <td className="py-3 px-3 text-center text-sm text-white font-semibold">{stats.goals}</td>
                <td className="py-3 px-3 text-center text-sm text-white font-semibold">{stats.assists}</td>
                <td className="py-3 px-3 text-center">
                  <span className="text-sm font-bold text-sky-300 bg-sky-400/10 px-2 py-0.5 rounded">{stats.points}</span>
                </td>
                <td className={`py-3 px-3 text-center text-sm font-semibold ${stats.plusMinus > 0 ? "text-emerald-400" : stats.plusMinus < 0 ? "text-rose-400" : "text-white/50"}`}>
                  {stats.plusMinus > 0 ? `+${stats.plusMinus}` : stats.plusMinus}
                </td>
                {!compact && (
                  <>
                    <td className="py-3 px-3 text-center text-sm text-white/60">{stats.powerPlayGoals}</td>
                    <td className="py-3 px-3 text-center text-sm text-white/60">{stats.shots}</td>
                    <td className="py-3 px-3 text-center text-sm text-white/60">
                      {stats.shootingPct > 0 ? `${(stats.shootingPct * 100).toFixed(1)}%` : "—"}
                    </td>
                    <td className="py-3 px-3 text-center text-sm text-white/60 font-medium">{stats.timeOnIcePerGame}</td>
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
          <tr className="text-left text-[11px] text-white/40 uppercase tracking-wider bg-white/[0.02]">
            {showRank && <th className="py-3.5 px-3 w-10 font-medium">#</th>}
            <th className="py-3.5 px-3 font-medium">Goalie</th>
            {showTeam && <th className="py-3.5 px-3 w-16 font-medium">Team</th>}
            <th className="py-3.5 px-3 w-12 text-center font-medium">GP</th>
            <th className="py-3.5 px-3 w-12 text-center font-medium">GS</th>
            <th className="py-3.5 px-3 w-12 text-center font-semibold text-emerald-400/70">W</th>
            <th className="py-3.5 px-3 w-10 text-center font-medium">L</th>
            <th className="py-3.5 px-3 w-12 text-center font-medium">OTL</th>
            <th className="py-3.5 px-3 w-14 text-center font-semibold text-sky-400/70">SV%</th>
            <th className="py-3.5 px-3 w-14 text-center font-semibold text-amber-400/70">GAA</th>
            {!compact && (
              <>
                <th className="py-3.5 px-3 w-10 text-center font-medium">SO</th>
                <th className="py-3.5 px-3 w-14 text-center font-medium">SA</th>
                <th className="py-3.5 px-3 w-14 text-center font-medium">SV</th>
              </>
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-white/[0.04]">
          {displayGoalies.map((goalie, idx) => {
            const { bio, stats } = goalie;
            const isTopThree = idx < 3;
            const row = (
              <tr
                key={bio.playerId}
                className={`${linkToProfile ? "hover:bg-white/[0.04] cursor-pointer transition-all duration-150" : ""} ${idx % 2 === 0 ? "bg-transparent" : "bg-white/[0.01]"}`}
              >
                {showRank && (
                  <td className="py-3 px-3">
                    <span className={`text-sm font-semibold ${isTopThree ? "text-amber-400" : "text-white/40"}`}>
                      {idx + 1}
                    </span>
                  </td>
                )}
                <td className="py-3 px-3">
                  <div className="flex items-center gap-3">
                    <PlayerAvatar headshot={bio.headshot} name={bio.fullName} teamAbbrev={bio.teamAbbrev} size={36} />
                    <div className="flex flex-col">
                      <span className="font-semibold text-white text-sm leading-tight">{bio.fullName}</span>
                      {bio.jerseyNumber && (
                        <span className="text-[10px] text-white/35 mt-0.5">#{bio.jerseyNumber}</span>
                      )}
                    </div>
                  </div>
                </td>
                {showTeam && (
                  <td className="py-3 px-3">
                    <div className="flex items-center gap-2">
                      <TeamLogo teamAbbrev={bio.teamAbbrev} size="xs" />
                      <span className="text-xs font-medium text-white/50">{bio.teamAbbrev}</span>
                    </div>
                  </td>
                )}
                <td className="py-3 px-3 text-center text-sm text-white/60 font-medium">{stats.gamesPlayed}</td>
                <td className="py-3 px-3 text-center text-sm text-white/60">{stats.gamesStarted}</td>
                <td className="py-3 px-3 text-center">
                  <span className="text-sm font-bold text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded">{stats.wins}</span>
                </td>
                <td className="py-3 px-3 text-center text-sm text-white/60">{stats.losses}</td>
                <td className="py-3 px-3 text-center text-sm text-white/60">{stats.otLosses}</td>
                <td className="py-3 px-3 text-center">
                  <span className="text-sm font-bold text-sky-300 bg-sky-400/10 px-2 py-0.5 rounded">
                    {formatSavePct(stats.savePct)}
                  </span>
                </td>
                <td className={`py-3 px-3 text-center text-sm font-semibold ${stats.goalsAgainstAverage < 2.5 ? "text-emerald-400" : stats.goalsAgainstAverage > 3.2 ? "text-rose-400" : "text-amber-400"}`}>
                  {stats.goalsAgainstAverage.toFixed(2)}
                </td>
                {!compact && (
                  <>
                    <td className="py-3 px-3 text-center text-sm text-white font-semibold">{stats.shutouts}</td>
                    <td className="py-3 px-3 text-center text-sm text-white/60">{stats.shotsAgainst}</td>
                    <td className="py-3 px-3 text-center text-sm text-white/60">{stats.saves}</td>
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
