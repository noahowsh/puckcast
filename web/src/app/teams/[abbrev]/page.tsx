import { notFound } from "next/navigation";
import { buildTeamSnapshots, computeStandingsPowerScore, formatPowerScore, getCurrentStandings, getCurrentPredictions } from "@/lib/current";
import { TeamLogo } from "@/components/TeamLogo";
import { TeamCrest } from "@/components/TeamCrest";
import goaliePulseRaw from "@/data/goaliePulse.json";
import powerIndexSnapshot from "@/data/powerIndexSnapshot.json";
import type { GoaliePulse } from "@/types/goalie";

const goaliePulse = goaliePulseRaw as GoaliePulse;
const movementReasons = powerIndexSnapshot.movementReasons as Record<string, string>;
const snapshots = buildTeamSnapshots();
const snapshotMap = new Map(
  snapshots.map((team, idx) => [team.abbrev.toLowerCase(), { ...team, powerRank: idx + 1, powerScore: formatPowerScore(team) }]),
);
const standings = getCurrentStandings();
const standingsMap = new Map(standings.map((t) => [t.abbrev.toLowerCase(), { ...t, record: `${t.wins}-${t.losses}-${t.ot}` }]));
const predictions = getCurrentPredictions();

// Get league-wide stats for comparison
const leagueStats = {
  maxGoalsFor: Math.max(...standings.map(t => t.goalsForPerGame ?? 0)),
  minGoalsFor: Math.min(...standings.map(t => t.goalsForPerGame ?? 0)),
  maxGoalsAgainst: Math.max(...standings.map(t => t.goalsAgainstPerGame ?? 0)),
  minGoalsAgainst: Math.min(...standings.map(t => t.goalsAgainstPerGame ?? 0)),
  avgGoalsFor: standings.reduce((sum, t) => sum + (t.goalsForPerGame ?? 0), 0) / standings.length,
  avgGoalsAgainst: standings.reduce((sum, t) => sum + (t.goalsAgainstPerGame ?? 0), 0) / standings.length,
  maxPointPctg: Math.max(...standings.map(t => t.pointPctg ?? 0)),
};

function movementLabel(movement: number) {
  if (movement === 0) return "Even";
  return movement > 0 ? `+${movement}` : `${movement}`;
}

function buildStrengths(team: (typeof snapshots)[number]) {
  const strengths: string[] = [];
  if (team.avgProb > 0.55) strengths.push("Consistent favorite in the model");
  if ((team.avgEdge ?? 0) > 0.12) strengths.push("High average edge vs market baselines");
  if ((team.favoriteRate ?? 0) > 0.6) strengths.push("Wins model coin flips often");
  if (strengths.length === 0) strengths.push("Steady but not dominant in recent projections");
  return strengths;
}

function buildWeaknesses(team: (typeof snapshots)[number]) {
  const weaknesses: string[] = [];
  if (team.avgProb < 0.5) weaknesses.push("Model sees below-average win probability");
  if ((team.avgEdge ?? 0) < 0.08) weaknesses.push("Edges are tight; little margin for error");
  if ((team.favoriteRate ?? 0) < 0.4) weaknesses.push("Rarely a strong favorite in the model");
  if (weaknesses.length === 0) weaknesses.push("Edges can compress against top opponents");
  return weaknesses;
}

export function generateStaticParams() {
  return standings.map((team) => ({
    abbrev: team.abbrev.toLowerCase(),
  }));
}

