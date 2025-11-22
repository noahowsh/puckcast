import Link from "next/link";
import { buildTeamSnapshots, computeStandingsPowerScore, formatPowerScore, getCurrentStandings } from "@/lib/current";
import { TeamLogo } from "@/components/TeamLogo";

const snapshots = buildTeamSnapshots();
const standings = getCurrentStandings();

const combined = standings.map((team) => {
  const snap = snapshots.find((s) => s.abbrev === team.abbrev);
  const avgProb = snap?.avgProb ?? team.pointPctg ?? 0.5;
  const avgEdge = snap?.avgEdge ?? Math.max(Math.min(team.goalDifferential / 200, 0.15), -0.15);
  const powerScore = snap ? formatPowerScore(snap) : computeStandingsPowerScore({ ...team, rank: team.rank });
  return {
    team: team.team,
    abbrev: team.abbrev,
    games: snap?.games ?? team.gamesPlayed ?? 0,
    avgProb,
    avgEdge,
    favoriteRate: snap?.favoriteRate ?? 0.5,
    record: `${team.wins}-${team.losses}-${team.ot}`,
    points: team.points,
    pointPctg: team.pointPctg,
    standingsRank: team.rank,
    nextGame: snap?.nextGame,
    powerScore,
  };
});

const rankedTeams = combined
  .slice()
  .sort((a, b) => b.powerScore - a.powerScore)
  .map((team, idx) => {
    const powerRank = idx + 1;
    const movement = (team.standingsRank ?? powerRank) - powerRank;
    return { ...team, powerRank, movement };
  });

function movementLabel(movement: number) {
  if (movement === 0) return "Even";
  return movement > 0 ? `+${movement}` : `${movement}`;
}

export default function TeamsIndexPage() {
  return (
    <div className="min-h-screen">
      <div className="container">
        <section className="nova-hero nav-offset">
          <div className="nova-hero__text">
            <div className="pill-row">
              <span className="pill">Team Index</span>
              <span className="pill">All 32 teams</span>
            </div>
            <h1 className="display-xl">Find your team.</h1>
            <p className="lead">
              Quick snapshot of every club: power rank, record, and how the model sees them today. Tap into a team page for a deeper view.
            </p>
            <div className="chip-row">
              <span className="chip-soft">Power score from model + standings</span>
              <span className="chip-soft">Updated with live data</span>
            </div>
          </div>
        </section>

        <section className="nova-section">
          <div className="power-list">
            {rankedTeams.map((team) => (
              <Link key={team.abbrev} href={`/teams/${team.abbrev.toLowerCase()}`} className="power-list-item">
                <div className="power-list-item__row">
                  <div className="power-list-item__meta">
                    <span className="power-rank">#{team.powerRank}</span>
                    <span className="power-name">{team.team}</span>
                    <TeamLogo teamAbbrev={team.abbrev} size="xs" />
                  </div>
                  <span
                    className={`movement movement--pillless ${
                      team.movement > 0 ? "movement--positive" : team.movement < 0 ? "movement--negative" : "movement--neutral"
                    }`}
                  >
                    {movementLabel(team.movement)}
                  </span>
                </div>
                <div className="power-list-item__sub">
                  <span className="chip-soft chip-soft--mini">{team.record ?? "Record N/A"}</span>
                  <span className="chip-soft chip-soft--mini">Power {team.powerScore}</span>
                  <span className="chip-soft chip-soft--mini">Model win {(team.avgProb * 100).toFixed(1)}%</span>
                </div>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
