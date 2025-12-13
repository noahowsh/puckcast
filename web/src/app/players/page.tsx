import Link from "next/link";
import { SkaterStatsTable, GoalieStatsTable, LeaderRow } from "@/components/PlayerStatsTable";
import { fetchSkaterLeaders, fetchGoalieLeaders, fetchEnrichedSkaterStats, fetchGoalieStats } from "@/lib/playerHub";

export const revalidate = 3600; // Revalidate every hour

export default async function PlayersPage() {
  const [skaterLeaders, goalieLeaders, allSkaters, allGoalies] = await Promise.all([
    fetchSkaterLeaders(),
    fetchGoalieLeaders(),
    fetchEnrichedSkaterStats(5),
    fetchGoalieStats(3),
  ]);

  const updatedAt = new Date().toLocaleString("en-US", { timeZone: "America/New_York", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });

  // Calculate some summary stats for the hero panel
  const totalSkaters = allSkaters.length;
  const totalGoalies = allGoalies.length;
  const topScorer = skaterLeaders.points[0];
  const topGoalie = goalieLeaders.savePct[0];

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
              <h1 className="display-xl">Player intelligence, distilled.</h1>
              <p className="lead">
                Live statistical leaders across the NHL. Track scoring races, goaltending dominance, and category leaders
                updated hourly from official league data.
              </p>
              <div className="cta-row">
                <Link href="/skaters" className="cta cta-ghost">
                  Skater Deep Dive →
                </Link>
                <Link href="/goalies" className="cta cta-ghost">
                  Goalie Deep Dive →
                </Link>
              </div>
            </div>

            {/* Hero Panel - Top Performers */}
            <div className="nova-hero__panel" style={{ padding: '1.25rem' }}>
              <p style={{ fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-tertiary)', marginBottom: '0.75rem' }}>
                Season Leaders
              </p>

              {topScorer && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem', background: 'rgba(126, 227, 255, 0.08)', borderRadius: '0.75rem', border: '1px solid rgba(126, 227, 255, 0.2)', marginBottom: '0.5rem' }}>
                  <div style={{ width: '2.5rem', height: '2.5rem', borderRadius: '50%', background: 'linear-gradient(135deg, rgba(126, 227, 255, 0.2), rgba(110, 240, 194, 0.2))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '0.9rem', color: 'var(--aqua)' }}>
                    1
                  </div>
                  <div style={{ flex: 1 }}>
                    <p style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-tertiary)', fontWeight: 600, marginBottom: '0.1rem' }}>Points Leader</p>
                    <p style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>{topScorer.bio.fullName}</p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <p style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--aqua)' }}>{topScorer.stats.points}</p>
                    <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>PTS</p>
                  </div>
                </div>
              )}

              {topGoalie && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem', background: 'rgba(110, 240, 194, 0.08)', borderRadius: '0.75rem', border: '1px solid rgba(110, 240, 194, 0.2)' }}>
                  <div style={{ width: '2.5rem', height: '2.5rem', borderRadius: '50%', background: 'linear-gradient(135deg, rgba(110, 240, 194, 0.2), rgba(126, 227, 255, 0.2))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '0.9rem', color: 'var(--mint)' }}>
                    1
                  </div>
                  <div style={{ flex: 1 }}>
                    <p style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-tertiary)', fontWeight: 600, marginBottom: '0.1rem' }}>Save % Leader</p>
                    <p style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>{topGoalie.bio.fullName}</p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <p style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--mint)' }}>.{Math.round(topGoalie.stats.savePct * 1000)}</p>
                    <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>SV%</p>
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
                  <p style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>{totalGoalies}</p>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Goalies tracked</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Scoring Leaders Section */}
        <section className="nova-section">
          <div className="section-head">
            <div>
              <p className="eyebrow">The scoring race</p>
              <h2>Scoring Leaders</h2>
              <p className="lead-sm">Top 10 in points, goals, and assists across the league.</p>
            </div>
          </div>

          {skaterLeaders.points.length === 0 ? (
            <div className="empty-tile">
              <p>Skater statistics are being loaded. Please refresh the page.</p>
            </div>
          ) : (
            <div className="bento-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))' }}>
              {/* Points Leaders */}
              <div className="bento-card">
                <p className="micro-label">Points</p>
                <h3 style={{ marginBottom: '0.75rem' }}>Total Scoring</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  {skaterLeaders.points.slice(0, 10).map((player, idx) => (
                    <LeaderRow
                      key={player.bio.playerId}
                      rank={idx + 1}
                      name={player.bio.fullName}
                      fullName={player.bio.fullName}
                      team={player.bio.teamAbbrev}
                      value={player.stats.points}
                      playerId={player.bio.playerId}
                      headshot={player.bio.headshot}
                    />
                  ))}
                </div>
              </div>

              {/* Goals Leaders */}
              <div className="bento-card">
                <p className="micro-label">Goals</p>
                <h3 style={{ marginBottom: '0.75rem' }}>Lamp Lighters</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  {skaterLeaders.goals.slice(0, 10).map((player, idx) => (
                    <LeaderRow
                      key={player.bio.playerId}
                      rank={idx + 1}
                      name={player.bio.fullName}
                      fullName={player.bio.fullName}
                      team={player.bio.teamAbbrev}
                      value={player.stats.goals}
                      playerId={player.bio.playerId}
                      headshot={player.bio.headshot}
                    />
                  ))}
                </div>
              </div>

              {/* Assists Leaders */}
              <div className="bento-card">
                <p className="micro-label">Assists</p>
                <h3 style={{ marginBottom: '0.75rem' }}>Playmakers</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  {skaterLeaders.assists.slice(0, 10).map((player, idx) => (
                    <LeaderRow
                      key={player.bio.playerId}
                      rank={idx + 1}
                      name={player.bio.fullName}
                      fullName={player.bio.fullName}
                      team={player.bio.teamAbbrev}
                      value={player.stats.assists}
                      playerId={player.bio.playerId}
                      headshot={player.bio.headshot}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}
        </section>

        {/* Category Leaders Section */}
        <section className="nova-section" style={{ paddingTop: 0 }}>
          <div className="section-head">
            <div>
              <p className="eyebrow">Specialty stats</p>
              <h2>Category Leaders</h2>
              <p className="lead-sm">Power play production, plus/minus, clutch goals, and shot volume.</p>
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
                    fullName={player.bio.fullName}
                    team={player.bio.teamAbbrev}
                    value={player.stats.powerPlayGoals}
                    playerId={player.bio.playerId}
                      headshot={player.bio.headshot}
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
                    fullName={player.bio.fullName}
                    team={player.bio.teamAbbrev}
                    value={`+${player.stats.plusMinus}`}
                    playerId={player.bio.playerId}
                      headshot={player.bio.headshot}
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
                    fullName={player.bio.fullName}
                    team={player.bio.teamAbbrev}
                    value={player.stats.gameWinningGoals}
                    playerId={player.bio.playerId}
                      headshot={player.bio.headshot}
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
                    fullName={player.bio.fullName}
                    team={player.bio.teamAbbrev}
                    value={player.stats.shots}
                    playerId={player.bio.playerId}
                      headshot={player.bio.headshot}
                  />
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Goalie Leaders Section */}
        <section className="nova-section" style={{ paddingTop: 0 }}>
          <div className="section-head">
            <div>
              <p className="eyebrow">Between the pipes</p>
              <h2>Goaltending Leaders</h2>
              <p className="lead-sm">Wins, save percentage, goals against average, and shutouts.</p>
            </div>
            <Link href="/goalies" className="cta cta-ghost">
              Full Goalie Analysis →
            </Link>
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
                    fullName={goalie.bio.fullName}
                    team={goalie.bio.teamAbbrev}
                    value={goalie.stats.wins}
                    playerId={goalie.bio.playerId}
                    headshot={goalie.bio.headshot}
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
                    fullName={goalie.bio.fullName}
                    team={goalie.bio.teamAbbrev}
                    value={`.${Math.round(goalie.stats.savePct * 1000)}`}
                    playerId={goalie.bio.playerId}
                    headshot={goalie.bio.headshot}
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
                    fullName={goalie.bio.fullName}
                    team={goalie.bio.teamAbbrev}
                    value={goalie.stats.goalsAgainstAverage.toFixed(2)}
                    playerId={goalie.bio.playerId}
                    headshot={goalie.bio.headshot}
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
                    fullName={goalie.bio.fullName}
                    team={goalie.bio.teamAbbrev}
                    value={goalie.stats.shutouts}
                    playerId={goalie.bio.playerId}
                    headshot={goalie.bio.headshot}
                    isGoalie
                  />
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Full Stats Tables Section */}
        <section className="nova-section" style={{ paddingTop: 0 }}>
          <div className="section-head">
            <div>
              <p className="eyebrow">Complete data</p>
              <h2>Full Statistical Tables</h2>
              <p className="lead-sm">Sortable tables for top skaters and goalies this season.</p>
            </div>
          </div>

          {/* Skaters Table */}
          <div style={{ marginBottom: '2.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Top Skaters</h3>
                <p className="chip-soft" style={{ marginTop: '0.25rem' }}>Top 25 by points • Min 5 GP</p>
              </div>
              <Link href="/skaters" className="cta cta-ghost" style={{ fontSize: '0.875rem' }}>
                View All Skaters →
              </Link>
            </div>
            <SkaterStatsTable players={allSkaters} maxRows={25} />
          </div>

          {/* Goalies Table */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Top Goalies</h3>
                <p className="chip-soft" style={{ marginTop: '0.25rem' }}>Top 15 by wins • Min 3 GP</p>
              </div>
              <Link href="/goalies" className="cta cta-ghost" style={{ fontSize: '0.875rem' }}>
                View All Goalies →
              </Link>
            </div>
            <GoalieStatsTable goalies={allGoalies} maxRows={15} />
          </div>
        </section>
      </div>
    </div>
  );
}
