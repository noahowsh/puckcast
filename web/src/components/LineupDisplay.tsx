"use client";

// Lineup Display Components
// Visual components for showing projected lineups and strength metrics

import { useState } from "react";
import Link from "next/link";
import { TeamCrest } from "./TeamCrest";
import type { TeamLineup, LineupPlayer, GoalieLineup, LineupStrengthMetrics } from "@/types/lineup";
import { getPlayerUrl, getGoalieUrl } from "@/lib/playerSlug";

// =============================================================================
// Strength Meter Component
// =============================================================================

function StrengthMeter({ label, value, maxValue = 100, color }: {
  label: string;
  value: number;
  maxValue?: number;
  color?: string;
}) {
  const percentage = Math.min(100, (value / maxValue) * 100);
  const displayColor = color || getStrengthColor(value);

  return (
    <div style={{ marginBottom: '0.75rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
        <span style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>{label}</span>
        <span style={{ fontSize: '0.85rem', fontWeight: 600, color: displayColor }}>{Math.round(value)}</span>
      </div>
      <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
        <div style={{
          height: '100%',
          width: `${percentage}%`,
          background: displayColor,
          borderRadius: '3px',
          transition: 'width 0.3s ease',
        }} />
      </div>
    </div>
  );
}

function getStrengthColor(value: number): string {
  if (value >= 75) return '#10b981';
  if (value >= 50) return '#3b82f6';
  if (value >= 25) return '#f59e0b';
  return '#ef4444';
}

// =============================================================================
// Lineup Strength Card
// =============================================================================

export function LineupStrengthCard({ strength }: { strength: LineupStrengthMetrics }) {
  return (
    <div className="card" style={{ padding: '1.25rem' }}>
      <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'white', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{
          width: '32px',
          height: '32px',
          borderRadius: '8px',
          background: 'rgba(59,130,246,0.2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <svg className="w-4 h-4 text-sky-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
          </svg>
        </span>
        Lineup Strength
      </h3>

      {/* Overall Quality Ring */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', marginBottom: '1.25rem' }}>
        <div style={{ position: 'relative', width: '80px', height: '80px' }}>
          <svg width="80" height="80" viewBox="0 0 80 80" style={{ transform: 'rotate(-90deg)' }}>
            <circle cx="40" cy="40" r="32" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="8" />
            <circle
              cx="40" cy="40" r="32"
              fill="none"
              stroke={getStrengthColor(strength.overallQuality)}
              strokeWidth="8"
              strokeDasharray={`${(strength.overallQuality / 100) * 201} 201`}
              strokeLinecap="round"
            />
          </svg>
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            textAlign: 'center',
          }}>
            <p style={{ fontSize: '1.5rem', fontWeight: 800, color: getStrengthColor(strength.overallQuality), lineHeight: 1 }}>
              {strength.overallQuality}
            </p>
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>Overall Quality</p>
          <p style={{ fontSize: '1rem', fontWeight: 600, color: 'white' }}>
            {strength.percentOfFullStrength}% Full Strength
          </p>
          {strength.injuryImpact < 0 && (
            <p style={{ fontSize: '0.8rem', color: '#f59e0b', marginTop: '0.25rem' }}>
              -{Math.abs(strength.injuryImpact)} injury impact
            </p>
          )}
        </div>
      </div>

      {/* Strength Breakdown */}
      <StrengthMeter label="Offensive Strength" value={strength.offensiveStrength} />
      <StrengthMeter label="Defensive Strength" value={strength.defensiveStrength} />
      <StrengthMeter label="Goaltending" value={strength.goalieStrength} />

      {/* Quick Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', marginTop: '1rem' }}>
        <div style={{ padding: '0.5rem', background: 'rgba(255,255,255,0.03)', borderRadius: '0.5rem', textAlign: 'center' }}>
          <p style={{ fontSize: '1rem', fontWeight: 700, color: 'white' }}>{strength.topLineStrength}</p>
          <p style={{ fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Top Line</p>
        </div>
        <div style={{ padding: '0.5rem', background: 'rgba(255,255,255,0.03)', borderRadius: '0.5rem', textAlign: 'center' }}>
          <p style={{ fontSize: '1rem', fontWeight: 700, color: 'white' }}>{strength.topPairStrength}</p>
          <p style={{ fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Top Pair</p>
        </div>
        <div style={{ padding: '0.5rem', background: 'rgba(255,255,255,0.03)', borderRadius: '0.5rem', textAlign: 'center' }}>
          <p style={{ fontSize: '1rem', fontWeight: 700, color: 'white' }}>{strength.starterRating}</p>
          <p style={{ fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Starter</p>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// OVR Rating Legend Component
// =============================================================================

function OvrRatingLegend() {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '1rem',
      padding: '0.5rem 1rem',
      background: 'rgba(255,255,255,0.02)',
      borderRadius: '0.5rem',
      marginBottom: '1rem',
      flexWrap: 'wrap',
    }}>
      <span style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
        OVR Rating:
      </span>
      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <div style={{ width: '12px', height: '12px', borderRadius: '2px', background: '#10b981' }} />
          <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>Elite (75+)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <div style={{ width: '12px', height: '12px', borderRadius: '2px', background: '#3b82f6' }} />
          <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>Above Avg (50-74)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <div style={{ width: '12px', height: '12px', borderRadius: '2px', background: '#f59e0b' }} />
          <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>Average (25-49)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <div style={{ width: '12px', height: '12px', borderRadius: '2px', background: '#ef4444' }} />
          <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>Below Avg (&lt;25)</span>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Player Row Components
// =============================================================================

// Helper to get player headshot URL
function getHeadshotUrl(playerId: number, teamAbbrev?: string): string {
  // NHL headshot URL format - uses current season (2025-26)
  const season = "20252026";
  return `https://assets.nhle.com/mugs/nhl/${season}/${teamAbbrev || 'NHL'}/${playerId}.png`;
}

// Fallback headshot component with initials and proper loading state
function PlayerHeadshot({ playerId, playerName, teamAbbrev, size = 40 }: {
  playerId: number;
  playerName: string;
  teamAbbrev?: string;
  size?: number;
}) {
  const [hasError, setHasError] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);
  const initials = playerName.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();

  return (
    <div style={{
      width: size,
      height: size,
      borderRadius: '50%',
      overflow: 'hidden',
      background: 'linear-gradient(135deg, rgba(59,130,246,0.3), rgba(16,185,129,0.3))',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexShrink: 0,
      position: 'relative',
    }}>
      {/* Show initials as fallback or while loading */}
      {(hasError || !isLoaded) && (
        <span style={{
          fontSize: `${size * 0.35}px`,
          fontWeight: 700,
          color: 'rgba(255,255,255,0.7)',
        }}>
          {initials}
        </span>
      )}
      {/* Only render image if no error */}
      {!hasError && (
        <img
          src={getHeadshotUrl(playerId, teamAbbrev)}
          alt={playerName}
          width={size}
          height={size}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            opacity: isLoaded ? 1 : 0,
            position: 'absolute',
            top: 0,
            left: 0,
          }}
          onLoad={() => setIsLoaded(true)}
          onError={() => setHasError(true)}
        />
      )}
    </div>
  );
}

