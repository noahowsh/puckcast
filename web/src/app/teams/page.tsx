import Link from "next/link";
import { computeStandingsPowerScore, getCurrentStandings } from "@/lib/current";
import { TeamLogo } from "@/components/TeamLogo";
import { TeamCrest } from "@/components/TeamCrest";
import { fetchSkaterLeaders, fetchGoalieLeaders } from "@/lib/playerHub";

export const revalidate = 3600; // Revalidate every hour

const standings = getCurrentStandings();

// Build power rankings for all teams
const powerRankings = [...standings]
  .map(team => ({ ...team, powerScore: computeStandingsPowerScore(team) }))
  .sort((a, b) => b.powerScore - a.powerScore)
  .map((team, idx) => ({ ...team, powerRank: idx + 1 }));

const allTeams = powerRankings
  .map((team) => ({
    team: team.team,
    abbrev: team.abbrev,
    record: `${team.wins}-${team.losses}-${team.ot}`,
    points: team.points,
    pointPctg: team.pointPctg,
    powerRank: team.powerRank,
    powerScore: team.powerScore,
  }))
  .sort((a, b) => a.team.localeCompare(b.team)); // Sort alphabetically by team name

// Get top 5 teams by points for the visual
const topTeams = [...standings].sort((a, b) => b.points - a.points).slice(0, 5);
const maxPoints = topTeams[0]?.points ?? 1;

export default async function TeamsIndexPage() {
  // Fetch player leaders for preview
  const [skaterLeaders, goalieLeaders] = await Promise.all([
    fetchSkaterLeaders(),
    fetchGoalieLeaders(),
  ]);

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

        {/* Quick Navigation */}
        <section className="nova-section">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <Link href="/players" className="card p-4 hover:border-sky-500/30 transition-all group">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-sky-500/20 flex items-center justify-center">
                  <svg className="w-5 h-5 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-white group-hover:text-sky-400 transition-colors">Player Stats</h3>
                  <p className="text-xs text-white/50">League leaders & full stats</p>
                </div>
              </div>
              <div className="space-y-1">
                {skaterLeaders.points.slice(0, 3).map((p, idx) => (
                  <div key={p.bio.playerId} className="flex items-center justify-between text-sm">
                    <span className="text-white/70">{idx + 1}. {p.bio.lastName}</span>
                    <span className="text-sky-300 font-semibold">{p.stats.points} pts</span>
                  </div>
                ))}
              </div>
            </Link>

            <Link href="/goalies" className="card p-4 hover:border-emerald-500/30 transition-all group">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                  <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-white group-hover:text-emerald-400 transition-colors">Goalie Intelligence</h3>
                  <p className="text-xs text-white/50">GSAx, trends & analysis</p>
                </div>
              </div>
              <div className="space-y-1">
                {goalieLeaders.wins.slice(0, 3).map((g, idx) => (
                  <div key={g.bio.playerId} className="flex items-center justify-between text-sm">
                    <span className="text-white/70">{idx + 1}. {g.bio.lastName}</span>
                    <span className="text-emerald-300 font-semibold">{g.stats.wins} W</span>
                  </div>
                ))}
              </div>
            </Link>

            <Link href="/leaderboards" className="card p-4 hover:border-amber-500/30 transition-all group">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-amber-500/20 flex items-center justify-center">
                  <svg className="w-5 h-5 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-white group-hover:text-amber-400 transition-colors">Power Rankings</h3>
                  <p className="text-xs text-white/50">Model-driven team index</p>
                </div>
              </div>
              <div className="space-y-1">
                {topTeams.slice(0, 3).map((t, idx) => (
                  <div key={t.abbrev} className="flex items-center justify-between text-sm">
                    <span className="text-white/70">{idx + 1}. {t.team.split(' ').pop()}</span>
                    <span className="text-amber-300 font-semibold">{t.points} pts</span>
                  </div>
                ))}
              </div>
            </Link>
          </div>
        </section>

        {/* All Teams */}
        <section className="nova-section">
          <h2 className="text-xl font-bold text-white mb-4">All 32 Teams</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {allTeams.map((team) => (
              <Link key={team.abbrev} href={`/teams/${team.abbrev.toLowerCase()}`} className="card group p-4">
                <div className="flex items-center gap-4">
                  <div className="flex-shrink-0">
                    <TeamLogo teamAbbrev={team.abbrev} size="lg" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-bold text-white group-hover:text-cyan-400 transition-colors leading-tight mb-1">
                      {team.team}
                    </h3>
                    <p className="text-sm text-white/60 mb-2">{team.record}</p>
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="chip-soft chip-soft--mini">{team.points} pts</span>
                      <span className="chip-soft chip-soft--mini">{(team.pointPctg * 100).toFixed(0)}%</span>
                      <span className="chip-soft chip-soft--mini">#{team.powerRank}</span>
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
