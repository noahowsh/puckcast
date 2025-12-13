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
    <div className="rounded-xl border border-white/[0.08] bg-gradient-to-b from-white/[0.02] to-transparent overflow-hidden">
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        padding: '0.6rem 1rem',
        background: 'rgba(255,255,255,0.02)',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
        gap: '0.25rem',
      }}>
        {showRank && <span style={{ width: '28px', fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>#</span>}
        <span style={{ flex: 1, minWidth: '140px', fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>Player</span>
        {showTeam && <span style={{ width: '48px', fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, textAlign: 'center' }}>Team</span>}
        <span style={{ width: '32px', fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, textAlign: 'center' }}>GP</span>
        <span style={{ width: '32px', fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, textAlign: 'center' }}>G</span>
        <span style={{ width: '32px', fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, textAlign: 'center' }}>A</span>
        <span style={{ width: '36px', fontSize: '0.6rem', color: 'var(--aqua)', textTransform: 'uppercase', fontWeight: 600, textAlign: 'center' }}>PTS</span>
        <span style={{ width: '36px', fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, textAlign: 'center' }}>+/-</span>
        {!compact && (
          <>
            <span style={{ width: '32px', fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, textAlign: 'center' }}>PPG</span>
            <span style={{ width: '36px', fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, textAlign: 'center' }}>SOG</span>
          </>
        )}
      </div>

      {/* Rows */}
      {displayPlayers.map((player, idx) => {
        const { bio, stats } = player;
        const isTopThree = idx < 3;
        const isEven = idx % 2 === 0;

        const rowContent = (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '0.5rem 1rem',
              background: isEven ? 'transparent' : 'rgba(255,255,255,0.015)',
              borderBottom: '1px solid rgba(255,255,255,0.03)',
              gap: '0.25rem',
              transition: 'background 0.15s ease',
            }}
            className={linkToProfile ? "hover:bg-[rgba(126,227,255,0.08)] cursor-pointer" : ""}
          >
            {showRank && (
              <span style={{
                width: '28px',
                fontSize: '0.8rem',
                fontWeight: 600,
                color: isTopThree ? '#fbbf24' : 'var(--text-tertiary)',
              }}>{idx + 1}</span>
            )}
            <div style={{ flex: 1, minWidth: '140px', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <PlayerAvatar headshot={bio.headshot} name={bio.fullName} teamAbbrev={bio.teamAbbrev} size={28} />
              <span style={{ fontSize: '0.85rem', fontWeight: 500, color: 'white', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{bio.fullName}</span>
            </div>
            {showTeam && (
              <div style={{ width: '48px', display: 'flex', justifyContent: 'center' }}>
                <TeamLogo teamAbbrev={bio.teamAbbrev} size="xs" />
              </div>
            )}
            <span style={{ width: '32px', fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500, textAlign: 'center' }}>{stats.gamesPlayed}</span>
            <span style={{ width: '32px', fontSize: '0.8rem', color: '#10b981', fontWeight: 700, textAlign: 'center' }}>{stats.goals}</span>
            <span style={{ width: '32px', fontSize: '0.8rem', color: 'white', fontWeight: 600, textAlign: 'center' }}>{stats.assists}</span>
            <span style={{ width: '36px', fontSize: '0.85rem', color: 'var(--aqua)', fontWeight: 700, textAlign: 'center' }}>{stats.points}</span>
            <span style={{
              width: '36px',
              fontSize: '0.8rem',
              fontWeight: 600,
              textAlign: 'center',
              color: stats.plusMinus > 0 ? '#10b981' : stats.plusMinus < 0 ? '#ef4444' : 'var(--text-tertiary)',
            }}>{stats.plusMinus > 0 ? `+${stats.plusMinus}` : stats.plusMinus}</span>
            {!compact && (
              <>
                <span style={{ width: '32px', fontSize: '0.8rem', color: 'var(--text-secondary)', textAlign: 'center' }}>{stats.powerPlayGoals}</span>
                <span style={{ width: '36px', fontSize: '0.8rem', color: 'var(--text-secondary)', textAlign: 'center' }}>{stats.shots}</span>
              </>
            )}
          </div>
        );

        if (linkToProfile) {
          return (
            <Link key={bio.playerId} href={getPlayerUrl(bio.playerId, bio.fullName)} style={{ display: 'block', textDecoration: 'none' }}>
              {rowContent}
            </Link>
          );
        }
        return <div key={bio.playerId}>{rowContent}</div>;
      })}
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
    <div className="rounded-xl border border-white/[0.08] bg-gradient-to-b from-white/[0.02] to-transparent overflow-hidden">
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        padding: '0.6rem 1rem',
        background: 'rgba(255,255,255,0.02)',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
        gap: '0.25rem',
      }}>
        {showRank && <span style={{ width: '28px', fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>#</span>}
        <span style={{ flex: 1, minWidth: '140px', fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>Goalie</span>
        {showTeam && <span style={{ width: '48px', fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, textAlign: 'center' }}>Team</span>}
        <span style={{ width: '32px', fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, textAlign: 'center' }}>GP</span>
        <span style={{ width: '32px', fontSize: '0.6rem', color: '#10b981', textTransform: 'uppercase', fontWeight: 600, textAlign: 'center' }}>W</span>
        <span style={{ width: '28px', fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, textAlign: 'center' }}>L</span>
        <span style={{ width: '44px', fontSize: '0.6rem', color: 'var(--aqua)', textTransform: 'uppercase', fontWeight: 600, textAlign: 'center' }}>SV%</span>
        <span style={{ width: '40px', fontSize: '0.6rem', color: '#fbbf24', textTransform: 'uppercase', fontWeight: 600, textAlign: 'center' }}>GAA</span>
        {!compact && (
          <span style={{ width: '28px', fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, textAlign: 'center' }}>SO</span>
        )}
      </div>

      {/* Rows */}
      {displayGoalies.map((goalie, idx) => {
        const { bio, stats } = goalie;
        const isTopThree = idx < 3;
        const isEven = idx % 2 === 0;

        const rowContent = (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '0.5rem 1rem',
              background: isEven ? 'transparent' : 'rgba(255,255,255,0.015)',
              borderBottom: '1px solid rgba(255,255,255,0.03)',
              gap: '0.25rem',
              transition: 'background 0.15s ease',
            }}
            className={linkToProfile ? "hover:bg-[rgba(126,227,255,0.08)] cursor-pointer" : ""}
          >
            {showRank && (
              <span style={{
                width: '28px',
                fontSize: '0.8rem',
                fontWeight: 600,
                color: isTopThree ? '#fbbf24' : 'var(--text-tertiary)',
              }}>{idx + 1}</span>
            )}
            <div style={{ flex: 1, minWidth: '140px', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <PlayerAvatar headshot={bio.headshot} name={bio.fullName} teamAbbrev={bio.teamAbbrev} size={28} />
              <span style={{ fontSize: '0.85rem', fontWeight: 500, color: 'white', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{bio.fullName}</span>
            </div>
            {showTeam && (
              <div style={{ width: '48px', display: 'flex', justifyContent: 'center' }}>
                <TeamLogo teamAbbrev={bio.teamAbbrev} size="xs" />
              </div>
            )}
            <span style={{ width: '32px', fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500, textAlign: 'center' }}>{stats.gamesPlayed}</span>
            <span style={{ width: '32px', fontSize: '0.8rem', color: '#10b981', fontWeight: 700, textAlign: 'center' }}>{stats.wins}</span>
            <span style={{ width: '28px', fontSize: '0.8rem', color: '#ef4444', fontWeight: 600, textAlign: 'center' }}>{stats.losses}</span>
            <span style={{ width: '44px', fontSize: '0.8rem', color: 'var(--aqua)', fontWeight: 600, textAlign: 'center' }}>{formatSavePct(stats.savePct)}</span>
            <span style={{
              width: '40px',
              fontSize: '0.8rem',
              fontWeight: 600,
              textAlign: 'center',
              color: stats.goalsAgainstAverage < 2.5 ? '#10b981' : stats.goalsAgainstAverage > 3.2 ? '#ef4444' : '#fbbf24',
            }}>{stats.goalsAgainstAverage.toFixed(2)}</span>
            {!compact && (
              <span style={{ width: '28px', fontSize: '0.8rem', color: 'white', fontWeight: 600, textAlign: 'center' }}>{stats.shutouts}</span>
            )}
          </div>
        );

        if (linkToProfile) {
          return (
            <Link key={bio.playerId} href={getGoalieUrl(bio.playerId, bio.fullName)} style={{ display: 'block', textDecoration: 'none' }}>
              {rowContent}
            </Link>
          );
        }
        return <div key={bio.playerId}>{rowContent}</div>;
      })}
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
