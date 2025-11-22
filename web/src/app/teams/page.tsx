import Link from "next/link";
import { buildTeamSnapshots, computeStandingsPowerScore, formatPowerScore, getCurrentStandings } from "@/lib/current";
import { TeamLogo } from "@/components/TeamLogo";

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
              Browse all 32 NHL teams alphabetically. Tap any team to view detailed stats, upcoming games, and goalie performance.
            </p>
            <div className="chip-row">
              <span className="chip-soft">Alphabetically sorted</span>
              <span className="chip-soft">Updated with live data</span>
            </div>
          </div>
        </section>

        <section className="nova-section">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {allTeams.map((team) => (
              <Link key={team.abbrev} href={`/teams/${team.abbrev.toLowerCase()}`} className="card group">
                <div className="flex items-center gap-4">
                  <TeamLogo teamAbbrev={team.abbrev} size="md" />
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-bold text-white truncate group-hover:text-cyan-400 transition-colors">
                      {team.team}
                    </h3>
                    <p className="text-sm text-white/60">{team.record}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 mt-3">
                  <span className="chip-soft chip-soft--mini">{team.points} pts</span>
                  <span className="chip-soft chip-soft--mini">{(team.avgProb * 100).toFixed(1)}% win</span>
                </div>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
