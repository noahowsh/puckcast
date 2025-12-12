import { buildTeamSnapshots, computeStandingsPowerScore, getCurrentStandings } from "@/lib/current";
import powerIndexSnapshot from "@/data/powerIndexSnapshot.json";
import { TeamCrest } from "@/components/TeamCrest";
import { PowerBoardClient, type LeaderboardRow } from "@/components/PowerBoardClient";
import { fetchNextGamesMap } from "@/lib/nextGames";

const snapshots = buildTeamSnapshots();
const snapshotMap = new Map(snapshots.map((team) => [team.abbrev, team]));
const standings = getCurrentStandings();
const nameToAbbrev = new Map<string, string>(standings.map((team) => [team.team, team.abbrev]));

// Calculate expected win rates for all teams based on power score
// This provides a meaningful "model strength" metric even when team isn't playing today
const allPowerScores = standings.map(s => computeStandingsPowerScore(s));
const avgPowerScore = allPowerScores.reduce((a, b) => a + b, 0) / allPowerScores.length;
const maxPowerScore = Math.max(...allPowerScores);
const minPowerScore = Math.min(...allPowerScores);

function getExpectedWinRate(powerScore: number): number {
  // Convert power score to expected win rate (0.35 to 0.65 range)
  // Teams at avg power score get ~0.50, best teams ~0.65, worst ~0.35
  const normalized = (powerScore - minPowerScore) / (maxPowerScore - minPowerScore);
  return 0.35 + normalized * 0.30;
}

// Weekly update schedule - only revalidate once per week
export const dynamic = "force-dynamic";
export const revalidate = 604800; // 7 days in seconds

const weekOf = powerIndexSnapshot.weekOf;

const rankedRows: LeaderboardRow[] = standings
  .map((standing) => {
    const snap = snapshotMap.get(standing.abbrev);
    const power = computeStandingsPowerScore(standing);
    const record = `${standing.wins}-${standing.losses}-${standing.ot}`;
    // Use today's game win prob if available, otherwise use expected win rate based on power score
    const overlayAvg = snap?.avgProb || getExpectedWinRate(power);
    return {
      powerRank: 0,
      standingsRank: standing.rank,
      movement: 0,
      team: standing.team,
      abbrev: standing.abbrev,
      record,
      points: standing.points,
      goalDifferential: standing.goalDifferential,
      pointPctg: standing.pointPctg,
      powerScore: power,
      overlay: { avgProb: overlayAvg },
    };
  })
  .sort((a, b) => b.powerScore - a.powerScore)
  .map((row, idx) => ({
    ...row,
    powerRank: idx + 1,
    movement: row.standingsRank - (idx + 1),
  }));

const biggestMover = rankedRows.reduce<LeaderboardRow | null>((best, row) => {
  if (row.movement <= 0) return best;
  if (!best || row.movement > best.movement) return row;
  return best;
}, null);

const biggestSlider = rankedRows.reduce<LeaderboardRow | null>((best, row) => {
  if (row.movement >= 0) return best;
  if (!best || row.movement < best.movement) return row;
  return best;
}, null);

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

type NextGameInfo = { opponent: string; date: string; startTimeEt: string | null };

async function fetchNextGames(abbrevs: string[]): Promise<Record<string, NextGameInfo>> {
  const today = new Date();
  const end = new Date();
  end.setDate(end.getDate() + 14); // two-week lookahead
  const fmt = (d: Date) => d.toISOString().slice(0, 10);
  const url = `https://statsapi.web.nhl.com/api/v1/schedule?startDate=${fmt(today)}&endDate=${fmt(end)}`;

  try {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) {
      console.warn("schedule fetch failed", res.status);
      return {};
    }
    const data = await res.json();
    const map: Record<string, NextGameInfo> = {};

    const resolveAbbrev = (team: any) => {
      const cand = team?.abbreviation || team?.triCode || nameToAbbrev.get(team?.name) || team?.teamName || team?.name;
      return (cand || "").toString().toUpperCase();
    };

    const formatEt = (iso: string) => {
      if (!iso) return null;
      const dt = new Date(iso);
      return new Intl.DateTimeFormat("en-US", {
        timeZone: "America/New_York",
        hour: "numeric",
        minute: "2-digit",
      }).format(dt);
    };

    data?.dates?.forEach((block: any) => {
      const date = block?.date;
      block?.games?.forEach((game: any) => {
        const homeTeam = game?.teams?.home?.team;
        const awayTeam = game?.teams?.away?.team;
        const home = resolveAbbrev(homeTeam);
        const away = resolveAbbrev(awayTeam);
        const startTimeEt = formatEt(game?.gameDate);
        if (home && !map[home]) {
          map[home] = { opponent: away, date, startTimeEt };
        }
        if (away && !map[away]) {
          map[away] = { opponent: home, date, startTimeEt };
        }
      });
    });

    // Keep only requested teams
    const filtered: Record<string, NextGameInfo> = {};
    abbrevs.forEach((abbr) => {
      if (map[abbr]) filtered[abbr] = map[abbr];
    });
    return filtered;
  } catch (e) {
    console.warn("schedule fetch exception", e);
    return {};
  }
}