function PlayerRow({ player, rank, showRankingScore = true, teamAbbrev }: {
  player: LineupPlayer;
  rank: number;
  showRankingScore?: boolean;
  teamAbbrev?: string;
}) {
  const isOut = !player.isHealthy;
  const isDTD = player.isHealthy && player.injuryStatus &&
    ['dtd', 'gtd', 'questionable', 'probable', 'day-to-day'].includes(player.injuryStatus.toLowerCase());
  const hasInjuryStatus = player.injuryStatus !== null;

  return (
    <Link
      href={getPlayerUrl(player.playerId, player.playerName)}
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: '0.75rem 1rem',
        background: rank % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'transparent',
        opacity: isOut ? 0.5 : 1,
        textDecoration: 'none',
        transition: 'all 0.15s ease',
        cursor: 'pointer',
        borderLeft: isDTD ? '3px solid #f59e0b' : isOut ? '3px solid #ef4444' : '3px solid transparent',
      }}
      className="hover:bg-white/[0.08] hover:border-l-sky-500"
    >
      <span style={{
        width: '28px',
        fontSize: '0.85rem',
        fontWeight: 600,
        color: rank <= 3 ? '#10b981' : 'var(--text-tertiary)',
      }}>{rank}</span>

      {/* Headshot */}
      <div style={{ marginRight: '0.75rem' }}>
        <PlayerHeadshot
          playerId={player.playerId}
          playerName={player.playerName}
          teamAbbrev={teamAbbrev}
          size={36}
        />
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.9rem', color: 'white', fontWeight: 500 }}>
            {player.playerName}
          </span>
          <span style={{
            fontSize: '0.7rem',
            color: 'var(--text-tertiary)',
            fontFamily: 'monospace',
          }}>#{player.jerseyNumber || '—'}</span>
          {hasInjuryStatus && (
            <span style={{
              fontSize: '0.6rem',
              color: isDTD ? '#f59e0b' : '#ef4444',
              fontWeight: 600,
              background: isDTD ? 'rgba(245,158,11,0.15)' : 'rgba(239,68,68,0.15)',
              padding: '0.1rem 0.35rem',
              borderRadius: '3px',
            }}>{player.injuryStatus}</span>
          )}
        </div>
        <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', marginTop: '0.15rem' }}>
          {player.position} • {player.gamesPlayed} GP
        </div>
      </div>

      {/* Stats columns - fixed width for proper alignment */}
      <div style={{ display: 'flex', gap: '0.25rem', alignItems: 'center' }}>
        <div style={{ width: '32px', textAlign: 'center' }}>
          <span style={{ fontSize: '0.8rem', color: 'white', fontWeight: 600, display: 'block' }}>{player.gamesPlayed}</span>
        </div>
        <div style={{ width: '32px', textAlign: 'center' }}>
          <span style={{ fontSize: '0.8rem', color: '#10b981', fontWeight: 700, display: 'block' }}>{player.goals}</span>
        </div>
        <div style={{ width: '32px', textAlign: 'center' }}>
          <span style={{ fontSize: '0.8rem', color: '#3b82f6', fontWeight: 700, display: 'block' }}>{player.assists}</span>
        </div>
        <div style={{ width: '32px', textAlign: 'center' }}>
          <span style={{ fontSize: '0.8rem', color: 'white', fontWeight: 700, display: 'block' }}>{player.points}</span>
        </div>
        <div style={{ width: '36px', textAlign: 'center' }}>
          <span style={{
            fontSize: '0.8rem',
            color: player.plusMinus >= 0 ? '#10b981' : '#ef4444',
            fontWeight: 600,
            display: 'block',
          }}>{player.plusMinus >= 0 ? '+' : ''}{player.plusMinus}</span>
        </div>
        <div style={{ width: '36px', textAlign: 'center' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600, display: 'block' }}>
            {player.shootingPct ? (player.shootingPct * 100).toFixed(1) : '0.0'}
          </span>
        </div>
        <div style={{ width: '32px', textAlign: 'center' }}>
          <span style={{ fontSize: '0.8rem', color: '#a855f7', fontWeight: 700, display: 'block' }}>{player.powerPlayGoals}</span>
        </div>
        {showRankingScore && (
          <div style={{
            width: '40px',
            textAlign: 'center',
            padding: '0.1rem 0.2rem',
            background: `rgba(${player.rankingScore >= 75 ? '16,185,129' : player.rankingScore >= 50 ? '59,130,246' : player.rankingScore >= 25 ? '245,158,11' : '239,68,68'}, 0.15)`,
            borderRadius: '4px',
          }}>
            <span style={{
              fontSize: '0.8rem',
              color: getStrengthColor(player.rankingScore),
              fontWeight: 700,
              display: 'block',
            }}>{player.rankingScore}</span>
          </div>
        )}
      </div>
    </Link>
  );
}

