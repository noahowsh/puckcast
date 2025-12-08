import Link from "next/link";
import { fetchGoalieLeaders, fetchGoalieStats } from "@/lib/playerHub";
import { GoalieStatsTable, LeaderRow } from "@/components/PlayerStatsTable";
import { GoalieCardView } from "@/components/PlayerCard";

export const revalidate = 3600; // Revalidate every hour

export default async function GoaliePage() {
  const [goalieLeaders, allGoalies] = await Promise.all([
    fetchGoalieLeaders(),
    fetchGoalieStats(3),
  ]);

  const updatedAt = new Date().toLocaleString("en-US", { timeZone: "America/New_York", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });

  // Get top performers for hero panel
  const topBySavePct = goalieLeaders.savePct[0];
  const topByWins = goalieLeaders.wins[0];
  const totalGoalies = allGoalies.length;

  return (
    <div className="min-h-screen">
      <div className="container">
        {/* Nova Hero Section */}
        <section className="nova-hero">
          <div className="nova-hero__grid">
            <div className="nova-hero__text">
              <div className="pill-row">
                <span className="pill">2025-26 Season</span>
                <span className="pill">Updated {updatedAt} ET</span>
              </div>
              <h1 className="display-xl">Goaltending breakdown.</h1>
              <p className="lead">
                Deep analysis of every starter and backup in the league. Save percentages, goals against averages,
                win totals, and workload metrics for informed lineup decisions.
              </p>
              <div className="cta-row">
                <Link href="/players" className="cta cta-ghost">
                  ← Back to Player Stats
                </Link>
              </div>
            </div>

            {/* Hero Panel - Top Goalies */}
            <div className="nova-hero__panel" style={{ padding: '1.25rem' }}>
              <p style={{ fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-tertiary)', marginBottom: '0.75rem' }}>
                Goaltending Leaders
              </p>

              {topBySavePct && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem', background: 'rgba(110, 240, 194, 0.08)', borderRadius: '0.75rem', border: '1px solid rgba(110, 240, 194, 0.2)', marginBottom: '0.5rem' }}>
                  <div style={{ width: '2.5rem', height: '2.5rem', borderRadius: '50%', background: 'linear-gradient(135deg, rgba(110, 240, 194, 0.2), rgba(126, 227, 255, 0.2))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '0.9rem', color: 'var(--mint)' }}>
                    1
                  </div>
                  <div style={{ flex: 1 }}>
                    <p style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-tertiary)', fontWeight: 600, marginBottom: '0.1rem' }}>Save % Leader</p>
                    <p style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>{topBySavePct.bio.fullName}</p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <p style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--mint)' }}>.{Math.round(topBySavePct.stats.savePct * 1000)}</p>
                    <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>SV%</p>
                  </div>
                </div>
              )}

              {topByWins && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem', background: 'rgba(126, 227, 255, 0.08)', borderRadius: '0.75rem', border: '1px solid rgba(126, 227, 255, 0.2)' }}>
                  <div style={{ width: '2.5rem', height: '2.5rem', borderRadius: '50%', background: 'linear-gradient(135deg, rgba(126, 227, 255, 0.2), rgba(110, 240, 194, 0.2))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '0.9rem', color: 'var(--aqua)' }}>
                    1
                  </div>
                  <div style={{ flex: 1 }}>
                    <p style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-tertiary)', fontWeight: 600, marginBottom: '0.1rem' }}>Wins Leader</p>
                    <p style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>{topByWins.bio.fullName}</p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <p style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--aqua)' }}>{topByWins.stats.wins}</p>
                    <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>W</p>
                  </div>
                </div>
              )}

              {/* Summary stats */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', paddingTop: '0.75rem', marginTop: '0.75rem', borderTop: '1px solid var(--border-subtle)' }}>
                <div style={{ textAlign: 'center' }}>
                  <p style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>{totalGoalies}</p>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Goalies tracked</p>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <p style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>3+</p>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Min GP filter</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* League Leaders Section */}
        <section className="nova-section">
          <div className="section-head">
            <div>
              <p className="eyebrow">Between the pipes</p>
              <h2>League Leaders</h2>
              <p className="lead-sm">Top 5 in each major goaltending category.</p>
            </div>
          </div>

          <div className="bento-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
            {/* Wins */}
            <div className="bento-card">
              <p className="micro-label">Wins</p>
              <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Win Leaders</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                {goalieLeaders.wins.slice(0, 5).map((goalie, idx) => (
                  <LeaderRow
                    key={goalie.bio.playerId}
                    rank={idx + 1}
                    name={goalie.bio.lastName}
                    team={goalie.bio.teamAbbrev}
                    value={goalie.stats.wins}
                    playerId={goalie.bio.playerId}
                    isGoalie
                  />
                ))}
              </div>
            </div>

            {/* Save Percentage */}
            <div className="bento-card">
              <p className="micro-label">Save %</p>
              <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Stop Rate</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                {goalieLeaders.savePct.slice(0, 5).map((goalie, idx) => (
                  <LeaderRow
                    key={goalie.bio.playerId}
                    rank={idx + 1}
                    name={goalie.bio.lastName}
                    team={goalie.bio.teamAbbrev}
                    value={`.${Math.round(goalie.stats.savePct * 1000)}`}
                    playerId={goalie.bio.playerId}
                    isGoalie
                  />
                ))}
              </div>
            </div>

            {/* GAA */}
            <div className="bento-card">
              <p className="micro-label">GAA</p>
              <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Goals Against</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                {goalieLeaders.goalsAgainstAverage.slice(0, 5).map((goalie, idx) => (
                  <LeaderRow
                    key={goalie.bio.playerId}
                    rank={idx + 1}
                    name={goalie.bio.lastName}
                    team={goalie.bio.teamAbbrev}
                    value={goalie.stats.goalsAgainstAverage.toFixed(2)}
                    playerId={goalie.bio.playerId}
                    isGoalie
                  />
                ))}
              </div>
            </div>

            {/* Shutouts */}
            <div className="bento-card">
              <p className="micro-label">Shutouts</p>
              <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Clean Sheets</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                {goalieLeaders.shutouts.slice(0, 5).map((goalie, idx) => (
                  <LeaderRow
                    key={goalie.bio.playerId}
                    rank={idx + 1}
                    name={goalie.bio.lastName}
                    team={goalie.bio.teamAbbrev}
                    value={goalie.stats.shutouts}
                    playerId={goalie.bio.playerId}
                    isGoalie
                  />
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Top Performers Cards */}
        <section className="nova-section" style={{ paddingTop: 0 }}>
          <div className="section-head">
            <div>
              <p className="eyebrow">Detailed profiles</p>
              <h2>Top Performers</h2>
              <p className="lead-sm">In-depth look at the league&apos;s leading netminders.</p>
            </div>
          </div>

          <div className="bento-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))' }}>
            {goalieLeaders.wins.slice(0, 4).map((goalie, idx) => (
              <GoalieCardView key={goalie.bio.playerId} goalie={goalie} rank={idx + 1} />
            ))}
          </div>
        </section>

        {/* Full Stats Table */}
        <section className="nova-section" style={{ paddingTop: 0 }}>
          <div className="section-head">
            <div>
              <p className="eyebrow">Complete data</p>
              <h2>All Goalies</h2>
              <p className="lead-sm">Full statistical breakdown for every qualified goaltender.</p>
            </div>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <p className="chip-soft">Minimum 3 games played</p>
          </div>
          <div className="table-container" style={{ borderRadius: '20px' }}>
            <GoalieStatsTable goalies={allGoalies} maxRows={30} />
          </div>
        </section>
      </div>
    </div>
  );
}
