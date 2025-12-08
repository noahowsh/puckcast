// Lineup Display Components
// Visual components for showing projected lineups and strength metrics

import Link from "next/link";
import { TeamCrest } from "./TeamCrest";
import type { TeamLineup, LineupPlayer, GoalieLineup, LineupStrengthMetrics } from "@/types/lineup";

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
// Player Row Components
// =============================================================================

function PlayerRow({ player, rank, showRankingScore = true }: {
  player: LineupPlayer;
  rank: number;
  showRankingScore?: boolean;
}) {
  const isInjured = !player.isHealthy;

  return (
    <Link
      href={`/players/${player.playerId}`}
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: '0.5rem 0.75rem',
        background: rank % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'transparent',
        opacity: isInjured ? 0.5 : 1,
        textDecoration: 'none',
        transition: 'background 0.15s ease',
      }}
      className="hover:bg-white/5"
    >
      <span style={{
        width: '24px',
        fontSize: '0.8rem',
        fontWeight: 600,
        color: rank <= 3 ? '#10b981' : 'var(--text-tertiary)',
      }}>{rank}</span>
      <span style={{
        width: '28px',
        fontSize: '0.75rem',
        color: 'var(--text-tertiary)',
        fontFamily: 'monospace',
      }}>{player.jerseyNumber || '—'}</span>
      <span style={{ flex: 1, fontSize: '0.85rem', color: 'white', fontWeight: 500 }}>
        {player.playerName}
        {isInjured && (
          <span style={{ marginLeft: '0.5rem', fontSize: '0.65rem', color: '#ef4444', fontWeight: 600 }}>INJ</span>
        )}
      </span>
      <span style={{ width: '30px', fontSize: '0.8rem', color: 'var(--text-secondary)', textAlign: 'center' }}>{player.position}</span>
      <span style={{ width: '35px', fontSize: '0.8rem', color: 'var(--text-secondary)', textAlign: 'right' }}>{player.gamesPlayed}</span>
      <span style={{ width: '35px', fontSize: '0.8rem', color: '#10b981', textAlign: 'right', fontWeight: 600 }}>{player.points}</span>
      <span style={{
        width: '35px',
        fontSize: '0.8rem',
        color: player.plusMinus >= 0 ? '#10b981' : '#ef4444',
        textAlign: 'right',
      }}>{player.plusMinus >= 0 ? '+' : ''}{player.plusMinus}</span>
      {showRankingScore && (
        <span style={{
          width: '45px',
          fontSize: '0.75rem',
          color: getStrengthColor(player.rankingScore),
          textAlign: 'right',
          fontWeight: 600,
        }}>{player.rankingScore}</span>
      )}
    </Link>
  );
}

function GoalieRow({ goalie, rank }: { goalie: GoalieLineup; rank: number }) {
  const isInjured = !goalie.isHealthy;

  return (
    <Link
      href={`/goalies/${goalie.playerId}`}
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: '0.5rem 0.75rem',
        background: rank % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'transparent',
        opacity: isInjured ? 0.5 : 1,
        textDecoration: 'none',
        transition: 'background 0.15s ease',
      }}
      className="hover:bg-white/5"
    >
      <span style={{
        width: '24px',
        fontSize: '0.8rem',
        fontWeight: 600,
        color: goalie.isProjectedStarter ? '#10b981' : 'var(--text-tertiary)',
      }}>{goalie.isProjectedStarter ? '★' : rank}</span>
      <span style={{
        width: '28px',
        fontSize: '0.75rem',
        color: 'var(--text-tertiary)',
        fontFamily: 'monospace',
      }}>{goalie.jerseyNumber || '—'}</span>
      <span style={{ flex: 1, fontSize: '0.85rem', color: 'white', fontWeight: 500 }}>
        {goalie.playerName}
        {goalie.isProjectedStarter && (
          <span style={{ marginLeft: '0.5rem', fontSize: '0.6rem', color: '#10b981', fontWeight: 600 }}>STARTER</span>
        )}
        {isInjured && (
          <span style={{ marginLeft: '0.5rem', fontSize: '0.65rem', color: '#ef4444', fontWeight: 600 }}>INJ</span>
        )}
      </span>
      <span style={{ width: '35px', fontSize: '0.8rem', color: 'var(--text-secondary)', textAlign: 'right' }}>{goalie.gamesPlayed}</span>
      <span style={{ width: '35px', fontSize: '0.8rem', color: '#10b981', textAlign: 'right', fontWeight: 600 }}>{goalie.wins}</span>
      <span style={{ width: '45px', fontSize: '0.8rem', color: 'var(--text-secondary)', textAlign: 'right' }}>
        .{Math.round(goalie.savePct * 1000)}
      </span>
      <span style={{ width: '45px', fontSize: '0.8rem', color: 'var(--text-secondary)', textAlign: 'right' }}>
        {goalie.goalsAgainstAverage.toFixed(2)}
      </span>
      <span style={{
        width: '45px',
        fontSize: '0.75rem',
        color: getStrengthColor(goalie.rankingScore),
        textAlign: 'right',
        fontWeight: 600,
      }}>{goalie.rankingScore}</span>
    </Link>
  );
}

// =============================================================================
// Main Lineup Display Component
// =============================================================================