function GoalieRow({ goalie, rank, teamAbbrev }: { goalie: GoalieLineup; rank: number; teamAbbrev?: string }) {
  const isInjured = !goalie.isHealthy;

  return (
    <Link
      href={getGoalieUrl(goalie.playerId, goalie.playerName)}
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: '0.75rem 1rem',
        background: rank % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'transparent',
        opacity: isInjured ? 0.5 : 1,
        textDecoration: 'none',
        transition: 'all 0.15s ease',
        cursor: 'pointer',
        borderLeft: '3px solid transparent',
      }}
      className="hover:bg-white/[0.08] hover:border-l-sky-500"
    >
      <span style={{
        width: '28px',
        fontSize: '0.85rem',
        fontWeight: 600,
        color: goalie.isProjectedStarter ? '#10b981' : 'var(--text-tertiary)',
      }}>{goalie.isProjectedStarter ? '★' : rank}</span>

      {/* Headshot */}
      <div style={{ marginRight: '0.75rem' }}>
        <PlayerHeadshot
          playerId={goalie.playerId}
          playerName={goalie.playerName}
          teamAbbrev={teamAbbrev}
          size={36}
        />
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.9rem', color: 'white', fontWeight: 500 }}>
            {goalie.playerName}
          </span>
          <span style={{
            fontSize: '0.7rem',
            color: 'var(--text-tertiary)',
            fontFamily: 'monospace',
          }}>#{goalie.jerseyNumber || '—'}</span>
          {goalie.isProjectedStarter && (
            <span style={{
              fontSize: '0.6rem',
              color: '#10b981',
              fontWeight: 600,
              background: 'rgba(16,185,129,0.15)',
              padding: '0.1rem 0.35rem',
              borderRadius: '3px',
            }}>STARTER</span>
          )}
          {isInjured && (
            <span style={{
              fontSize: '0.6rem',
              color: '#ef4444',
              fontWeight: 600,
              background: 'rgba(239,68,68,0.15)',
              padding: '0.1rem 0.35rem',
              borderRadius: '3px',
            }}>INJ</span>
          )}
        </div>
        <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', marginTop: '0.15rem' }}>
          {goalie.gamesPlayed} GP • {goalie.gamesStarted} GS
        </div>
      </div>

      {/* Stats columns - aligned with header */}
      <div style={{ display: 'flex', gap: '0.25rem', alignItems: 'center' }}>
        <div style={{ width: '36px', textAlign: 'center' }}>
          <span style={{ fontSize: '0.85rem', color: 'white', fontWeight: 600, display: 'block' }}>{goalie.gamesPlayed}</span>
        </div>
        <div style={{ width: '36px', textAlign: 'center' }}>
          <span style={{ fontSize: '0.85rem', color: '#10b981', fontWeight: 700, display: 'block' }}>{goalie.wins}</span>
        </div>
        <div style={{ width: '36px', textAlign: 'center' }}>
          <span style={{ fontSize: '0.85rem', color: '#ef4444', fontWeight: 600, display: 'block' }}>
            {goalie.gamesPlayed - goalie.wins}
          </span>
        </div>
        <div style={{ width: '48px', textAlign: 'center' }}>
          <span style={{ fontSize: '0.85rem', color: 'white', fontWeight: 600, display: 'block' }}>
            .{Math.round(goalie.savePct * 1000).toString().padStart(3, '0')}
          </span>
        </div>
        <div style={{ width: '48px', textAlign: 'center' }}>
          <span style={{
            fontSize: '0.85rem',
            color: goalie.goalsAgainstAverage <= 2.5 ? '#10b981' : goalie.goalsAgainstAverage <= 3.0 ? '#3b82f6' : '#f59e0b',
            fontWeight: 600,
            display: 'block',
          }}>
            {goalie.goalsAgainstAverage.toFixed(2)}
          </span>
        </div>
        <div style={{
          width: '44px',
          textAlign: 'center',
          padding: '0.15rem 0.25rem',
          background: `rgba(${goalie.rankingScore >= 75 ? '16,185,129' : goalie.rankingScore >= 50 ? '59,130,246' : goalie.rankingScore >= 25 ? '245,158,11' : '239,68,68'}, 0.15)`,
          borderRadius: '4px',
        }}>
          <span style={{
            fontSize: '0.85rem',
            color: getStrengthColor(goalie.rankingScore),
            fontWeight: 700,
            display: 'block',
          }}>{goalie.rankingScore}</span>
        </div>
      </div>
    </Link>
  );
}

