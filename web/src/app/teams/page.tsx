import Link from "next/link";
import { buildTeamSnapshots, computeStandingsPowerScore, formatPowerScore, getCurrentStandings } from "@/lib/current";
import { TeamLogo } from "@/components/TeamLogo";
import { TeamCrest } from "@/components/TeamCrest";

const snapshots = buildTeamSnapshots();
const standings = getCurrentStandings();

const allTeams = standings
  .map((team) => {
    const snap = snapshots.find((s) => s.abbrev === team.abbrev);
    const avgProb = snap?.avgProb ?? team.pointPctg ?? 0.5;
    const powerScore = snap ? formatPowerScore(snap) : computeStandingsPowerScore({ ...team, rank: team.rank });
    return {
      team: team.team,
      abbrev: team.abbrev,
      record: `${team.wins}-${team.losses}-${team.ot}`,
      points: team.points,
      avgProb,
      powerScore,
    };
  })
  .sort((a, b) => a.team.localeCompare(b.team)); // Sort alphabetically by team name

// Get top 5 teams by points for the visual
const topTeams = [...standings].sort((a, b) => b.points - a.points).slice(0, 5);
const maxPoints = topTeams[0]?.points ?? 1;

export default function TeamsIndexPage() {
  return (
    <div className="min-h-screen">
      <div className="container">
        <section className="nova-hero nav-offset">
          <div className="nova-hero__grid">
            <div className="nova-hero__text">
              <div className="pill-row">
                <span className="pill">Team Index</span>
                <span className="pill">All 32 teams</span>
              </div>
              <h1 className="display-xl">Find your team.</h1>
              <p className="lead">
                Browse all 32 NHL teams alphabetically. Tap any team to view detailed stats, upcoming games, and goalie performance.
              </p>
              <div className="chip-row">
                <span className="chip-soft">Alphabetically sorted</span>
                <span className="chip-soft">Updated with live data</span>
              </div>
            </div>

            {/* League Leaders Mini Visual */}
            <div className="nova-hero__panel">
              <p style={{ fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-tertiary)', marginBottom: '1rem' }}>
                League Leaders
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                {topTeams.map((team, idx) => (
                  <div key={team.abbrev} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <span style={{ width: '1.25rem', fontSize: '0.8rem', fontWeight: 700, color: idx === 0 ? 'var(--mint)' : 'var(--text-tertiary)' }}>
                      {idx + 1}
                    </span>
                    <TeamCrest abbrev={team.abbrev} size={32} />
                    <div style={{ flex: 1 }}>
                      <div style={{ height: '0.5rem', background: 'rgba(255,255,255,0.1)', borderRadius: '0.25rem', overflow: 'hidden' }}>
                        <div style={{
                          width: `${(team.points / maxPoints) * 100}%`,
                          height: '100%',
                          background: idx === 0 ? 'linear-gradient(90deg, var(--aqua), var(--mint))' : 'var(--aqua)',
                          borderRadius: '0.25rem'
                        }} />
                      </div>
                    </div>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', minWidth: '2.5rem', textAlign: 'right' }}>
                      {team.points}
                    </span>
                  </div>
                ))}
              </div>
              <Link href="/leaderboards" className="cta cta-ghost" style={{ width: '100%', justifyContent: 'center', marginTop: '1rem' }}>
                Full Power Index →
              </Link>
            </div>
          </div>
        </section>

        <section className="nova-section">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {allTeams.map((team) => (
              <Link key={team.abbrev} href={`/teams/${team.abbrev.toLowerCase()}`} className="card group">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0">
                    <TeamLogo teamAbbrev={team.abbrev} size="md" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-bold text-white group-hover:text-cyan-400 transition-colors leading-tight mb-1">
                      {team.team}
                    </h3>
                    <p className="text-sm text-white/60">{team.record}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="chip-soft chip-soft--mini">{team.points} pts</span>
                      <span className="chip-soft chip-soft--mini">{(team.avgProb * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
