import { notFound } from "next/navigation";
import Link from "next/link";
import { computeStandingsPowerScore, getCurrentStandings, getCurrentPredictions } from "@/lib/current";
import { fetchTeamRoster } from "@/lib/playerHub";
import { buildProjectedLineup } from "@/lib/lineupService";
import { getTeamGoalies } from "@/lib/startingGoalieService";
import { TeamCrest } from "@/components/TeamCrest";
import { SkaterStatsTable, GoalieStatsTable } from "@/components/PlayerStatsTable";
import { ProjectedLineupDisplay, LineupStrengthCard } from "@/components/LineupDisplay";
import { TeamGoalieSituationCard } from "@/components/StartingGoalieDisplay";
import powerIndexSnapshot from "@/data/powerIndexSnapshot.json";

const movementReasons = powerIndexSnapshot.movementReasons as Record<string, string>;
const standings = getCurrentStandings();
const predictions = getCurrentPredictions();

// Build power rankings from standings (consistent across all teams)
const powerRankings = [...standings]
  .map(team => ({
    ...team,
    powerScore: computeStandingsPowerScore(team),
    record: `${team.wins}-${team.losses}-${team.ot}`,
  }))
  .sort((a, b) => b.powerScore - a.powerScore)
  .map((team, idx) => ({ ...team, powerRank: idx + 1 }));

const powerRankMap = new Map(powerRankings.map(t => [t.abbrev.toLowerCase(), t]));

// Division mapping
const divisions: Record<string, { name: string; conference: string; teams: string[] }> = {
  atlantic: { name: "Atlantic", conference: "Eastern", teams: ["BOS", "BUF", "DET", "FLA", "MTL", "OTT", "TBL", "TOR"] },
  metropolitan: { name: "Metropolitan", conference: "Eastern", teams: ["CAR", "CBJ", "NJD", "NYI", "NYR", "PHI", "PIT", "WSH"] },
  central: { name: "Central", conference: "Western", teams: ["CHI", "COL", "DAL", "MIN", "NSH", "STL", "UTA", "WPG"] },
  pacific: { name: "Pacific", conference: "Western", teams: ["ANA", "CGY", "EDM", "LAK", "SEA", "SJS", "VAN", "VGK"] },
};

function getTeamDivision(abbrev: string) {
  for (const [, div] of Object.entries(divisions)) {
    if (div.teams.includes(abbrev)) return div;
  }
  return null;
}

function getRankColor(rank: number, total: number = 32) {
  const pct = rank / total;
  if (pct <= 0.25) return '#10b981';
  if (pct <= 0.5) return '#3b82f6';
  if (pct <= 0.75) return '#f59e0b';
  return '#ef4444';
}

function getLeagueRank(abbrev: string, stat: 'goalsForPerGame' | 'goalsAgainstPerGame' | 'shotsForPerGame' | 'shotsAgainstPerGame' | 'pointPctg' | 'goalDifferential', ascending: boolean = false) {
  const sorted = [...standings].sort((a, b) => {
    const aVal = a[stat] ?? 0;
    const bVal = b[stat] ?? 0;
    return ascending ? aVal - bVal : bVal - aVal;
  });
  return sorted.findIndex(t => t.abbrev === abbrev) + 1;
}

// Calculate efficiency ranks
function getShootingPctRank(abbrev: string) {
  const withPct = standings.map(t => ({
    abbrev: t.abbrev,
    pct: t.goalsForPerGame && t.shotsForPerGame ? t.goalsForPerGame / t.shotsForPerGame : 0
  })).sort((a, b) => b.pct - a.pct);
  return withPct.findIndex(t => t.abbrev === abbrev) + 1;
}

function getSavePctRank(abbrev: string) {
  const withPct = standings.map(t => ({
    abbrev: t.abbrev,
    pct: t.goalsAgainstPerGame && t.shotsAgainstPerGame ? 1 - t.goalsAgainstPerGame / t.shotsAgainstPerGame : 0
  })).sort((a, b) => b.pct - a.pct);
  return withPct.findIndex(t => t.abbrev === abbrev) + 1;
}

function getPowerPlayRank(abbrev: string) {
  const sorted = [...standings]
    .filter(t => t.powerPlayPct != null)
    .sort((a, b) => (b.powerPlayPct ?? 0) - (a.powerPlayPct ?? 0));
  return sorted.findIndex(t => t.abbrev === abbrev) + 1;
}

function getPenaltyKillRank(abbrev: string) {
  const sorted = [...standings]
    .filter(t => t.penaltyKillPct != null)
    .sort((a, b) => (b.penaltyKillPct ?? 0) - (a.penaltyKillPct ?? 0));
  return sorted.findIndex(t => t.abbrev === abbrev) + 1;
}

