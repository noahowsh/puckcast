import { notFound } from "next/navigation";
import { buildTeamSnapshots, computeStandingsPowerScore, formatPowerScore, getCurrentStandings } from "@/lib/current";
import { TeamLogo } from "@/components/TeamLogo";

const snapshots = buildTeamSnapshots();
const snapshotMap = new Map(
  snapshots.map((team, idx) => [team.abbrev.toLowerCase(), { ...team, powerRank: idx + 1, powerScore: formatPowerScore(team) }]),
);
const standings = getCurrentStandings();
const standingsMap = new Map(standings.map((t) => [t.abbrev.toLowerCase(), { ...t, record: `${t.wins}-${t.losses}-${t.ot}` }]));

function movementLabel(movement: number) {
  if (movement === 0) return "Even";
  return movement > 0 ? `+${movement}` : `${movement}`;
}

function buildStrengths(team: (typeof snapshots)[number]) {
  const strengths: string[] = [];
  if (team.avgProb > 0.55) strengths.push("Consistent favorite in the model");
  if ((team.avgEdge ?? 0) > 0.12) strengths.push("High average edge vs market baselines");
  if ((team.favoriteRate ?? 0) > 0.6) strengths.push("Wins model coin flips often");
  if (strengths.length === 0) strengths.push("Steady but not dominant in recent projections");
  return strengths;
}

function buildWeaknesses(team: (typeof snapshots)[number]) {
  const weaknesses: string[] = [];
  if (team.avgProb < 0.5) weaknesses.push("Model sees below-average win probability");
  if ((team.avgEdge ?? 0) < 0.08) weaknesses.push("Edges are tight; little margin for error");
  if ((team.favoriteRate ?? 0) < 0.4) weaknesses.push("Rarely a strong favorite in the model");
  if (weaknesses.length === 0) weaknesses.push("Edges can compress against top opponents");
  return weaknesses;
}

export default function TeamPage({ params }: { params: { abbrev: string } }) {
  const key = params.abbrev?.toLowerCase?.();
  if (!key) return notFound();
  const fallbackStandings = standingsMap.get(key);
  const snapshot =
    snapshotMap.get(key) ||
    (fallbackStandings && {
      team: fallbackStandings.team,
      abbrev: fallbackStandings.abbrev,
      games: fallbackStandings.gamesPlayed,
      avgProb: 0.5,
      avgEdge: 0,
      favoriteRate: 0.5,
      record: fallbackStandings.record,
      points: fallbackStandings.points,
      pointPctg: fallbackStandings.pointPctg,
      standingsRank: fallbackStandings.rank,
      powerRank: fallbackStandings.rank,
      powerScore: computeStandingsPowerScore(fallbackStandings),
    });
  if (!snapshot) return notFound();

  const standingsInfo = standingsMap.get(key);
  const powerScore = snapshot.powerScore ?? formatPowerScore(snapshot as any);
  const movement = standingsInfo?.rank ? standingsInfo.rank - snapshot.powerRank : 0;
  const strengths = buildStrengths(snapshot);
  const weaknesses = buildWeaknesses(snapshot);

  return (
    <div className="min-h-screen">
      <div className="container">
        <section className="nova-hero nav-offset">
          <div className="nova-hero__grid nova-hero__grid--balanced">
            <div className="nova-hero__text">
              <div className="pill-row">
                <span className="pill">Team profile</span>
                <span className="pill">{snapshot.team}</span>
              </div>
              <h1 className="display-xl">
                #{snapshot.powerRank} · {snapshot.team}
              </h1>
              <p className="lead">
                Model view of the {snapshot.team}: power index, edges, upcoming opponent, and how the model stacks them versus the standings.
              </p>
              <div className="stat-grid">
                <div className="stat-tile">
                  <p className="stat-tile__label">Power score</p>
                  <p className="stat-tile__value">{powerScore}</p>
                  <p className="stat-tile__detail">#{snapshot.powerRank} in the model</p>
                </div>
                <div className="stat-tile">
                  <p className="stat-tile__label">Record</p>
                  <p className="stat-tile__value">{standingsInfo?.record ?? "N/A"}</p>
                  <p className="stat-tile__detail">Points {standingsInfo?.points ?? "N/A"}</p>
                </div>
                <div className="stat-tile">
                  <p className="stat-tile__label">Model win %</p>
                  <p className="stat-tile__value">{(snapshot.avgProb * 100).toFixed(1)}%</p>
                  <p className="stat-tile__detail">Avg edge {(snapshot.avgEdge * 100).toFixed(1)} pts</p>
                </div>
                <div className="stat-tile">
                  <p className="stat-tile__label">Movement</p>
                  <p className="stat-tile__value">{movementLabel(movement)}</p>
                  <p className="stat-tile__detail">vs standings #{standingsInfo?.rank ?? "N/A"}</p>
                </div>
              </div>
            </div>

            <div className="nova-hero__panel">
              <div className="flex items-center gap-3 mb-4">
                <TeamLogo teamAbbrev={snapshot.abbrev} size="sm" />
                <div>
                  <p className="text-lg font-semibold text-white">{snapshot.team}</p>
                  <p className="text-sm text-white/60">Power score {powerScore}</p>
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="card-flat">
                  <p className="stat-label">Strengths</p>
                  <ul className="space-y-2 text-sm text-white/80">
                    {strengths.map((item) => (
                      <li key={item}>• {item}</li>
                    ))}
                  </ul>
                </div>
                <div className="card-flat">
                  <p className="stat-label">Weaknesses</p>
                  <ul className="space-y-2 text-sm text-white/80">
                    {weaknesses.map((item) => (
                      <li key={item}>• {item}</li>
                    ))}
                  </ul>
                </div>
              </div>
              <div className="mt-4 rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <p className="stat-label mb-1">Upcoming opponent</p>
                <p className="text-sm text-white/80">
                  {snapshot.nextGame ? `${snapshot.nextGame.opponent} on ${snapshot.nextGame.date}` : "TBD"}
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="nova-section">
          <div className="card">
            <h2 className="text-xl font-bold text-white mb-3">How the model sees this team</h2>
            <p className="text-white/75 leading-relaxed">
              {snapshot.team} rate as #{snapshot.powerRank} in the Puckcast power index. The model blends win probability, edge, and standings context
              to size up each matchup. Edges tighten against elite opponents and expand versus teams the model flags as overrated.
            </p>
          </div>
        </section>

        <section className="nova-section">
          <div className="card">
            <h3 className="text-lg font-bold text-white mb-2">Recent prediction performance</h3>
            <p className="text-white/70 text-sm">Last 10-game form tracking is coming soon.</p>
          </div>
        </section>

        <section className="nova-section">
          <div className="card">
            <h3 className="text-lg font-bold text-white mb-2">Trend line</h3>
            <p className="text-white/70 text-sm">Power index trend (last 10 games) coming soon once history is wired in.</p>
          </div>
        </section>
      </div>
    </div>
  );
}