export function ProjectedLineupDisplay({ lineup }: { lineup: TeamLineup }) {
  const injuredPlayers = [
    ...lineup.forwards.filter(p => !p.isHealthy),
    ...lineup.defensemen.filter(p => !p.isHealthy),
    ...lineup.goalies.filter(g => !g.isHealthy),
  ];

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      {/* Left Column: Strength Card */}
      <div className="lg:col-span-1">
        <LineupStrengthCard strength={lineup.lineupStrength} />

        {/* Injured Players */}
        {injuredPlayers.length > 0 && (
          <div className="card mt-4" style={{ padding: '1rem', borderLeft: '3px solid #ef4444' }}>
            <h4 style={{ fontSize: '0.8rem', fontWeight: 600, color: '#ef4444', marginBottom: '0.75rem', textTransform: 'uppercase' }}>
              Injured Players ({injuredPlayers.length})
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {lineup.lineupStrength.missingPlayerImpact.slice(0, 5).map((missing) => (
                <div key={missing.playerId} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{missing.playerName}</span>
                  <span style={{ fontSize: '0.75rem', color: '#f59e0b', fontWeight: 600 }}>-{missing.impactScore.toFixed(1)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Right Column: Roster Lists */}
      <div className="lg:col-span-2">
        {/* Forwards */}
        <div className="card mb-4" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '0.75rem 1rem', background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
            <h4 style={{ fontSize: '0.8rem', fontWeight: 600, color: 'white', textTransform: 'uppercase' }}>
              Forwards ({lineup.projectedForwards.length}/{lineup.typicalForwards})
            </h4>
          </div>
          <div style={{
            display: 'flex',
            padding: '0.35rem 0.75rem',
            fontSize: '0.65rem',
            color: 'var(--text-tertiary)',
            textTransform: 'uppercase',
            borderBottom: '1px solid rgba(255,255,255,0.03)',
          }}>
            <span style={{ width: '24px' }}>#</span>
            <span style={{ width: '28px' }}>NO</span>
            <span style={{ flex: 1 }}>Player</span>
            <span style={{ width: '30px', textAlign: 'center' }}>Pos</span>
            <span style={{ width: '35px', textAlign: 'right' }}>GP</span>
            <span style={{ width: '35px', textAlign: 'right' }}>Pts</span>
            <span style={{ width: '35px', textAlign: 'right' }}>+/-</span>
            <span style={{ width: '45px', textAlign: 'right' }}>Score</span>
          </div>
          {lineup.forwards.slice(0, 14).map((player, idx) => (
            <PlayerRow key={player.playerId} player={player} rank={idx + 1} />
          ))}
        </div>

        {/* Defensemen */}
        <div className="card mb-4" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '0.75rem 1rem', background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
            <h4 style={{ fontSize: '0.8rem', fontWeight: 600, color: 'white', textTransform: 'uppercase' }}>
              Defensemen ({lineup.projectedDefensemen.length}/{lineup.typicalDefensemen})
            </h4>
          </div>
          <div style={{
            display: 'flex',
            padding: '0.35rem 0.75rem',
            fontSize: '0.65rem',
            color: 'var(--text-tertiary)',
            textTransform: 'uppercase',
            borderBottom: '1px solid rgba(255,255,255,0.03)',
          }}>
            <span style={{ width: '24px' }}>#</span>
            <span style={{ width: '28px' }}>NO</span>
            <span style={{ flex: 1 }}>Player</span>
            <span style={{ width: '30px', textAlign: 'center' }}>Pos</span>
            <span style={{ width: '35px', textAlign: 'right' }}>GP</span>
            <span style={{ width: '35px', textAlign: 'right' }}>Pts</span>
            <span style={{ width: '35px', textAlign: 'right' }}>+/-</span>
            <span style={{ width: '45px', textAlign: 'right' }}>Score</span>
          </div>
          {lineup.defensemen.slice(0, 8).map((player, idx) => (
            <PlayerRow key={player.playerId} player={player} rank={idx + 1} />
          ))}
        </div>

        {/* Goalies */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '0.75rem 1rem', background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
            <h4 style={{ fontSize: '0.8rem', fontWeight: 600, color: 'white', textTransform: 'uppercase' }}>
              Goalies ({lineup.projectedGoalies.length}/{lineup.typicalGoalies})
            </h4>
          </div>
          <div style={{
            display: 'flex',
            padding: '0.35rem 0.75rem',
            fontSize: '0.65rem',
            color: 'var(--text-tertiary)',
            textTransform: 'uppercase',
            borderBottom: '1px solid rgba(255,255,255,0.03)',
          }}>
            <span style={{ width: '24px' }}>#</span>
            <span style={{ width: '28px' }}>NO</span>
            <span style={{ flex: 1 }}>Player</span>
            <span style={{ width: '35px', textAlign: 'right' }}>GP</span>
            <span style={{ width: '35px', textAlign: 'right' }}>W</span>
            <span style={{ width: '45px', textAlign: 'right' }}>SV%</span>
            <span style={{ width: '45px', textAlign: 'right' }}>GAA</span>
            <span style={{ width: '45px', textAlign: 'right' }}>Score</span>
          </div>
          {lineup.goalies.map((goalie, idx) => (
            <GoalieRow key={goalie.playerId} goalie={goalie} rank={idx + 1} />
          ))}
        </div>
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