function buildStrengths(teamData: typeof powerRankings[number]) {
  const strengths: string[] = [];
  const offenseRank = getLeagueRank(teamData.abbrev, 'goalsForPerGame');
  const defenseRank = getLeagueRank(teamData.abbrev, 'goalsAgainstPerGame', true);
  const shotsForRank = getLeagueRank(teamData.abbrev, 'shotsForPerGame');

  if (offenseRank <= 5) strengths.push(`Elite offense - #${offenseRank} in goals/game`);
  else if (offenseRank <= 10) strengths.push(`Strong offense - #${offenseRank} in scoring`);

  if (defenseRank <= 5) strengths.push(`Stingy defense - #${defenseRank} in goals against`);
  else if (defenseRank <= 10) strengths.push(`Solid defense - #${defenseRank} in GA/game`);

  if (shotsForRank <= 5) strengths.push(`Shot generation machine - #${shotsForRank} in shots/game`);
  if ((teamData.goalDifferential ?? 0) > 20) strengths.push("Elite goal differential");
  if ((teamData.pointPctg ?? 0) > 0.65) strengths.push("Outstanding point percentage");
  if (teamData.powerRank <= 5) strengths.push(`Top 5 in Power Index (#${teamData.powerRank})`);

  if (strengths.length === 0) strengths.push("Steady but not dominant in projections");
  return strengths.slice(0, 4);
}

function buildWeaknesses(teamData: typeof powerRankings[number]) {
  const weaknesses: string[] = [];
  const offenseRank = getLeagueRank(teamData.abbrev, 'goalsForPerGame');
  const defenseRank = getLeagueRank(teamData.abbrev, 'goalsAgainstPerGame', true);
  const shotsAgainstRank = getLeagueRank(teamData.abbrev, 'shotsAgainstPerGame', true);

  if (offenseRank >= 28) weaknesses.push(`Struggling offense - #${offenseRank} in goals`);
  else if (offenseRank >= 22) weaknesses.push(`Below-average scoring - #${offenseRank}`);

  if (defenseRank >= 28) weaknesses.push(`Leaky defense - #${defenseRank} in goals against`);
  else if (defenseRank >= 22) weaknesses.push(`Defensive concerns - #${defenseRank} in GA`);

  if (shotsAgainstRank >= 28) weaknesses.push(`Giving up too many shots - #${shotsAgainstRank}`);
  if ((teamData.goalDifferential ?? 0) < -15) weaknesses.push("Concerning goal differential");
  if (teamData.powerRank >= 25) weaknesses.push(`Bottom tier in Power Index (#${teamData.powerRank})`);

  if (weaknesses.length === 0) weaknesses.push("No major weaknesses identified");
  return weaknesses.slice(0, 4);
}

export function generateStaticParams() {
  return standings.map((team) => ({ abbrev: team.abbrev.toLowerCase() }));
}

