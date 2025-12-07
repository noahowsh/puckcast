import { notFound } from "next/navigation";
import { computeStandingsPowerScore, getCurrentStandings, getCurrentPredictions } from "@/lib/current";
import { TeamCrest } from "@/components/TeamCrest";
import goaliePulseRaw from "@/data/goaliePulse.json";
import powerIndexSnapshot from "@/data/powerIndexSnapshot.json";
import type { GoaliePulse } from "@/types/goalie";

const goaliePulse = goaliePulseRaw as GoaliePulse;
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
  for (const [key, div] of Object.entries(divisions)) {
    if (div.teams.includes(abbrev)) {
      return { key, ...div };
    }
  }
  return null;
}

// Get league-wide stats for comparison
const leagueStats = {
  maxGoalsFor: Math.max(...standings.map(t => t.goalsForPerGame ?? 0)),
  minGoalsFor: Math.min(...standings.map(t => t.goalsForPerGame ?? 0)),
  avgGoalsFor: standings.reduce((sum, t) => sum + (t.goalsForPerGame ?? 0), 0) / standings.length,
  avgGoalsAgainst: standings.reduce((sum, t) => sum + (t.goalsAgainstPerGame ?? 0), 0) / standings.length,
  maxPointPctg: Math.max(...standings.map(t => t.pointPctg ?? 0)),
};

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
  return standings.map((team) => ({
    abbrev: team.abbrev.toLowerCase(),
  }));
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

  // Get ALL upcoming games for this team from predictions
  const upcomingGames = predictions.games.filter(
    (game) => game.homeTeam.abbrev === teamData.abbrev || game.awayTeam.abbrev === teamData.abbrev
  );

  // Get team goalies
  const teamGoalies = goaliePulse.goalies.filter((g) => g.team === teamData.abbrev);

  // Calculate efficiency metrics
  const shootingPct = teamData.goalsForPerGame && teamData.shotsForPerGame
    ? (teamData.goalsForPerGame / teamData.shotsForPerGame * 100) : 0;
  const savePct = teamData.goalsAgainstPerGame && teamData.shotsAgainstPerGame
    ? ((1 - teamData.goalsAgainstPerGame / teamData.shotsAgainstPerGame) * 100) : 0;

  // League ranks
  const ranks = {
    offense: getLeagueRank(teamData.abbrev, 'goalsForPerGame'),
    defense: getLeagueRank(teamData.abbrev, 'goalsAgainstPerGame', true),
    shotsFor: getLeagueRank(teamData.abbrev, 'shotsForPerGame'),
    shotsAgainst: getLeagueRank(teamData.abbrev, 'shotsAgainstPerGame', true),
    goalDiff: getLeagueRank(teamData.abbrev, 'goalDifferential'),
    pointPct: getLeagueRank(teamData.abbrev, 'pointPctg'),
  };

  return (
    <div className="min-h-screen">
      <div className="container">
        {/* Simplified Hero Section */}
        <section className="nova-hero nav-offset">
          <div className="nova-hero__grid nova-hero__grid--balanced">
            <div className="nova-hero__text">
              <h1 className="display-xl">{teamData.team}</h1>
              <p className="lead">
                {teamDivision?.name} Division • {teamDivision?.conference} Conference
              </p>

              {/* Key Stats Row */}
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
              <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', marginBottom: '1.25rem' }}>
                <div style={{ position: 'relative' }}>
                  <svg width="100" height="100" viewBox="0 0 100 100" style={{ transform: 'rotate(-90deg)' }}>
                    <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="8" />
                    <circle cx="50" cy="50" r="42" fill="none" stroke={getRankColor(teamData.powerRank)} strokeWidth="8"
                      strokeDasharray={`${((33 - teamData.powerRank) / 32) * 264} 264`} strokeLinecap="round" />
                  </svg>
                  <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}>
                    <TeamCrest abbrev={teamData.abbrev} size={48} />
                  </div>
                </div>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: '2.5rem', fontWeight: 800, color: 'white', lineHeight: 1 }}>#{teamData.powerRank}</p>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginTop: '0.25rem' }}>Power Index</p>
                  <p style={{ fontSize: '0.8rem', color: movement > 0 ? '#10b981' : movement < 0 ? '#ef4444' : 'var(--text-tertiary)', marginTop: '0.25rem' }}>
                    {movement > 0 ? `▲ ${movement} above` : movement < 0 ? `▼ ${Math.abs(movement)} below` : '● Even with'} standings (#{teamData.rank})
                  </p>
                </div>
              </div>

              {/* Record Display */}
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
                  <div style={{ width: `${(teamData.ot / teamData.gamesPlayed) * 100}%`, background: '#f59e0b', display: 'flex', alignItems: 'center', justifyContent: 'center', minWidth: teamData.ot > 0 ? '30px' : 0 }}>
                    <span style={{ fontSize: '0.7rem', fontWeight: 600, color: 'white' }}>{teamData.ot}OT</span>
                  </div>
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

        {/* League Rankings */}
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
          </div>
        </section>

        {/* Efficiency Cards */}
        <section className="nova-section">
          <h2 className="text-xl font-bold text-white mb-3">Efficiency</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="card" style={{ padding: '1.25rem', background: 'linear-gradient(135deg, rgba(16,185,129,0.08), transparent)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'rgba(16,185,129,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <span style={{ fontSize: '1.25rem' }}>🎯</span>
                </div>
                <div>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Shooting %</p>
                  <p style={{ fontSize: '1.75rem', fontWeight: 700, color: '#10b981', lineHeight: 1 }}>{shootingPct.toFixed(1)}%</p>
                </div>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.75rem' }}>
                {teamData.goalsForPerGame?.toFixed(2)} goals on {teamData.shotsForPerGame?.toFixed(1)} shots/game
              </p>
            </div>
            <div className="card" style={{ padding: '1.25rem', background: 'linear-gradient(135deg, rgba(59,130,246,0.08), transparent)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'rgba(59,130,246,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <span style={{ fontSize: '1.25rem' }}>🧤</span>
                </div>
                <div>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Team Save %</p>
                  <p style={{ fontSize: '1.75rem', fontWeight: 700, color: '#3b82f6', lineHeight: 1 }}>{savePct.toFixed(1)}%</p>
                </div>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.75rem' }}>
                {teamData.goalsAgainstPerGame?.toFixed(2)} GA on {teamData.shotsAgainstPerGame?.toFixed(1)} shots faced
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

        {/* Goaltending */}
        {teamGoalies.length > 0 && (
          <section className="nova-section">
            <h2 className="text-xl font-bold text-white mb-3">Goaltending</h2>
            <div className="grid gap-3 sm:grid-cols-2">
              {teamGoalies.map((goalie) => (
                <div key={goalie.name} className="card" style={{ padding: '1.25rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                    <div style={{
                      width: '48px', height: '48px', borderRadius: '50%',
                      background: goalie.trend === 'surging' ? 'rgba(16,185,129,0.2)' : goalie.trend === 'steady' ? 'rgba(59,130,246,0.2)' : 'rgba(255,255,255,0.1)',
                      border: `2px solid ${goalie.trend === 'surging' ? '#10b981' : goalie.trend === 'steady' ? '#3b82f6' : 'rgba(255,255,255,0.2)'}`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center'
                    }}>
                      <span style={{ fontSize: '1.25rem' }}>🥅</span>
                    </div>
                    <div style={{ flex: 1 }}>
                      <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'white', margin: 0 }}>{goalie.name}</h3>
                      <span style={{
                        fontSize: '0.65rem', fontWeight: 600, textTransform: 'uppercase',
                        color: goalie.trend === 'surging' ? '#10b981' : goalie.trend === 'steady' ? '#3b82f6' : 'var(--text-tertiary)'
                      }}>{goalie.trend}</span>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <p style={{ fontSize: '1.25rem', fontWeight: 700, color: goalie.seasonGsa > 0 ? '#10b981' : goalie.seasonGsa < -5 ? '#ef4444' : 'white' }}>
                        {goalie.seasonGsa > 0 ? '+' : ''}{goalie.seasonGsa.toFixed(1)}
                      </p>
                      <p style={{ fontSize: '0.6rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>GSAx</p>
                    </div>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>{goalie.note}</p>
                  <div style={{ display: 'flex', gap: '1rem', marginTop: '0.75rem' }}>
                    <div><span style={{ fontSize: '0.65rem', color: 'var(--text-tertiary)' }}>Rolling:</span> <span style={{ fontWeight: 600, color: goalie.rollingGsa > 0 ? '#10b981' : 'white' }}>{goalie.rollingGsa > 0 ? '+' : ''}{goalie.rollingGsa.toFixed(1)}</span></div>
                    <div><span style={{ fontSize: '0.65rem', color: 'var(--text-tertiary)' }}>Rest:</span> <span style={{ fontWeight: 600, color: 'white' }}>{goalie.restDays}d</span></div>
                    <div><span style={{ fontSize: '0.65rem', color: 'var(--text-tertiary)' }}>Start:</span> <span style={{ fontWeight: 600, color: goalie.startLikelihood > 0.7 ? '#10b981' : 'white' }}>{(goalie.startLikelihood * 100).toFixed(0)}%</span></div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Upcoming Games */}
        <section className="nova-section">
          <h2 className="text-xl font-bold text-white mb-3">Upcoming Games</h2>
          {upcomingGames.length > 0 ? (
            <div className="grid gap-2">
              {upcomingGames.map((game) => {
                const isHome = game.homeTeam.abbrev === teamData.abbrev;
                const opponent = isHome ? game.awayTeam : game.homeTeam;
                const winProb = isHome ? game.homeWinProb : game.awayWinProb;
                const teamEdge = isHome ? game.edge : -game.edge;
                return (
                  <div key={game.id} className="card" style={{ padding: '1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <TeamCrest abbrev={opponent.abbrev} size={40} />
                      <div style={{ flex: 1 }}>
                        <p style={{ fontSize: '0.95rem', fontWeight: 600, color: 'white' }}>{isHome ? "vs" : "@"} {opponent.name}</p>
                        <p style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>{game.gameDate} • {game.startTimeEt ?? "TBD"}</p>
                      </div>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <span style={{ padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 600,
                          background: winProb >= 0.55 ? 'rgba(16,185,129,0.2)' : winProb >= 0.45 ? 'rgba(59,130,246,0.2)' : 'rgba(245,158,11,0.2)',
                          color: winProb >= 0.55 ? '#10b981' : winProb >= 0.45 ? '#3b82f6' : '#f59e0b'
                        }}>{(winProb * 100).toFixed(0)}%</span>
                        <span style={{ padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 600,
                          background: teamEdge >= 0 ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)',
                          color: teamEdge >= 0 ? '#10b981' : '#ef4444'
                        }}>{teamEdge >= 0 ? '+' : ''}{(teamEdge * 100).toFixed(1)}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="card" style={{ padding: '2rem', textAlign: 'center' }}>
              <p style={{ color: 'var(--text-tertiary)' }}>No games in current prediction window</p>
            </div>
          )}
        </section>

        {/* Division Rivals */}
        {teamDivision && (
          <section className="nova-section">
            <h2 className="text-xl font-bold text-white mb-3">{teamDivision.name} Division</h2>
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              {divisionStandings.map((team, idx) => {
                const isCurrent = team.abbrev === teamData.abbrev;
                return (
                  <div key={team.abbrev} style={{
                    display: 'flex', alignItems: 'center', padding: '0.6rem 1rem',
                    background: isCurrent ? 'rgba(59,130,246,0.15)' : idx % 2 ? 'rgba(255,255,255,0.02)' : 'transparent',
                    borderLeft: isCurrent ? '3px solid #3b82f6' : '3px solid transparent'
                  }}>
                    <span style={{ width: '20px', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-tertiary)' }}>{idx + 1}</span>
                    <TeamCrest abbrev={team.abbrev} size={24} />
                    <span style={{ marginLeft: '0.5rem', flex: 1, fontSize: '0.85rem', fontWeight: isCurrent ? 600 : 400, color: isCurrent ? 'white' : 'var(--text-secondary)' }}>{team.team}</span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginRight: '0.75rem' }}>{team.record}</span>
                    <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'white', width: '30px', textAlign: 'right' }}>{team.points}</span>
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