export default async function LeaderboardsPage() {
  const nextGames = await fetchNextGamesMap(rankedRows.map((r) => r.abbrev), 14);
  const topTeam = rankedRows[0];

  return (
    <div className="min-h-screen">
      <div className="container">
        <section className="nova-hero">
          <div className="nova-hero__grid">
            <div className="nova-hero__text">
              <div className="pill-row">
                <span className="pill">Puckcast Power Index</span>
                <span className="pill">Week of {weekOf}</span>
              </div>
              <h1 className="display-xl">The analytics snapshot of who&apos;s real.</h1>
              <p className="lead">
                Power score blends standings metrics (points, point percentage) with underlying strength (goal differential and model win rate).
                Rankings update every Monday to capture a full week of movement.
              </p>
            </div>

            {/* Visual: Top 3 Podium + Movers */}
            <div className="nova-hero__panel" style={{ padding: '1.25rem' }}>
              {/* Top 3 Teams Podium */}
              <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
                {/* #2 */}
                <div style={{ textAlign: 'center', flex: 1 }}>
                  <TeamCrest abbrev={rankedRows[1]?.abbrev ?? ''} size={48} />
                  <div style={{ marginTop: '0.5rem', padding: '0.75rem 0.5rem', background: 'rgba(192, 192, 192, 0.15)', borderRadius: '0.5rem 0.5rem 0 0', borderTop: '3px solid silver' }}>
                    <p style={{ fontSize: '1.25rem', fontWeight: 800, color: 'silver' }}>2</p>
                  </div>
                </div>
                {/* #1 */}
                <div style={{ textAlign: 'center', flex: 1 }}>
                  <TeamCrest abbrev={rankedRows[0]?.abbrev ?? ''} size={64} />
                  <div style={{ marginTop: '0.5rem', padding: '1rem 0.5rem', background: 'rgba(255, 215, 0, 0.15)', borderRadius: '0.5rem 0.5rem 0 0', borderTop: '3px solid gold' }}>
                    <p style={{ fontSize: '1.5rem', fontWeight: 800, color: 'gold' }}>1</p>
                  </div>
                </div>
                {/* #3 */}
                <div style={{ textAlign: 'center', flex: 1 }}>
                  <TeamCrest abbrev={rankedRows[2]?.abbrev ?? ''} size={48} />
                  <div style={{ marginTop: '0.5rem', padding: '0.5rem', background: 'rgba(205, 127, 50, 0.15)', borderRadius: '0.5rem 0.5rem 0 0', borderTop: '3px solid #cd7f32' }}>
                    <p style={{ fontSize: '1.1rem', fontWeight: 800, color: '#cd7f32' }}>3</p>
                  </div>
                </div>
              </div>

              {/* Movers Section */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                {biggestMover && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem', background: 'rgba(110, 240, 194, 0.1)', borderRadius: '0.5rem', border: '1px solid rgba(110, 240, 194, 0.2)' }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" style={{ color: 'var(--mint)', flexShrink: 0 }}>
                      <path d="M12 19V5M5 12l7-7 7 7" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                    <div>
                      <p style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-tertiary)', fontWeight: 600 }}>Rising</p>
                      <p style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--mint)' }}>{biggestMover.abbrev} +{biggestMover.movement}</p>
                    </div>
                  </div>
                )}
                {biggestSlider && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem', background: 'rgba(255, 148, 168, 0.1)', borderRadius: '0.5rem', border: '1px solid rgba(255, 148, 168, 0.2)' }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" style={{ color: 'var(--rose)', flexShrink: 0 }}>
                      <path d="M12 5v14M5 12l7 7 7-7" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                    <div>
                      <p style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-tertiary)', fontWeight: 600 }}>Falling</p>
                      <p style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--rose)' }}>{biggestSlider.abbrev} {biggestSlider.movement}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        <section className="nova-section">
          <div className="section-head">
            <div>
              <p className="eyebrow">Analytics snapshot</p>
              <h2>Puckcast Power Board</h2>
              <p className="lead-sm">Movement vs. the standings, model win rate overlay, and next opponent.</p>
            </div>
          </div>

          <PowerBoardClient rows={rankedRows} initialNextGames={nextGames} />
        </section>
      </div>
    </div>
  );
}