export default async function TeamPage({ params }: { params: Promise<{ abbrev: string }> }) {
  const { abbrev } = await params;
  const key = abbrev?.toLowerCase?.();
  if (!key) return notFound();

  const teamData = powerRankMap.get(key);
  if (!teamData) return notFound();

  const movement = teamData.rank - teamData.powerRank;
  const strengths = buildStrengths(teamData);
  const weaknesses = buildWeaknesses(teamData);
  const teamDivision = getTeamDivision(teamData.abbrev);

  // Get division standings
  const divisionStandings = teamDivision
    ? powerRankings.filter(t => teamDivision.teams.includes(t.abbrev)).sort((a, b) => b.points - a.points)
    : [];
  const divisionRank = divisionStandings.findIndex(t => t.abbrev === teamData.abbrev) + 1;

  // Get conference standings
  const conferenceTeams = teamDivision
    ? Object.values(divisions).filter(d => d.conference === teamDivision.conference).flatMap(d => d.teams)
    : [];
  const conferenceStandings = powerRankings.filter(t => conferenceTeams.includes(t.abbrev)).sort((a, b) => b.points - a.points);
  const conferenceRank = conferenceStandings.findIndex(t => t.abbrev === teamData.abbrev) + 1;

  // Get upcoming games (up to 3)
  const upcomingGames = predictions.games
    .filter((game) => game.homeTeam.abbrev === teamData.abbrev || game.awayTeam.abbrev === teamData.abbrev)
    .slice(0, 3);

  // Fetch team roster, projected lineup, and goalie info in parallel
  const [roster, projectedLineup, goalieInfo] = await Promise.all([
    fetchTeamRoster(teamData.abbrev),
    buildProjectedLineup(teamData.abbrev),
    getTeamGoalies(teamData.abbrev),
  ]);
  const allSkaters = [...roster.forwards, ...roster.defensemen].sort((a, b) => b.stats.points - a.stats.points);

  // Calculate efficiency metrics
  const shootingPct = teamData.goalsForPerGame && teamData.shotsForPerGame
    ? (teamData.goalsForPerGame / teamData.shotsForPerGame * 100) : 0;
  const savePct = teamData.goalsAgainstPerGame && teamData.shotsAgainstPerGame
    ? ((1 - teamData.goalsAgainstPerGame / teamData.shotsAgainstPerGame) * 100) : 0;

  // All league ranks
  const ranks = {
    offense: getLeagueRank(teamData.abbrev, 'goalsForPerGame'),
    defense: getLeagueRank(teamData.abbrev, 'goalsAgainstPerGame', true),
    shotsFor: getLeagueRank(teamData.abbrev, 'shotsForPerGame'),
    shotsAgainst: getLeagueRank(teamData.abbrev, 'shotsAgainstPerGame', true),
    goalDiff: getLeagueRank(teamData.abbrev, 'goalDifferential'),
    pointPct: getLeagueRank(teamData.abbrev, 'pointPctg'),
    shootingPct: getShootingPctRank(teamData.abbrev),
    savePct: getSavePctRank(teamData.abbrev),
    powerPlay: getPowerPlayRank(teamData.abbrev),
    penaltyKill: getPenaltyKillRank(teamData.abbrev),
  };

  return (
    <div className="min-h-screen">
      <div className="container">
        {/* Hero Section */}
        <section className="nova-hero nav-offset">
          <div className="nova-hero__grid nova-hero__grid--balanced">
            <div className="nova-hero__text">
              <h1 className="display-xl">{teamData.team}</h1>
              <p className="lead">{teamDivision?.name} Division • {teamDivision?.conference} Conference</p>

              {/* Key Stats */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem', marginTop: '1.5rem' }}>
                <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '0.75rem', textAlign: 'center' }}>
                  <p style={{ fontSize: '2rem', fontWeight: 800, color: getRankColor(teamData.powerRank), lineHeight: 1 }}>#{teamData.powerRank}</p>
                  <p style={{ fontSize: '0.65rem', color: 'var(--text-tertiary)', marginTop: '0.25rem', textTransform: 'uppercase' }}>Power Index</p>
                </div>
                <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '0.75rem', textAlign: 'center' }}>
                  <p style={{ fontSize: '2rem', fontWeight: 800, color: 'white', lineHeight: 1 }}>{teamData.points}</p>
                  <p style={{ fontSize: '0.65rem', color: 'var(--text-tertiary)', marginTop: '0.25rem', textTransform: 'uppercase' }}>Points</p>
                </div>
                <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '0.75rem', textAlign: 'center' }}>
                  <p style={{ fontSize: '2rem', fontWeight: 800, color: teamData.goalDifferential >= 0 ? '#10b981' : '#ef4444', lineHeight: 1 }}>
                    {teamData.goalDifferential >= 0 ? '+' : ''}{teamData.goalDifferential}
                  </p>
                  <p style={{ fontSize: '0.65rem', color: 'var(--text-tertiary)', marginTop: '0.25rem', textTransform: 'uppercase' }}>Goal Diff</p>
                </div>
                <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '0.75rem', textAlign: 'center' }}>
                  <p style={{ fontSize: '2rem', fontWeight: 800, color: 'white', lineHeight: 1 }}>{(teamData.pointPctg * 100).toFixed(0)}%</p>
                  <p style={{ fontSize: '0.65rem', color: 'var(--text-tertiary)', marginTop: '0.25rem', textTransform: 'uppercase' }}>Point %</p>
                </div>
              </div>
            </div>

            {/* Team Card Panel */}
            <div className="nova-hero__panel" style={{ padding: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', marginBottom: '1.25rem' }}>
                <div style={{ position: 'relative', width: '120px', height: '120px' }}>
                  {/* Progress ring */}
                  <svg width="120" height="120" viewBox="0 0 120 120" style={{ position: 'absolute', transform: 'rotate(-90deg)' }}>
                    <circle cx="60" cy="60" r="52" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="8" />
                    <circle cx="60" cy="60" r="52" fill="none" stroke={getRankColor(teamData.powerRank)} strokeWidth="8"
                      strokeDasharray={`${((33 - teamData.powerRank) / 32) * 327} 327`} strokeLinecap="round" />
                  </svg>
                  {/* Logo centered */}
                  <div className="team-hero-crest" style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                  }}>
                    <TeamCrest abbrev={teamData.abbrev} size={64} />
                  </div>
                </div>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: '3rem', fontWeight: 800, color: 'white', lineHeight: 1, letterSpacing: '-0.02em' }}>#{teamData.powerRank}</p>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginTop: '0.35rem', fontWeight: 500 }}>Power Index</p>
                </div>
              </div>

              {/* Record Bar - Fixed OT issue */}
              <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: '0.75rem', padding: '1rem', marginBottom: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Season Record</span>
                  <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'white' }}>{teamData.record}</span>
                </div>
                <div style={{ display: 'flex', height: '24px', borderRadius: '6px', overflow: 'hidden' }}>
                  <div style={{ width: `${(teamData.wins / teamData.gamesPlayed) * 100}%`, background: '#10b981', display: 'flex', alignItems: 'center', justifyContent: 'center', minWidth: '30px' }}>
                    <span style={{ fontSize: '0.7rem', fontWeight: 600, color: 'white' }}>{teamData.wins}W</span>
                  </div>
                  <div style={{ width: `${(teamData.losses / teamData.gamesPlayed) * 100}%`, background: '#ef4444', display: 'flex', alignItems: 'center', justifyContent: 'center', minWidth: '30px' }}>
                    <span style={{ fontSize: '0.7rem', fontWeight: 600, color: 'white' }}>{teamData.losses}L</span>
                  </div>
                  {teamData.ot > 0 && (
                    <div style={{ width: `${(teamData.ot / teamData.gamesPlayed) * 100}%`, background: '#f59e0b', display: 'flex', alignItems: 'center', justifyContent: 'center', minWidth: '30px' }}>
                      <span style={{ fontSize: '0.7rem', fontWeight: 600, color: 'white' }}>{teamData.ot}OT</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Division/Conference */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                <div style={{ padding: '0.5rem', background: 'rgba(255,255,255,0.03)', borderRadius: '0.5rem', textAlign: 'center' }}>
                  <p style={{ fontSize: '1.25rem', fontWeight: 700, color: getRankColor(divisionRank, 8) }}>{divisionRank}{['st','nd','rd'][divisionRank-1] || 'th'}</p>
                  <p style={{ fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>{teamDivision?.name} Div</p>
                </div>
                <div style={{ padding: '0.5rem', background: 'rgba(255,255,255,0.03)', borderRadius: '0.5rem', textAlign: 'center' }}>
                  <p style={{ fontSize: '1.25rem', fontWeight: 700, color: getRankColor(conferenceRank, 16) }}>{conferenceRank}{['st','nd','rd'][conferenceRank-1] || 'th'}</p>
                  <p style={{ fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>{teamDivision?.conference} Conf</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Standings vs Power Index Comparison */}
        <section className="nova-section">
          <h2 className="text-xl font-bold text-white mb-3">Standings vs Power Index</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="card" style={{ padding: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                <div>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>League Standings</p>
                  <p style={{ fontSize: '2.5rem', fontWeight: 800, color: 'white', lineHeight: 1 }}>#{teamData.rank}</p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{teamData.points} points</p>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{teamData.record}</p>
                </div>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>Based on total points earned this season</p>
            </div>
            <div className="card" style={{ padding: '1.25rem', borderLeft: `4px solid ${getRankColor(teamData.powerRank)}` }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                <div>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Power Index</p>
                  <p style={{ fontSize: '2.5rem', fontWeight: 800, color: getRankColor(teamData.powerRank), lineHeight: 1 }}>#{teamData.powerRank}</p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Score: {teamData.powerScore}</p>
                  <p style={{
                    fontSize: '0.75rem',
                    color: movement > 0 ? '#10b981' : movement < 0 ? '#ef4444' : 'var(--text-tertiary)',
                    fontWeight: 600
                  }}>
                    {movement > 0 ? `▲ ${movement} undervalued` : movement < 0 ? `▼ ${Math.abs(movement)} overvalued` : '● Fair value'}
                  </p>
                </div>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>Model rank using points, goal diff, offense & defense metrics</p>
            </div>
          </div>
        </section>

        {/* Weekly Insight */}
        {movementReasons[teamData.abbrev] && (
          <section className="nova-section">
            <div className="card" style={{ padding: '1.25rem', borderLeft: '4px solid var(--accent-primary)' }}>
              <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Weekly Insight</p>
              <p style={{ fontSize: '1rem', color: 'var(--text-secondary)', fontStyle: 'italic', lineHeight: 1.5 }}>
                {movementReasons[teamData.abbrev]}
              </p>
            </div>
          </section>
        )}

        {/* League Rankings - Expanded */}
        <section className="nova-section">
          <h2 className="text-xl font-bold text-white mb-3">League Rankings</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="card" style={{ padding: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Offense</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 700, color: getRankColor(ranks.offense) }}>#{ranks.offense}</span>
              </div>
              <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${((33 - ranks.offense) / 32) * 100}%`, background: getRankColor(ranks.offense), borderRadius: '3px' }} />
              </div>
              <p style={{ fontSize: '0.85rem', color: 'white', marginTop: '0.5rem', fontWeight: 600 }}>{teamData.goalsForPerGame?.toFixed(2)} GPG</p>
            </div>
            <div className="card" style={{ padding: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Defense</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 700, color: getRankColor(ranks.defense) }}>#{ranks.defense}</span>
              </div>
              <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${((33 - ranks.defense) / 32) * 100}%`, background: getRankColor(ranks.defense), borderRadius: '3px' }} />
              </div>
              <p style={{ fontSize: '0.85rem', color: 'white', marginTop: '0.5rem', fontWeight: 600 }}>{teamData.goalsAgainstPerGame?.toFixed(2)} GA/G</p>
            </div>
            <div className="card" style={{ padding: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Goal Diff</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 700, color: getRankColor(ranks.goalDiff) }}>#{ranks.goalDiff}</span>
              </div>
              <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${((33 - ranks.goalDiff) / 32) * 100}%`, background: getRankColor(ranks.goalDiff), borderRadius: '3px' }} />
              </div>
              <p style={{ fontSize: '0.85rem', color: teamData.goalDifferential >= 0 ? '#10b981' : '#ef4444', marginTop: '0.5rem', fontWeight: 600 }}>
                {teamData.goalDifferential >= 0 ? '+' : ''}{teamData.goalDifferential}
              </p>
            </div>
            <div className="card" style={{ padding: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Point %</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 700, color: getRankColor(ranks.pointPct) }}>#{ranks.pointPct}</span>
              </div>
              <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${((33 - ranks.pointPct) / 32) * 100}%`, background: getRankColor(ranks.pointPct), borderRadius: '3px' }} />
              </div>
              <p style={{ fontSize: '0.85rem', color: 'white', marginTop: '0.5rem', fontWeight: 600 }}>{(teamData.pointPctg * 100).toFixed(1)}%</p>
            </div>
          </div>

          {/* Second row of rankings */}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 mt-3">
            <div className="card" style={{ padding: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Shots For</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 700, color: getRankColor(ranks.shotsFor) }}>#{ranks.shotsFor}</span>
              </div>
              <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${((33 - ranks.shotsFor) / 32) * 100}%`, background: getRankColor(ranks.shotsFor), borderRadius: '3px' }} />
              </div>
              <p style={{ fontSize: '0.85rem', color: 'white', marginTop: '0.5rem', fontWeight: 600 }}>{teamData.shotsForPerGame?.toFixed(1)} S/G</p>
            </div>
            <div className="card" style={{ padding: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Shots Against</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 700, color: getRankColor(ranks.shotsAgainst) }}>#{ranks.shotsAgainst}</span>
              </div>
              <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${((33 - ranks.shotsAgainst) / 32) * 100}%`, background: getRankColor(ranks.shotsAgainst), borderRadius: '3px' }} />
              </div>
              <p style={{ fontSize: '0.85rem', color: 'white', marginTop: '0.5rem', fontWeight: 600 }}>{teamData.shotsAgainstPerGame?.toFixed(1)} SA/G</p>
            </div>
            <div className="card" style={{ padding: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Shooting %</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 700, color: getRankColor(ranks.shootingPct) }}>#{ranks.shootingPct}</span>
              </div>
              <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${((33 - ranks.shootingPct) / 32) * 100}%`, background: getRankColor(ranks.shootingPct), borderRadius: '3px' }} />
              </div>
              <p style={{ fontSize: '0.85rem', color: 'white', marginTop: '0.5rem', fontWeight: 600 }}>{shootingPct.toFixed(1)}%</p>
            </div>
            <div className="card" style={{ padding: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Team Save %</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 700, color: getRankColor(ranks.savePct) }}>#{ranks.savePct}</span>
              </div>
              <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${((33 - ranks.savePct) / 32) * 100}%`, background: getRankColor(ranks.savePct), borderRadius: '3px' }} />
              </div>
              <p style={{ fontSize: '0.85rem', color: 'white', marginTop: '0.5rem', fontWeight: 600 }}>{savePct.toFixed(1)}%</p>
            </div>
          </div>

          {/* Special Teams */}
          <h3 className="text-lg font-semibold text-white mt-8 mb-3" style={{ paddingTop: '0.5rem' }}>Special Teams</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="card" style={{ padding: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Power Play</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 700, color: getRankColor(ranks.powerPlay) }}>#{ranks.powerPlay}</span>
              </div>
              <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${((33 - ranks.powerPlay) / 32) * 100}%`, background: getRankColor(ranks.powerPlay), borderRadius: '3px' }} />
              </div>
              <p style={{ fontSize: '0.85rem', color: 'white', marginTop: '0.5rem', fontWeight: 600 }}>
                {teamData.powerPlayPct != null ? `${(teamData.powerPlayPct * 100).toFixed(1)}%` : '—'}
              </p>
            </div>
            <div className="card" style={{ padding: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Penalty Kill</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 700, color: getRankColor(ranks.penaltyKill) }}>#{ranks.penaltyKill}</span>
              </div>
              <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${((33 - ranks.penaltyKill) / 32) * 100}%`, background: getRankColor(ranks.penaltyKill), borderRadius: '3px' }} />
              </div>
              <p style={{ fontSize: '0.85rem', color: 'white', marginTop: '0.5rem', fontWeight: 600 }}>
                {teamData.penaltyKillPct != null ? `${(teamData.penaltyKillPct * 100).toFixed(1)}%` : '—'}
              </p>
            </div>
          </div>
        </section>

        {/* Strengths & Weaknesses */}
        <section className="nova-section">
          <h2 className="text-xl font-bold text-white mb-3">Analysis</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="card" style={{ borderTop: '3px solid #10b981', padding: '1.25rem' }}>
              <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: '#10b981', marginBottom: '0.75rem', textTransform: 'uppercase' }}>Strengths</h3>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {strengths.map((item, idx) => (
                  <li key={idx} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    <span style={{ color: '#10b981' }}>✓</span> {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="card" style={{ borderTop: '3px solid #f59e0b', padding: '1.25rem' }}>
              <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: '#f59e0b', marginBottom: '0.75rem', textTransform: 'uppercase' }}>Areas to Watch</h3>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {weaknesses.map((item, idx) => (
                  <li key={idx} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    <span style={{ color: '#f59e0b' }}>!</span> {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        {/* Goaltending Situation */}
        {(goalieInfo.starter || goalieInfo.backup) && (
          <section className="nova-section">
            <h2 className="text-xl font-bold text-white mb-3">Goaltending Situation</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <TeamGoalieSituationCard
                starter={goalieInfo.starter}
                backup={goalieInfo.backup}
                teamAbbrev={teamData.abbrev}
              />
              {/* Next start projection */}
              {goalieInfo.starter && (
                <div className="card" style={{ padding: '1.25rem' }}>
                  <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'white', marginBottom: '1rem' }}>Next Start Analysis</h3>
                  <div style={{ marginBottom: '1rem' }}>
                    <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                      Start Confidence
                    </p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <div style={{ flex: 1, height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
                        <div style={{
                          width: `${goalieInfo.starter.confidence * 100}%`,
                          height: '100%',
                          background: goalieInfo.starter.confidence > 0.7 ? '#10b981' : goalieInfo.starter.confidence > 0.4 ? '#f59e0b' : '#ef4444',
                          borderRadius: '4px',
                        }} />
                      </div>
                      <span style={{ fontSize: '1rem', fontWeight: 700, color: 'white' }}>
                        {Math.round(goalieInfo.starter.confidence * 100)}%
                      </span>
                    </div>
                  </div>
                  <div style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '0.5rem' }}>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                      {goalieInfo.starter.restDays !== null && goalieInfo.starter.restDays >= 2
                        ? `Well-rested with ${goalieInfo.starter.restDays} days off. Strong candidate for next start.`
                        : goalieInfo.starter.restDays === 1
                        ? "One day rest. May start depending on schedule."
                        : goalieInfo.starter.restDays === 0
                        ? "Started last game. Backup may get the call."
                        : "Start projection based on season patterns."}
                    </p>
                  </div>
                  <div style={{ marginTop: '1rem', fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>
                    <p>Source: {goalieInfo.starter.source.replace(/_/g, ' ')}</p>
                    <p style={{ marginTop: '0.25rem' }}>Updated: {new Date(goalieInfo.starter.updatedAt).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}</p>
                  </div>
                </div>
              )}
            </div>
          </section>
        )}

        {/* Goals Breakdown Visual */}
        <section className="nova-section">
          <h2 className="text-xl font-bold text-white mb-3">Scoring Breakdown</h2>
          <div className="card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
              {/* Goals For vs Against visual */}
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <span style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: 600 }}>Goals For</span>
                      <span style={{ fontSize: '0.9rem', fontWeight: 700, color: '#10b981' }}>{Math.round((teamData.goalsForPerGame ?? 0) * teamData.gamesPlayed)}</span>
                    </div>
                    <div style={{ height: '24px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{
                        height: '100%',
                        width: `${((teamData.goalsForPerGame ?? 0) / 4.5) * 100}%`,
                        background: 'linear-gradient(90deg, #10b98140 0%, #10b981 100%)',
                        borderRadius: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'flex-end',
                        paddingRight: '8px',
                      }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'white' }}>{teamData.goalsForPerGame?.toFixed(2)}/G</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <span style={{ fontSize: '0.75rem', color: '#ef4444', fontWeight: 600 }}>Goals Against</span>
                      <span style={{ fontSize: '0.9rem', fontWeight: 700, color: '#ef4444' }}>{Math.round((teamData.goalsAgainstPerGame ?? 0) * teamData.gamesPlayed)}</span>
                    </div>
                    <div style={{ height: '24px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{
                        height: '100%',
                        width: `${((teamData.goalsAgainstPerGame ?? 0) / 4.5) * 100}%`,
                        background: 'linear-gradient(90deg, #ef444440 0%, #ef4444 100%)',
                        borderRadius: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'flex-end',
                        paddingRight: '8px',
                      }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'white' }}>{teamData.goalsAgainstPerGame?.toFixed(2)}/G</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              {/* Net result */}
              <div style={{
                width: '120px',
                height: '120px',
                borderRadius: '50%',
                background: `conic-gradient(${teamData.goalDifferential >= 0 ? '#10b981' : '#ef4444'} 0deg, rgba(255,255,255,0.05) 0deg)`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: `4px solid ${teamData.goalDifferential >= 0 ? '#10b981' : '#ef4444'}`,
              }}>
                <div style={{ textAlign: 'center' }}>
                  <p style={{
                    fontSize: '2rem',
                    fontWeight: 800,
                    color: teamData.goalDifferential >= 0 ? '#10b981' : '#ef4444',
                    lineHeight: 1,
                  }}>
                    {teamData.goalDifferential >= 0 ? '+' : ''}{teamData.goalDifferential}
                  </p>
                  <p style={{ fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', marginTop: '0.25rem' }}>Goal Diff</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Today's Game Predictions */}
        <section className="nova-section">
          <h2 className="text-xl font-bold text-white mb-3">Today&apos;s Game Predictions</h2>
          {upcomingGames.length > 0 ? (
            <div className="grid gap-3">
              {upcomingGames.map((game) => {
                const isHome = game.homeTeam.abbrev === teamData.abbrev;
                const opponent = isHome ? game.awayTeam : game.homeTeam;
                const winProb = isHome ? game.homeWinProb : game.awayWinProb;
                const teamEdge = isHome ? game.edge : -game.edge;
                const opponentData = powerRankMap.get(opponent.abbrev.toLowerCase());
                return (
                  <div key={game.id} className="card" style={{ padding: '1.25rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                      <div style={{ position: 'relative' }}>
                        <TeamCrest abbrev={opponent.abbrev} size={56} />
                        {opponentData && (
                          <div style={{
                            position: 'absolute',
                            bottom: '-4px',
                            right: '-4px',
                            background: getRankColor(opponentData.powerRank),
                            borderRadius: '4px',
                            padding: '2px 6px',
                            fontSize: '0.65rem',
                            fontWeight: 700,
                            color: 'white',
                          }}>#{opponentData.powerRank}</div>
                        )}
                      </div>
                      <div style={{ flex: 1 }}>
                        <p style={{ fontSize: '1.1rem', fontWeight: 600, color: 'white' }}>{isHome ? "vs" : "@"} {opponent.name}</p>
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginTop: '0.25rem' }}>{game.startTimeEt ?? "TBD"} • {game.venue}</p>
                        {opponentData && (
                          <p style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginTop: '0.25rem' }}>
                            {opponentData.record} ({opponentData.points} pts)
                          </p>
                        )}
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', alignItems: 'flex-end' }}>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <div style={{
                            padding: '0.5rem 0.75rem',
                            borderRadius: '8px',
                            background: winProb >= 0.55 ? 'rgba(16,185,129,0.15)' : winProb >= 0.45 ? 'rgba(59,130,246,0.15)' : 'rgba(245,158,11,0.15)',
                            border: `1px solid ${winProb >= 0.55 ? 'rgba(16,185,129,0.3)' : winProb >= 0.45 ? 'rgba(59,130,246,0.3)' : 'rgba(245,158,11,0.3)'}`
                          }}>
                            <p style={{ fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: '0.15rem' }}>Win Prob</p>
                            <p style={{ fontSize: '1.25rem', fontWeight: 700, color: winProb >= 0.55 ? '#10b981' : winProb >= 0.45 ? '#3b82f6' : '#f59e0b' }}>
                              {(winProb * 100).toFixed(0)}%
                            </p>
                          </div>
                          <div style={{
                            padding: '0.5rem 0.75rem',
                            borderRadius: '8px',
                            background: teamEdge >= 0 ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
                            border: `1px solid ${teamEdge >= 0 ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`
                          }}>
                            <p style={{ fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: '0.15rem' }}>Model Edge</p>
                            <p style={{ fontSize: '1.25rem', fontWeight: 700, color: teamEdge >= 0 ? '#10b981' : '#ef4444' }}>
                              {teamEdge >= 0 ? '+' : ''}{(teamEdge * 100).toFixed(1)}
                            </p>
                          </div>
                        </div>
                        <span style={{
                          padding: '0.25rem 0.5rem',
                          borderRadius: '4px',
                          fontSize: '0.7rem',
                          fontWeight: 600,
                          background: game.confidenceGrade === 'A' ? 'rgba(16,185,129,0.2)' : game.confidenceGrade === 'B' ? 'rgba(59,130,246,0.2)' : 'rgba(245,158,11,0.2)',
                          color: game.confidenceGrade === 'A' ? '#10b981' : game.confidenceGrade === 'B' ? '#3b82f6' : '#f59e0b',
                        }}>{game.confidenceGrade}-tier confidence</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="card" style={{ padding: '2rem', textAlign: 'center' }}>
              <p style={{ fontSize: '1rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>No games scheduled for today</p>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>Check back on game days for model predictions</p>
            </div>
          )}
        </section>

        {/* Projected Lineup */}
        <section className="nova-section">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold text-white">Projected Lineup</h2>
              <p className="text-sm text-white/50 mt-1">Players ranked by TOI, points, and performance metrics</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-white/40">
                Updated: {new Date(projectedLineup.lastUpdated).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              </span>
              <Link href="/players" className="text-sm text-sky-400 hover:text-sky-300 transition-colors">
                All Players →
              </Link>
            </div>
          </div>
          <ProjectedLineupDisplay lineup={projectedLineup} />
        </section>

        {/* Player Statistics */}
        {allSkaters.length > 0 && (
          <section className="nova-section">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-xl font-bold text-white">Skater Statistics</h2>
                <p className="text-sm text-white/50 mt-1">Current season stats for team skaters</p>
              </div>
              <Link href="/players" className="text-sm text-sky-400 hover:text-sky-300 transition-colors font-medium">
                League Leaders →
              </Link>
            </div>
            <div className="rounded-xl border border-white/[0.06] bg-gradient-to-b from-white/[0.02] to-transparent overflow-hidden">
              <SkaterStatsTable
                players={allSkaters}
                showTeam={false}
                maxRows={15}
                linkToProfile={true}
              />
            </div>
          </section>
        )}

        {/* Goalie Statistics */}
        {roster.goalies.length > 0 && (
          <section className="nova-section">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-xl font-bold text-white">Goalie Statistics</h2>
                <p className="text-sm text-white/50 mt-1">Current season stats for team goalies</p>
              </div>
            </div>
            <div className="rounded-xl border border-white/[0.06] bg-gradient-to-b from-white/[0.02] to-transparent overflow-hidden">
              <GoalieStatsTable
                goalies={roster.goalies}
                showTeam={false}
                showRank={false}
                linkToProfile={true}
              />
            </div>
          </section>
        )}

        {/* Division Standings */}
        {teamDivision && (
          <section className="nova-section">
            <h2 className="text-xl font-bold text-white mb-3">{teamDivision.name} Division</h2>
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              {divisionStandings.map((team, idx) => {
                const isCurrent = team.abbrev === teamData.abbrev;
                return (
                  <div key={team.abbrev} style={{
                    display: 'flex', alignItems: 'center', padding: '0.75rem 1rem',
                    background: isCurrent ? 'rgba(59,130,246,0.15)' : idx % 2 ? 'rgba(255,255,255,0.02)' : 'transparent',
                    borderLeft: isCurrent ? '3px solid #3b82f6' : '3px solid transparent'
                  }}>
                    <span style={{ width: '24px', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-tertiary)' }}>{idx + 1}</span>
                    <TeamCrest abbrev={team.abbrev} size={28} />
                    <span style={{ marginLeft: '0.75rem', flex: 1, fontSize: '0.9rem', fontWeight: isCurrent ? 600 : 400, color: isCurrent ? 'white' : 'var(--text-secondary)' }}>{team.team}</span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginRight: '1rem' }}>{team.record}</span>
                    <span style={{ fontSize: '0.75rem', color: getRankColor(team.powerRank), marginRight: '0.75rem' }}>#{team.powerRank}</span>
                    <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'white', width: '35px', textAlign: 'right' }}>{team.points}</span>
                  </div>
                );
              })}
            </div>
          </section>
        )}

      </div>
    </div>
  );
}