// =============================================================================
// Main Lineup Display Component
// =============================================================================

export function ProjectedLineupDisplay({ lineup }: { lineup: TeamLineup }) {
  // Collect all players with injury status (both out and day-to-day)
  const allPlayersWithInjury = [
    ...lineup.forwards.filter(p => p.injuryStatus),
    ...lineup.defensemen.filter(p => p.injuryStatus),
    ...lineup.goalies.filter(g => !g.isHealthy),
  ];

  // Split into IR/OUT (definitely out) and DTD/GTD (uncertain)
  const outPlayers = allPlayersWithInjury.filter(p =>
    !p.isHealthy || ['IR', 'IR-LT', 'IR-NR', 'OUT', 'SUSPENDED', 'INJ'].includes((p as any).injuryStatus?.toUpperCase() || '')
  );
  const dtdPlayers = allPlayersWithInjury.filter(p =>
    p.isHealthy && ['dtd', 'gtd', 'questionable', 'probable', 'day-to-day'].includes((p as any).injuryStatus?.toLowerCase() || '')
  );

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1.5rem' }} className="lg:grid-cols-[1fr_2fr]">
      {/* Left Column: Strength Card */}
      <div>
        <LineupStrengthCard strength={lineup.lineupStrength} />
      </div>

      {/* Right Column: Roster Lists */}
      <div>
        {/* OVR Rating Legend */}
        <OvrRatingLegend />

        {/* Forwards */}
        <div className="card card-static" style={{ padding: 0, overflow: 'hidden', marginBottom: '1.5rem' }}>
          <div style={{ padding: '0.75rem 1rem', background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h4 style={{ fontSize: '0.8rem', fontWeight: 600, color: 'white', textTransform: 'uppercase' }}>
              Forwards ({lineup.forwards.length})
            </h4>
            <div style={{ display: 'flex', gap: '0.25rem', fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
              <span style={{ width: '32px', textAlign: 'center' }}>GP</span>
              <span style={{ width: '32px', textAlign: 'center' }}>G</span>
              <span style={{ width: '32px', textAlign: 'center' }}>A</span>
              <span style={{ width: '32px', textAlign: 'center' }}>PTS</span>
              <span style={{ width: '36px', textAlign: 'center' }}>+/-</span>
              <span style={{ width: '36px', textAlign: 'center' }}>S%</span>
              <span style={{ width: '32px', textAlign: 'center' }}>PPG</span>
              <span style={{ width: '40px', textAlign: 'center' }}>OVR</span>
            </div>
          </div>
          {lineup.forwards.map((player, idx) => (
            <PlayerRow key={player.playerId} player={player} rank={idx + 1} teamAbbrev={lineup.teamAbbrev} />
          ))}
        </div>

        {/* Defensemen */}
        <div className="card card-static" style={{ padding: 0, overflow: 'hidden', marginBottom: '1.5rem' }}>
          <div style={{ padding: '0.75rem 1rem', background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h4 style={{ fontSize: '0.8rem', fontWeight: 600, color: 'white', textTransform: 'uppercase' }}>
              Defensemen ({lineup.defensemen.length})
            </h4>
            <div style={{ display: 'flex', gap: '0.25rem', fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
              <span style={{ width: '32px', textAlign: 'center' }}>GP</span>
              <span style={{ width: '32px', textAlign: 'center' }}>G</span>
              <span style={{ width: '32px', textAlign: 'center' }}>A</span>
              <span style={{ width: '32px', textAlign: 'center' }}>PTS</span>
              <span style={{ width: '36px', textAlign: 'center' }}>+/-</span>
              <span style={{ width: '36px', textAlign: 'center' }}>S%</span>
              <span style={{ width: '32px', textAlign: 'center' }}>PPG</span>
              <span style={{ width: '40px', textAlign: 'center' }}>OVR</span>
            </div>
          </div>
          {lineup.defensemen.map((player, idx) => (
            <PlayerRow key={player.playerId} player={player} rank={idx + 1} teamAbbrev={lineup.teamAbbrev} />
          ))}
        </div>

        {/* Goalies */}
        <div className="card card-static" style={{ padding: 0, overflow: 'hidden', marginBottom: '1.5rem' }}>
          <div style={{ padding: '0.75rem 1rem', background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h4 style={{ fontSize: '0.8rem', fontWeight: 600, color: 'white', textTransform: 'uppercase' }}>
              Goalies ({lineup.goalies.length})
            </h4>
            <div style={{ display: 'flex', gap: '0.25rem', fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
              <span style={{ width: '36px', textAlign: 'center' }}>GP</span>
              <span style={{ width: '36px', textAlign: 'center' }}>W</span>
              <span style={{ width: '36px', textAlign: 'center' }}>L</span>
              <span style={{ width: '48px', textAlign: 'center' }}>SV%</span>
              <span style={{ width: '48px', textAlign: 'center' }}>GAA</span>
              <span style={{ width: '44px', textAlign: 'center' }}>OVR</span>
            </div>
          </div>
          {lineup.goalies.map((goalie, idx) => (
            <GoalieRow key={goalie.playerId} goalie={goalie} rank={idx + 1} teamAbbrev={lineup.teamAbbrev} />
          ))}
        </div>

        {/* IR/OUT Players */}
        {outPlayers.length > 0 && (
          <div className="card" style={{ padding: '1rem', borderLeft: '3px solid #ef4444', marginBottom: '1rem' }}>
            <h4 style={{ fontSize: '0.8rem', fontWeight: 600, color: '#ef4444', marginBottom: '0.75rem', textTransform: 'uppercase' }}>
              Injured Reserve / Out ({outPlayers.length})
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {outPlayers.map((player) => (
                <div key={player.playerId} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <PlayerHeadshot
                    playerId={player.playerId}
                    playerName={player.playerName}
                    teamAbbrev={lineup.teamAbbrev}
                    size={28}
                  />
                  <div style={{ flex: 1 }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{player.playerName}</span>
                    <span style={{
                      marginLeft: '0.5rem',
                      fontSize: '0.65rem',
                      fontWeight: 600,
                      color: ((player as any).injuryStatus === 'IR-LT') ? '#dc2626' : '#ef4444',
                      background: ((player as any).injuryStatus === 'IR-LT') ? 'rgba(220,38,38,0.15)' : 'rgba(239,68,68,0.1)',
                      padding: '0.1rem 0.3rem',
                      borderRadius: '3px',
                    }}>
                      {(player as any).injuryStatus || 'INJ'}
                    </span>
                  </div>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>
                    {'position' in player ? (player as any).position : 'G'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Day-to-Day / Game Time Decision Players */}
        {dtdPlayers.length > 0 && (
          <div className="card" style={{ padding: '1rem', borderLeft: '3px solid #f59e0b' }}>
            <h4 style={{ fontSize: '0.8rem', fontWeight: 600, color: '#f59e0b', marginBottom: '0.75rem', textTransform: 'uppercase' }}>
              Day-to-Day / Questionable ({dtdPlayers.length})
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {dtdPlayers.map((player) => (
                <div key={player.playerId} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <PlayerHeadshot
                    playerId={player.playerId}
                    playerName={player.playerName}
                    teamAbbrev={lineup.teamAbbrev}
                    size={28}
                  />
                  <div style={{ flex: 1 }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{player.playerName}</span>
                    <span style={{
                      marginLeft: '0.5rem',
                      fontSize: '0.65rem',
                      fontWeight: 600,
                      color: '#f59e0b',
                      background: 'rgba(245,158,11,0.15)',
                      padding: '0.1rem 0.3rem',
                      borderRadius: '3px',
                    }}>
                      {(player as any).injuryStatus || 'DTD'}
                    </span>
                  </div>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>
                    {'position' in player ? (player as any).position : 'G'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// Compact Lineup Summary (for game cards)
// =============================================================================

export function LineupSummaryBadge({ lineup }: { lineup: TeamLineup }) {
  const { lineupStrength } = lineup;

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '0.5rem',
      padding: '0.35rem 0.5rem',
      background: 'rgba(255,255,255,0.03)',
      borderRadius: '0.5rem',
    }}>
      <div style={{
        width: '32px',
        height: '32px',
        borderRadius: '50%',
        background: `conic-gradient(${getStrengthColor(lineupStrength.overallQuality)} ${lineupStrength.overallQuality * 3.6}deg, rgba(255,255,255,0.1) 0deg)`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'white' }}>{lineupStrength.overallQuality}</span>
      </div>
      <div>
        <p style={{ fontSize: '0.7rem', fontWeight: 600, color: 'white' }}>{lineupStrength.percentOfFullStrength}%</p>
        <p style={{ fontSize: '0.55rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Strength</p>
      </div>
      {lineupStrength.missingPlayerImpact.length > 0 && (
        <span style={{
          padding: '0.15rem 0.35rem',
          fontSize: '0.6rem',
          fontWeight: 600,
          color: '#ef4444',
          background: 'rgba(239,68,68,0.15)',
          borderRadius: '0.25rem',
        }}>
          {lineupStrength.missingPlayerImpact.length} OUT
        </span>
      )}
    </div>
  );
}

export type { TeamLineup };
