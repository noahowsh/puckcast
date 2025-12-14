import Link from "next/link";
import { fetchSkaterLeaders, fetchEnrichedSkaterStats } from "@/lib/playerHub";
import { SkaterStatsTable, LeaderRow } from "@/components/PlayerStatsTable";
import { PlayerCardView } from "@/components/PlayerCard";

export const revalidate = 3600; // Revalidate every hour

export default async function SkatersPage() {
  const [skaterLeaders, allSkaters] = await Promise.all([
    fetchSkaterLeaders(),
    fetchEnrichedSkaterStats(5),
  ]);

  const updatedAt = new Date().toLocaleString("en-US", { timeZone: "America/New_York", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });

  // Get top performers for hero panel
  const topByPoints = skaterLeaders.points[0];
  const topByGoals = skaterLeaders.goals[0];
  const totalSkaters = allSkaters.length;

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
              <h1 className="display-xl">Skater intelligence.</h1>
              <p className="lead">
                Complete statistical breakdown for every forward and defenseman in the league.
                Points, goals, assists, plus/minus, and advanced metrics for informed analysis.
              </p>
              <div className="cta-row">
                <Link href="/players" className="cta cta-ghost">
                  ← Back to Player Stats
                </Link>
              </div>
            </div>

            {/* Hero Panel - Top Skaters */}
            <div className="nova-hero__panel" style={{ padding: '1.25rem' }}>
              <p style={{ fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-tertiary)', marginBottom: '0.75rem' }}>
                Scoring Leaders
              </p>

              {topByPoints && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem', background: 'rgba(126, 227, 255, 0.08)', borderRadius: '0.75rem', border: '1px solid rgba(126, 227, 255, 0.2)', marginBottom: '0.5rem' }}>
                  <div style={{ width: '2.5rem', height: '2.5rem', borderRadius: '50%', background: 'linear-gradient(135deg, rgba(126, 227, 255, 0.2), rgba(110, 240, 194, 0.2))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '0.9rem', color: 'var(--aqua)' }}>
                    1
                  </div>
                  <div style={{ flex: 1 }}>
                    <p style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-tertiary)', fontWeight: 600, marginBottom: '0.1rem' }}>Points Leader</p>
                    <p style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>{topByPoints.bio.fullName}</p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <p style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--aqua)' }}>{topByPoints.stats.points}</p>
                    <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>PTS</p>
                  </div>
                </div>
              )}

              {topByGoals && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem', background: 'rgba(110, 240, 194, 0.08)', borderRadius: '0.75rem', border: '1px solid rgba(110, 240, 194, 0.2)' }}>
                  <div style={{ width: '2.5rem', height: '2.5rem', borderRadius: '50%', background: 'linear-gradient(135deg, rgba(110, 240, 194, 0.2), rgba(126, 227, 255, 0.2))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '0.9rem', color: 'var(--mint)' }}>
                    1
                  </div>
                  <div style={{ flex: 1 }}>
                    <p style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-tertiary)', fontWeight: 600, marginBottom: '0.1rem' }}>Goals Leader</p>
                    <p style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>{topByGoals.bio.fullName}</p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <p style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--mint)' }}>{topByGoals.stats.goals}</p>
                    <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>G</p>
                  </div>
                </div>
              )}

              {/* Summary stats */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', paddingTop: '0.75rem', marginTop: '0.75rem', borderTop: '1px solid var(--border-subtle)' }}>
                <div style={{ textAlign: 'center' }}>
                  <p style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>{totalSkaters}</p>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Skaters tracked</p>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <p style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>5+</p>
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
              <p className="eyebrow">The scoring race</p>
              <h2>League Leaders</h2>
              <p className="lead-sm">Top 5 in each major scoring category.</p>
            </div>
          </div>

          <div className="bento-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
            {/* Points */}
            <div className="bento-card">
              <p className="micro-label">Points</p>
              <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Total Scoring</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                {skaterLeaders.points.slice(0, 5).map((player, idx) => (
                  <LeaderRow
                    key={player.bio.playerId}
                    rank={idx + 1}
                    name={player.bio.lastName}
                    team={player.bio.teamAbbrev}
                    value={player.stats.points}
                    playerId={player.bio.playerId}
                  />
                ))}
              </div>
            </div>

            {/* Goals */}
            <div className="bento-card">
              <p className="micro-label">Goals</p>
              <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Lamp Lighters</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                {skaterLeaders.goals.slice(0, 5).map((player, idx) => (
                  <LeaderRow
                    key={player.bio.playerId}
                    rank={idx + 1}
                    name={player.bio.lastName}
                    team={player.bio.teamAbbrev}
                    value={player.stats.goals}
                    playerId={player.bio.playerId}
                  />
                ))}
              </div>
            </div>

            {/* Assists */}
            <div className="bento-card">
              <p className="micro-label">Assists</p>
              <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Playmakers</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                {skaterLeaders.assists.slice(0, 5).map((player, idx) => (
                  <LeaderRow
                    key={player.bio.playerId}
                    rank={idx + 1}
                    name={player.bio.lastName}
                    team={player.bio.teamAbbrev}
                    value={player.stats.assists}
                    playerId={player.bio.playerId}
                  />
                ))}
              </div>
            </div>

            {/* Plus/Minus */}
            <div className="bento-card">
              <p className="micro-label">Plus/Minus</p>
              <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>On-Ice Impact</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                {skaterLeaders.plusMinus.slice(0, 5).map((player, idx) => (
                  <LeaderRow
                    key={player.bio.playerId}
                    rank={idx + 1}
                    name={player.bio.lastName}
                    team={player.bio.teamAbbrev}
                    value={`+${player.stats.plusMinus}`}
                    playerId={player.bio.playerId}
                  />
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Specialty Stats Section */}
        <section className="nova-section" style={{ paddingTop: 0 }}>
          <div className="section-head">
            <div>
              <p className="eyebrow">Advanced metrics</p>
              <h2>Specialty Leaders</h2>
              <p className="lead-sm">Power play, game winners, and shot volume.</p>
            </div>
          </div>

          <div className="bento-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
            {/* Power Play Goals */}
            <div className="bento-card">
              <p className="micro-label">Power Play Goals</p>
              <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Man Advantage</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                {skaterLeaders.powerPlayGoals.slice(0, 5).map((player, idx) => (
                  <LeaderRow
                    key={player.bio.playerId}
                    rank={idx + 1}
                    name={player.bio.lastName}
                    team={player.bio.teamAbbrev}
                    value={player.stats.powerPlayGoals}
                    playerId={player.bio.playerId}
                  />
                ))}
              </div>
            </div>

            {/* Game Winning Goals */}
            <div className="bento-card">
              <p className="micro-label">Game Winners</p>
              <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Clutch Performers</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                {skaterLeaders.gameWinningGoals.slice(0, 5).map((player, idx) => (
                  <LeaderRow
                    key={player.bio.playerId}
                    rank={idx + 1}
                    name={player.bio.lastName}
                    team={player.bio.teamAbbrev}
                    value={player.stats.gameWinningGoals}
                    playerId={player.bio.playerId}
                  />
                ))}
              </div>
            </div>

            {/* Shots */}
            <div className="bento-card">
              <p className="micro-label">Shots</p>
              <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Volume Shooters</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                {skaterLeaders.shots.slice(0, 5).map((player, idx) => (
                  <LeaderRow
                    key={player.bio.playerId}
                    rank={idx + 1}
                    name={player.bio.lastName}
                    team={player.bio.teamAbbrev}
                    value={player.stats.shots}
                    playerId={player.bio.playerId}
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
              <p className="lead-sm">In-depth look at the league&apos;s leading scorers.</p>
            </div>
          </div>

          <div className="bento-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))' }}>
            {skaterLeaders.points.slice(0, 4).map((player, idx) => (
              <PlayerCardView key={player.bio.playerId} player={player} rank={idx + 1} />
            ))}
          </div>
        </section>

        {/* Full Stats Table */}
        <section className="nova-section" style={{ paddingTop: 0 }}>
          <div className="section-head">
            <div>
              <p className="eyebrow">Complete data</p>
              <h2>All Skaters</h2>
              <p className="lead-sm">Full statistical breakdown for every qualified skater.</p>
            </div>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <p className="chip-soft">Minimum 5 games played</p>
          </div>
          <SkaterStatsTable players={allSkaters} maxRows={50} />
        </section>
      </div>
    </div>
  );
}
