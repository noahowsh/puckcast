import { notFound } from "next/navigation";
import { buildTeamSnapshots, computeStandingsPowerScore, formatPowerScore, getCurrentStandings, getCurrentPredictions } from "@/lib/current";
import { TeamLogo } from "@/components/TeamLogo";
import goaliePulseRaw from "@/data/goaliePulse.json";
import type { GoaliePulse } from "@/types/goalie";

const goaliePulse = goaliePulseRaw as GoaliePulse;
const snapshots = buildTeamSnapshots();
const snapshotMap = new Map(
  snapshots.map((team, idx) => [team.abbrev.toLowerCase(), { ...team, powerRank: idx + 1, powerScore: formatPowerScore(team) }]),
);
const standings = getCurrentStandings();
const standingsMap = new Map(standings.map((t) => [t.abbrev.toLowerCase(), { ...t, record: `${t.wins}-${t.losses}-${t.ot}` }]));
const predictions = getCurrentPredictions();

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

export function generateStaticParams() {
  return standings.map((team) => ({
    abbrev: team.abbrev.toLowerCase(),
  }));
}

export default async function TeamPage({ params }: { params: Promise<{ abbrev: string }> }) {
  const { abbrev } = await params;
  const key = abbrev?.toLowerCase?.();
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

  // Get upcoming games for this team
  const upcomingGames = predictions.games.filter(
    (game) => game.homeTeam.abbrev === snapshot.abbrev || game.awayTeam.abbrev === snapshot.abbrev
  );

  // Get team goalies
  const teamGoalies = goaliePulse.goalies.filter((g) => g.team === snapshot.abbrev);

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
                Model view of the {snapshot.team}: power index, edges, upcoming games, and how the model stacks them versus the standings.
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
                    {strengths.map((item, idx) => (
                      <li key={idx}>• {item}</li>
                    ))}
                  </ul>
                </div>
                <div className="card-flat">
                  <p className="stat-label">Weaknesses</p>
                  <ul className="space-y-2 text-sm text-white/80">
                    {weaknesses.map((item, idx) => (
                      <li key={idx}>• {item}</li>
                    ))}
                  </ul>
                </div>
              </div>
              <div className="mt-4 rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <p className="stat-label mb-1">Next game</p>
                <p className="text-sm text-white/80">
                  {snapshot.nextGame ? `vs ${snapshot.nextGame.opponent} on ${snapshot.nextGame.date}` : "TBD"}
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

        {/* Upcoming Games Section */}
        <section className="nova-section">
          <h2 className="text-2xl font-bold text-white mb-4">Upcoming games</h2>
          {upcomingGames.length > 0 ? (
            <div className="space-y-3">
              {upcomingGames.map((game) => {
                const isHome = game.homeTeam.abbrev === snapshot.abbrev;
                const opponent = isHome ? game.awayTeam : game.homeTeam;
                const winProb = isHome ? game.homeWinProb : game.awayWinProb;
                const teamEdge = isHome ? game.edge : -game.edge;

                return (
                  <div key={game.id} className="card">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                      <div className="flex items-center gap-4">
                        <TeamLogo teamAbbrev={opponent.abbrev} size="xs" />
                        <div>
                          <p className="text-white font-semibold">
                            {isHome ? "vs" : "@"} {opponent.name}
                          </p>
                          <p className="text-sm text-white/60">
                            {game.gameDate} • {game.startTimeEt ?? "TBD"}
                          </p>
                          {game.venue && <p className="text-xs text-white/50">{game.venue}</p>}
                        </div>
                      </div>
                      <div className="flex flex-col sm:items-end gap-1">
                        <div className="flex items-center gap-2">
                          <span className="chip-soft chip-soft--mini">{(winProb * 100).toFixed(1)}% win prob</span>
                          <span className={`chip-soft chip-soft--mini ${teamEdge >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {teamEdge >= 0 ? '+' : ''}{(teamEdge * 100).toFixed(1)} edge
                          </span>
                        </div>
                        <span className="text-xs text-white/60 text-right sm:text-left">{game.confidenceGrade} confidence</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="card">
              <p className="text-white/70">No upcoming games scheduled</p>
            </div>
          )}
        </section>

        {/* Team Statistics Section */}
        <section className="nova-section">
          <h2 className="text-2xl font-bold text-white mb-4">Team statistics</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="card">
              <p className="stat-label">Goals per game</p>
              <p className="stat-tile__value text-2xl">{standingsInfo?.goalsForPerGame?.toFixed(2) ?? "N/A"}</p>
              <p className="text-xs text-white/50 mt-1">Offense</p>
            </div>
            <div className="card">
              <p className="stat-label">Goals against per game</p>
              <p className="stat-tile__value text-2xl">{standingsInfo?.goalsAgainstPerGame?.toFixed(2) ?? "N/A"}</p>
              <p className="text-xs text-white/50 mt-1">Defense</p>
            </div>
            <div className="card">
              <p className="stat-label">Goal differential</p>
              <p className={`stat-tile__value text-2xl ${(standingsInfo?.goalDifferential ?? 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {standingsInfo?.goalDifferential ?? "N/A"}
              </p>
              <p className="text-xs text-white/50 mt-1">Season total</p>
            </div>
            <div className="card">
              <p className="stat-label">Point percentage</p>
              <p className="stat-tile__value text-2xl">{standingsInfo?.pointPctg ? (standingsInfo.pointPctg * 100).toFixed(1) + '%' : "N/A"}</p>
              <p className="text-xs text-white/50 mt-1">Win rate</p>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 mt-4">
            <div className="card">
              <p className="stat-label mb-3">Shooting</p>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-white/70">Shots for per game</span>
                  <span className="text-white font-semibold">{standingsInfo?.shotsForPerGame?.toFixed(1) ?? "N/A"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-white/70">Shots against per game</span>
                  <span className="text-white font-semibold">{standingsInfo?.shotsAgainstPerGame?.toFixed(1) ?? "N/A"}</span>
                </div>
                {standingsInfo?.shotsForPerGame && standingsInfo?.shotsAgainstPerGame && (
                  <div className="flex justify-between pt-2 border-t border-white/10">
                    <span className="text-sm text-white/70">Shot differential</span>
                    <span className={`font-semibold ${(standingsInfo.shotsForPerGame - standingsInfo.shotsAgainstPerGame) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {(standingsInfo.shotsForPerGame - standingsInfo.shotsAgainstPerGame) >= 0 ? '+' : ''}
                      {(standingsInfo.shotsForPerGame - standingsInfo.shotsAgainstPerGame).toFixed(1)}
                    </span>
                  </div>
                )}
              </div>
            </div>
            <div className="card">
              <p className="stat-label mb-3">Record breakdown</p>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-white/70">Wins</span>
                  <span className="text-emerald-400 font-semibold">{standingsInfo?.wins ?? "N/A"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-white/70">Losses</span>
                  <span className="text-rose-400 font-semibold">{standingsInfo?.losses ?? "N/A"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-white/70">Overtime/Shootout</span>
                  <span className="text-amber-400 font-semibold">{standingsInfo?.ot ?? "N/A"}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Goalies Section */}
        {teamGoalies.length > 0 && (
          <section className="nova-section">
            <h2 className="text-2xl font-bold text-white mb-4">Team goalies</h2>
            <div className="space-y-3">
              {teamGoalies.map((goalie) => (
                <div key={goalie.name} className="card">
                  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-bold text-white">{goalie.name}</h3>
                        <span className={`chip-soft chip-soft--mini ${
                          goalie.trend === 'surging' ? 'text-emerald-400' :
                          goalie.trend === 'steady' ? 'text-blue-400' :
                          'text-white/70'
                        }`}>
                          {goalie.trend}
                        </span>
                      </div>
                      <p className="text-sm text-white/70 mb-3">{goalie.note}</p>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        <div>
                          <p className="text-xs text-white/50 mb-1">Season GSAx</p>
                          <p className="text-white font-semibold">{goalie.seasonGsa.toFixed(1)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-white/50 mb-1">Rolling GSAx</p>
                          <p className="text-white font-semibold">{goalie.rollingGsa.toFixed(1)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-white/50 mb-1">Rest days</p>
                          <p className="text-white font-semibold">{goalie.restDays}</p>
                        </div>
                        <div>
                          <p className="text-xs text-white/50 mb-1">Start likelihood</p>
                          <p className="text-white font-semibold">{(goalie.startLikelihood * 100).toFixed(0)}%</p>
                        </div>
                      </div>
                    </div>
                    <div className="flex sm:flex-col gap-2">
                      {goalie.strengths.length > 0 && (
                        <div className="flex-1">
                          <p className="text-xs text-emerald-400 mb-1">Strengths</p>
                          {goalie.strengths.map((s, idx) => (
                            <p key={idx} className="text-xs text-white/70">• {s}</p>
                          ))}
                        </div>
                      )}
                      {goalie.watchouts.length > 0 && (
                        <div className="flex-1">
                          <p className="text-xs text-amber-400 mb-1">Watch</p>
                          {goalie.watchouts.map((w, idx) => (
                            <p key={idx} className="text-xs text-white/70">• {w}</p>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
