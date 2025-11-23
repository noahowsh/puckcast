import { buildTeamSnapshots, computeStandingsPowerScore, getCurrentStandings, type TeamSnapshot } from "@/lib/current";
import { TeamCrest } from "@/components/TeamCrest";
import { PowerBoardClient, type LeaderboardRow } from "@/components/PowerBoardClient";

const snapshots = buildTeamSnapshots();
const snapshotMap = new Map(snapshots.map((team) => [team.abbrev, team]));
const standings = getCurrentStandings();
const nameToAbbrev = new Map<string, string>(standings.map((team) => [team.team, team.abbrev]));

export const dynamic = "force-dynamic";
export const revalidate = 0;

const rankedRows: LeaderboardRow[] = standings
  .map((standing) => {
    const snap = snapshotMap.get(standing.abbrev);
    const power = computeStandingsPowerScore(standing);
    const record = `${standing.wins}-${standing.losses}-${standing.ot}`;
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
      overlay: snap,
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
  const nextGames = await fetchNextGames(rankedRows.map((r) => r.abbrev));
  const topTeam = rankedRows[0];
  const updatedDisplay = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "numeric",
  }).format(new Date());

  return (
    <div className="min-h-screen">
      <div className="container">
        <section className="nova-hero">
          <div className="nova-hero__grid">
            <div className="nova-hero__text">
              <div className="pill-row">
                <span className="pill">Puckcast Power Index</span>
                <span className="pill">Updated {updatedDisplay} ET</span>
              </div>
              <h1 className="display-xl">The analytics snapshot of who&apos;s real.</h1>
              <p className="lead">
                Power score blends standings metrics (points, point percentage) with underlying strength (goal differential and model win rate).
                These rankings refresh weekly so you always know who is outrunning or lagging behind their record.
              </p>
            </div>

            <div className="nova-hero__panel">
              <div className="stat-grid stat-grid-compact">
                {topTeam && (
                  <div className="stat-tile">
                    <p className="stat-tile__label">Current #1</p>
                    <p className="stat-tile__value">{topTeam.team}</p>
                    <p className="stat-tile__detail">#{topTeam.powerRank} · {topTeam.record}</p>
                  </div>
                )}
                {biggestMover && (
                  <div className="stat-tile">
                    <p className="stat-tile__label">Biggest riser</p>
                    <p className="stat-tile__value">{biggestMover.team}</p>
                    <p className="stat-tile__detail">+{biggestMover.movement} spots</p>
                  </div>
                )}
                {biggestSlider && (
                  <div className="stat-tile">
                    <p className="stat-tile__label">Biggest slider</p>
                    <p className="stat-tile__value">{biggestSlider.team}</p>
                    <p className="stat-tile__detail">{biggestSlider.movement} spots</p>
                  </div>
                )}
                <div className="stat-tile">
                  <p className="stat-tile__label">Refresh cadence</p>
                  <p className="stat-tile__value">Weekly</p>
                  <p className="stat-tile__detail">Last updated {updatedDisplay} ET</p>
                </div>
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
