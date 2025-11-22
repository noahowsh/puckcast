import { buildTeamSnapshots, computeStandingsPowerScore, getCurrentStandings, type TeamSnapshot } from "@/lib/current";
import { teamBorderColor, teamGradient } from "@/lib/teamColors";

const snapshots = buildTeamSnapshots();
const snapshotMap = new Map(snapshots.map((team) => [team.abbrev, team]));
const standings = getCurrentStandings();

type LeaderboardRow = {
  powerRank: number;
  standingsRank: number;
  movement: number;
  team: string;
  abbrev: string;
  record: string;
  points: number;
  goalDifferential: number;
  pointPctg: number;
  powerScore: number;
  nextGame?: TeamSnapshot["nextGame"];
  overlay?: TeamSnapshot;
};

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
      nextGame: snap?.nextGame,
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

function Crest({ label }: { label: string }) {
  return (
    <span
      className="crest"
      style={{
        background: teamGradient(label),
        borderColor: teamBorderColor(label),
      }}
    >
      {label}
    </span>
  );
}

export default function LeaderboardsPage() {
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

          <div className="power-board">
            <div className="power-board__head">
              <span>#</span>
              <span>Team</span>
              <span>Movement</span>
              <span>Record</span>
              <span>Point %</span>
              <span>Goal Diff</span>
              <span>Model Win%</span>
              <span>Next</span>
            </div>
            {rankedRows.map((row) => (
              <PowerRow key={row.abbrev} row={row} />
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

function PowerRow({ row }: { row: LeaderboardRow }) {
  const movementDisplay = row.movement === 0 ? "Even" : row.movement > 0 ? `+${row.movement}` : row.movement;
  const movementTone = row.movement > 0 ? "movement--positive" : row.movement < 0 ? "movement--negative" : "movement--neutral";

  return (
    <div className="power-board__row">
      <div className="rank-chip">#{row.powerRank}</div>
      <div className="power-team">
        <Crest label={row.abbrev} />
        <div>
          <p className="power-name">{row.team}</p>
          <p className="micro-label">Standings #{row.standingsRank}</p>
        </div>
      </div>
      <span className={`movement movement--pillless ${movementTone}`}>{movementDisplay}</span>
      <span className="power-data">{row.record}</span>
      <span className="power-data">{pct(row.pointPctg)}</span>
      <span className={`power-data ${row.goalDifferential >= 0 ? "text-up" : "text-down"}`}>
        {row.goalDifferential >= 0 ? "+" : ""}
        {row.goalDifferential}
      </span>
      <span className="power-data">{row.overlay ? pct(row.overlay.avgProb) : "-"}</span>
      <span className="power-data">{row.nextGame ? `${row.nextGame.opponent} (${row.nextGame.date})` : "TBD"}</span>
    </div>
  );
}