export default async function TeamPage({ params }: { params: Promise<{ abbrev: string }> }) {
  const { abbrev } = await params;
  const key = abbrev?.toLowerCase?.();
  if (!key) return notFound();
  const fallbackStandings = standingsMap.get(key);
  const snapshot =
    snapshotMap.get(key) ||
    (fallbackStandings && {
      team: fallbackStandings.team,
      abbrev: fallbackStandings.abbrev,
      games: fallbackStandings.gamesPlayed,
      avgProb: 0.5,
      avgEdge: 0,
      favoriteRate: 0.5,
      record: fallbackStandings.record,
      points: fallbackStandings.points,
      pointPctg: fallbackStandings.pointPctg,
      standingsRank: fallbackStandings.rank,
      powerRank: fallbackStandings.rank,
      powerScore: computeStandingsPowerScore(fallbackStandings),
    });
  if (!snapshot) return notFound();

  const standingsInfo = standingsMap.get(key);
  const powerScore = snapshot.powerScore ?? formatPowerScore(snapshot as any);
  const movement = standingsInfo?.rank ? standingsInfo.rank - snapshot.powerRank : 0;
  const strengths = buildStrengths(snapshot);
  const weaknesses = buildWeaknesses(snapshot);

  // Get upcoming games for this team
  const upcomingGames = predictions.games.filter(
    (game) => game.homeTeam.abbrev === snapshot.abbrev || game.awayTeam.abbrev === snapshot.abbrev
  );

  // Get team goalies
  const teamGoalies = goaliePulse.goalies.filter((g) => g.team === snapshot.abbrev);

  return (
    <div className="min-h-screen">
      <div className="container">
        <section className="nova-hero nav-offset">
          <div className="nova-hero__grid nova-hero__grid--balanced">
            <div className="nova-hero__text">
              <div className="pill-row">
                <span className="pill">Team profile</span>
                <span className="pill">{snapshot.team}</span>
              </div>
              <h1 className="display-xl">
                #{snapshot.powerRank} · {snapshot.team}
              </h1>
              <p className="lead">
                Model view of the {snapshot.team}: power index, edges, upcoming games, and how the model stacks them versus the standings.
              </p>
              <div className="stat-grid">
                <div className="stat-tile">
                  <p className="stat-tile__label">Power score</p>
                  <p className="stat-tile__value">{powerScore}</p>
                  <p className="stat-tile__detail">#{snapshot.powerRank} in the model</p>
                </div>
                <div className="stat-tile">
                  <p className="stat-tile__label">Record</p>
                  <p className="stat-tile__value">{standingsInfo?.record ?? "N/A"}</p>
                  <p className="stat-tile__detail">Points {standingsInfo?.points ?? "N/A"}</p>
                </div>
                <div className="stat-tile">
                  <p className="stat-tile__label">Model win %</p>
                  <p className="stat-tile__value">{(snapshot.avgProb * 100).toFixed(1)}%</p>
                  <p className="stat-tile__detail">Avg edge {(snapshot.avgEdge * 100).toFixed(1)} pts</p>
                </div>
                <div className="stat-tile">
                  <p className="stat-tile__label">Movement</p>
                  <p className="stat-tile__value">{movementLabel(movement)}</p>
                  <p className="stat-tile__detail">vs standings #{standingsInfo?.rank ?? "N/A"}</p>
                </div>
              </div>
            </div>

            {/* Power Score Visual Panel */}
            <div className="nova-hero__panel" style={{ padding: '1.5rem' }}>
              {/* Team Crest + Power Ring */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', marginBottom: '1.5rem' }}>
                <div style={{ position: 'relative' }}>
                  {/* Power Score Ring */}
                  <svg width="120" height="120" viewBox="0 0 120 120" style={{ transform: 'rotate(-90deg)' }}>
                    {/* Background ring */}
                    <circle cx="60" cy="60" r="52" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="8" />
                    {/* Progress ring - based on power rank (1-32) */}
                    <circle
                      cx="60" cy="60" r="52"
                      fill="none"
                      stroke={snapshot.powerRank <= 8 ? '#10b981' : snapshot.powerRank <= 16 ? '#3b82f6' : snapshot.powerRank <= 24 ? '#f59e0b' : '#ef4444'}
                      strokeWidth="8"
                      strokeDasharray={`${((33 - snapshot.powerRank) / 32) * 327} 327`}
                      strokeLinecap="round"
                    />
                  </svg>
                  {/* Team crest in center */}
                  <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}>
                    <TeamCrest abbrev={snapshot.abbrev} size={56} />
                  </div>
                </div>
                <div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Power Index</p>
                  <p style={{ fontSize: '2.5rem', fontWeight: 700, color: 'white', lineHeight: 1 }}>#{snapshot.powerRank}</p>
                  <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                    Score: {powerScore} pts
                  </p>
                </div>
              </div>

              {/* Model Confidence Meter */}
              <div style={{ marginBottom: '1.25rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Model Win Rate</span>
                  <span style={{ fontSize: '1rem', fontWeight: 600, color: snapshot.avgProb >= 0.55 ? '#10b981' : snapshot.avgProb >= 0.45 ? '#3b82f6' : '#f59e0b' }}>
                    {(snapshot.avgProb * 100).toFixed(1)}%
                  </span>
                </div>
                <div style={{ height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{
                    height: '100%',
                    width: `${snapshot.avgProb * 100}%`,
                    background: snapshot.avgProb >= 0.55 ? 'linear-gradient(90deg, #10b981, #34d399)' : snapshot.avgProb >= 0.45 ? 'linear-gradient(90deg, #3b82f6, #60a5fa)' : 'linear-gradient(90deg, #f59e0b, #fbbf24)',
                    borderRadius: '4px',
                    transition: 'width 0.5s ease'
                  }} />
                </div>
                <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', marginTop: '0.25rem' }}>
                  Avg edge: {((snapshot.avgEdge ?? 0) * 100).toFixed(1)} pts • Favorite {((snapshot.favoriteRate ?? 0) * 100).toFixed(0)}% of games
                </p>
              </div>

              {/* Quick Context - Movement Reason */}
              {movementReasons[snapshot.abbrev] && (
                <div style={{
                  padding: '0.75rem',
                  background: 'rgba(255,255,255,0.03)',
                  borderRadius: '0.5rem',
                  borderLeft: '3px solid var(--accent-primary)',
                  marginBottom: '1rem'
                }}>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>This Week</p>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontStyle: 'italic' }}>
                    {movementReasons[snapshot.abbrev]}
                  </p>
                </div>
              )}

              {/* Offense vs Defense Bars */}
              <div style={{ display: 'grid', gap: '0.75rem' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                    <span style={{ fontSize: '0.7rem', color: '#10b981' }}>OFFENSE</span>
                    <span style={{ fontSize: '0.75rem', color: 'white', fontWeight: 500 }}>{standingsInfo?.goalsForPerGame?.toFixed(2)} GPG</span>
                  </div>
                  <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{
                      height: '100%',
                      width: `${((standingsInfo?.goalsForPerGame ?? 0) / leagueStats.maxGoalsFor) * 100}%`,
                      background: 'linear-gradient(90deg, #10b981, #34d399)',
                      borderRadius: '3px'
                    }} />
                  </div>
                </div>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                    <span style={{ fontSize: '0.7rem', color: '#3b82f6' }}>DEFENSE</span>
                    <span style={{ fontSize: '0.75rem', color: 'white', fontWeight: 500 }}>{standingsInfo?.goalsAgainstPerGame?.toFixed(2)} GA/G</span>
                  </div>
                  <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                    {/* For defense, lower is better - invert the bar */}
                    <div style={{
                      height: '100%',
                      width: `${(1 - ((standingsInfo?.goalsAgainstPerGame ?? leagueStats.avgGoalsAgainst) - leagueStats.minGoalsAgainst) / (leagueStats.maxGoalsAgainst - leagueStats.minGoalsAgainst)) * 100}%`,
                      background: 'linear-gradient(90deg, #3b82f6, #60a5fa)',
                      borderRadius: '3px'
                    }} />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* League Rankings Context */}
        <section className="nova-section">
          <h2 className="text-2xl font-bold text-white mb-4">League standings context</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Points Rank */}
            <div className="card" style={{ position: 'relative', overflow: 'hidden' }}>
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                height: '100%',
                width: `${((33 - (standingsInfo?.rank ?? 16)) / 32) * 100}%`,
                background: 'linear-gradient(90deg, rgba(16,185,129,0.15), transparent)',
                zIndex: 0
              }} />
              <div style={{ position: 'relative', zIndex: 1 }}>
                <p className="stat-label">League Rank</p>
                <p className="stat-tile__value text-3xl">#{standingsInfo?.rank ?? 'N/A'}</p>
                <p className="text-xs text-white/50 mt-1">of 32 teams</p>
              </div>
            </div>

            {/* Power Index vs Standings */}
            <div className="card">
              <p className="stat-label">Power vs Standings</p>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
                <p className="stat-tile__value text-2xl">{movement > 0 ? '+' : ''}{movement}</p>
                <span style={{ fontSize: '0.75rem', color: movement > 0 ? '#10b981' : movement < 0 ? '#ef4444' : 'var(--text-tertiary)' }}>
                  {movement > 0 ? 'undervalued' : movement < 0 ? 'overvalued' : 'fair value'}
                </span>
              </div>
              <p className="text-xs text-white/50 mt-1">
                Model #{snapshot.powerRank} vs Standings #{standingsInfo?.rank ?? 'N/A'}
              </p>
            </div>

            {/* Point Percentage Rank */}
            <div className="card">
              <p className="stat-label">Point %</p>
              <p className="stat-tile__value text-2xl">{standingsInfo?.pointPctg ? (standingsInfo.pointPctg * 100).toFixed(1) + '%' : 'N/A'}</p>
              <div style={{ marginTop: '0.5rem', height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${((standingsInfo?.pointPctg ?? 0) / leagueStats.maxPointPctg) * 100}%`,
                  background: '#3b82f6',
                  borderRadius: '2px'
                }} />
              </div>
            </div>

            {/* Goal Diff Rank */}
            <div className="card">
              <p className="stat-label">Goal Differential</p>
              <p className={`stat-tile__value text-2xl ${(standingsInfo?.goalDifferential ?? 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {(standingsInfo?.goalDifferential ?? 0) >= 0 ? '+' : ''}{standingsInfo?.goalDifferential ?? 'N/A'}
              </p>
              <p className="text-xs text-white/50 mt-1">
                {(standingsInfo?.goalDifferential ?? 0) > 20 ? 'Elite run differential' :
                 (standingsInfo?.goalDifferential ?? 0) > 0 ? 'Positive run diff' :
                 (standingsInfo?.goalDifferential ?? 0) > -10 ? 'Slightly negative' : 'Struggling to outscore opponents'}
              </p>
            </div>
          </div>
        </section>

        {/* Strengths & Weaknesses Visual */}
        <section className="nova-section">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="card" style={{ borderLeft: '4px solid #10b981' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <span style={{ fontSize: '1.25rem' }}>💪</span>
                <h3 className="text-lg font-bold text-white">Strengths</h3>
              </div>
              <ul className="space-y-3">
                {strengths.map((item, idx) => (
                  <li key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                    <span style={{ color: '#10b981', fontWeight: 700, fontSize: '0.875rem' }}>✓</span>
                    <span className="text-sm text-white/80">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="card" style={{ borderLeft: '4px solid #f59e0b' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <span style={{ fontSize: '1.25rem' }}>⚠️</span>
                <h3 className="text-lg font-bold text-white">Watch Out For</h3>
              </div>
              <ul className="space-y-3">
                {weaknesses.map((item, idx) => (
                  <li key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                    <span style={{ color: '#f59e0b', fontWeight: 700, fontSize: '0.875rem' }}>!</span>
                    <span className="text-sm text-white/80">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        {/* Upcoming Games Section */}
        <section className="nova-section">
          <h2 className="text-2xl font-bold text-white mb-4">Upcoming games</h2>
          {upcomingGames.length > 0 ? (
            <div className="space-y-3">
              {upcomingGames.map((game) => {
                const isHome = game.homeTeam.abbrev === snapshot.abbrev;
                const opponent = isHome ? game.awayTeam : game.homeTeam;
                const winProb = isHome ? game.homeWinProb : game.awayWinProb;
                const teamEdge = isHome ? game.edge : -game.edge;

                return (
                  <div key={game.id} className="card">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                      <div className="flex items-center gap-4">
                        <TeamLogo teamAbbrev={opponent.abbrev} size="xs" />
                        <div>
                          <p className="text-white font-semibold">
                            {isHome ? "vs" : "@"} {opponent.name}
                          </p>
                          <p className="text-sm text-white/60">
                            {game.gameDate} • {game.startTimeEt ?? "TBD"}
                          </p>
                          {game.venue && <p className="text-xs text-white/50">{game.venue}</p>}
                        </div>
                      </div>
                      <div className="flex flex-col sm:items-end gap-1">
                        <div className="flex items-center gap-2">
                          <span className="chip-soft chip-soft--mini">{(winProb * 100).toFixed(1)}% win prob</span>
                          <span className={`chip-soft chip-soft--mini ${teamEdge >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {teamEdge >= 0 ? '+' : ''}{(teamEdge * 100).toFixed(1)} edge
                          </span>
                        </div>
                        <span className="text-xs text-white/60 text-right sm:text-left">{game.confidenceGrade} confidence</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="card">
              <p className="text-white/70">No upcoming games scheduled</p>
            </div>
          )}
        </section>

        {/* Team Statistics Section - Visual */}
        <section className="nova-section">
          <h2 className="text-2xl font-bold text-white mb-4">Team performance</h2>

          {/* Visual Record Breakdown */}
          <div className="card" style={{ marginBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
              <p className="stat-label" style={{ margin: 0 }}>Season Record</p>
              <p style={{ fontSize: '1.5rem', fontWeight: 700, color: 'white' }}>{standingsInfo?.record ?? 'N/A'}</p>
            </div>
            {/* Visual record bar */}
            {standingsInfo && (
              <div style={{ display: 'flex', height: '32px', borderRadius: '8px', overflow: 'hidden' }}>
                <div style={{
                  width: `${(standingsInfo.wins / standingsInfo.gamesPlayed) * 100}%`,
                  background: 'linear-gradient(135deg, #10b981, #34d399)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  minWidth: standingsInfo.wins > 0 ? '40px' : 0
                }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'white' }}>{standingsInfo.wins}W</span>
                </div>
                <div style={{
                  width: `${(standingsInfo.losses / standingsInfo.gamesPlayed) * 100}%`,
                  background: 'linear-gradient(135deg, #ef4444, #f87171)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  minWidth: standingsInfo.losses > 0 ? '40px' : 0
                }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'white' }}>{standingsInfo.losses}L</span>
                </div>
                <div style={{
                  width: `${(standingsInfo.ot / standingsInfo.gamesPlayed) * 100}%`,
                  background: 'linear-gradient(135deg, #f59e0b, #fbbf24)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  minWidth: standingsInfo.ot > 0 ? '40px' : 0
                }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'white' }}>{standingsInfo.ot}OT</span>
                </div>
              </div>
            )}
          </div>

          {/* Offense vs Defense Visual Comparison */}
          <div className="grid gap-4 sm:grid-cols-2">
            {/* Offense Card */}
            <div className="card" style={{ background: 'linear-gradient(135deg, rgba(16,185,129,0.1), rgba(16,185,129,0.02))' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  background: 'rgba(16,185,129,0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <span style={{ fontSize: '1.25rem' }}>⚔️</span>
                </div>
                <div>
                  <p className="stat-label" style={{ margin: 0 }}>Offense</p>
                  <p style={{ fontSize: '1.75rem', fontWeight: 700, color: '#10b981', lineHeight: 1 }}>
                    {standingsInfo?.goalsForPerGame?.toFixed(2) ?? 'N/A'}
                  </p>
                </div>
                <p style={{ marginLeft: 'auto', fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>goals/game</p>
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', marginBottom: '0.25rem' }}>Shots For</p>
                  <p style={{ fontSize: '1.125rem', fontWeight: 600, color: 'white' }}>{standingsInfo?.shotsForPerGame?.toFixed(1) ?? 'N/A'}</p>
                </div>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', marginBottom: '0.25rem' }}>League Rank</p>
                  <p style={{ fontSize: '1.125rem', fontWeight: 600, color: 'white' }}>
                    #{standings.sort((a, b) => (b.goalsForPerGame ?? 0) - (a.goalsForPerGame ?? 0)).findIndex(t => t.abbrev === snapshot.abbrev) + 1}
                  </p>
                </div>
              </div>
            </div>

            {/* Defense Card */}
            <div className="card" style={{ background: 'linear-gradient(135deg, rgba(59,130,246,0.1), rgba(59,130,246,0.02))' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  background: 'rgba(59,130,246,0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <span style={{ fontSize: '1.25rem' }}>🛡️</span>
                </div>
                <div>
                  <p className="stat-label" style={{ margin: 0 }}>Defense</p>
                  <p style={{ fontSize: '1.75rem', fontWeight: 700, color: '#3b82f6', lineHeight: 1 }}>
                    {standingsInfo?.goalsAgainstPerGame?.toFixed(2) ?? 'N/A'}
                  </p>
                </div>
                <p style={{ marginLeft: 'auto', fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>goals against/game</p>
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', marginBottom: '0.25rem' }}>Shots Against</p>
                  <p style={{ fontSize: '1.125rem', fontWeight: 600, color: 'white' }}>{standingsInfo?.shotsAgainstPerGame?.toFixed(1) ?? 'N/A'}</p>
                </div>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', marginBottom: '0.25rem' }}>League Rank</p>
                  <p style={{ fontSize: '1.125rem', fontWeight: 600, color: 'white' }}>
                    #{standings.sort((a, b) => (a.goalsAgainstPerGame ?? 99) - (b.goalsAgainstPerGame ?? 99)).findIndex(t => t.abbrev === snapshot.abbrev) + 1}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Goalies Section */}
        {teamGoalies.length > 0 && (
          <section className="nova-section">
            <h2 className="text-2xl font-bold text-white mb-4">Team goalies</h2>
            <div className="space-y-3">
              {teamGoalies.map((goalie) => (
                <div key={goalie.name} className="card">
                  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-bold text-white">{goalie.name}</h3>
                        <span className={`chip-soft chip-soft--mini ${
                          goalie.trend === 'surging' ? 'text-emerald-400' :
                          goalie.trend === 'steady' ? 'text-blue-400' :
                          'text-white/70'
                        }`}>
                          {goalie.trend}
                        </span>
                      </div>
                      <p className="text-sm text-white/70 mb-3">{goalie.note}</p>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        <div>
                          <p className="text-xs text-white/50 mb-1">Season GSAx</p>
                          <p className="text-white font-semibold">{goalie.seasonGsa.toFixed(1)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-white/50 mb-1">Rolling GSAx</p>
                          <p className="text-white font-semibold">{goalie.rollingGsa.toFixed(1)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-white/50 mb-1">Rest days</p>
                          <p className="text-white font-semibold">{goalie.restDays}</p>
                        </div>
                        <div>
                          <p className="text-xs text-white/50 mb-1">Start likelihood</p>
                          <p className="text-white font-semibold">{(goalie.startLikelihood * 100).toFixed(0)}%</p>
                        </div>
                      </div>
                    </div>
                    <div className="flex sm:flex-col gap-2">
                      {goalie.strengths.length > 0 && (
                        <div className="flex-1">
                          <p className="text-xs text-emerald-400 mb-1">Strengths</p>
                          {goalie.strengths.map((s, idx) => (
                            <p key={idx} className="text-xs text-white/70">• {s}</p>
                          ))}
                        </div>
                      )}
                      {goalie.watchouts.length > 0 && (
                        <div className="flex-1">
                          <p className="text-xs text-amber-400 mb-1">Watch</p>
                          {goalie.watchouts.map((w, idx) => (
                            <p key={idx} className="text-xs text-white/70">• {w}</p>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
