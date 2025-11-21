import { buildTeamSnapshots, computeStandingsPowerScore, getCurrentStandings, type TeamSnapshot } from "@/lib/current";
import { PageHeader } from "@/components/PageHeader";
import { TeamLogo } from "@/components/TeamLogo";

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

export default function LeaderboardsPage() {
  return (
    <div className="min-h-screen">
      <div className="container" style={{ paddingTop: '8rem' }}>
        <PageHeader
          title="Power Rankings"
          description="Our model's team strength rankings vs. traditional standings. Based on goal differential, point percentage, and predictive win rates."
          icon={
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          }
        />

        {/* Biggest Movers */}
        {(biggestMover || biggestSlider) && (
          <section className="mb-16">
            <h2 className="text-2xl font-bold text-white mb-8">Biggest Movers</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {biggestMover && (
                <div className="card bg-green-500/5 border-green-500/30">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-green-500/20 border border-green-500/30">
                      <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                      </svg>
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-green-400 uppercase">Biggest Riser</div>
                      <div className="text-xs text-slate-400">Model vs standings</div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <TeamLogo teamAbbrev={biggestMover.abbrev} size="lg" />
                      <div>
                        <div className="text-xl font-bold text-white">{biggestMover.team}</div>
                        <div className="text-sm text-slate-400">{biggestMover.record}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-3xl font-bold text-green-400">+{biggestMover.movement}</div>
                      <div className="text-xs text-slate-400">spots</div>
                    </div>
                  </div>
                </div>
              )}

              {biggestSlider && (
                <div className="card bg-red-500/5 border-red-500/30">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-red-500/20 border border-red-500/30">
                      <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                      </svg>
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-red-400 uppercase">Biggest Faller</div>
                      <div className="text-xs text-slate-400">Model vs standings</div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <TeamLogo teamAbbrev={biggestSlider.abbrev} size="lg" />
                      <div>
                        <div className="text-xl font-bold text-white">{biggestSlider.team}</div>
                        <div className="text-sm text-slate-400">{biggestSlider.record}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-3xl font-bold text-red-400">{biggestSlider.movement}</div>
                      <div className="text-xs text-slate-400">spots</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </section>
        )}

        {/* Full Rankings Table */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold text-white mb-8">All 32 Teams</h2>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Power Rank</th>
                  <th>Team</th>
                  <th>Movement</th>
                  <th>Record</th>
                  <th>Points</th>
                  <th>Point %</th>
                  <th>Goal Diff</th>
                  {snapshots.length > 0 && <th>Model Win %</th>}
                </tr>
              </thead>
              <tbody>
                {rankedRows.map((row) => {
                  const movementDisplay = row.movement === 0 ? "—" : row.movement > 0 ? `+${row.movement}` : row.movement;
                  const movementColor =
                    row.movement > 0
                      ? "text-green-400"
                      : row.movement < 0
                      ? "text-red-400"
                      : "text-slate-500";

                  return (
                    <tr key={row.abbrev}>
                      <td>
                        <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-sky-500/20 to-cyan-500/20 border border-sky-500/30">
                          <span className="text-lg font-bold text-sky-400">{row.powerRank}</span>
                        </div>
                      </td>
                      <td>
                        <div className="flex items-center gap-3">
                          <TeamLogo teamAbbrev={row.abbrev} size="sm" />
                          <div>
                            <div className="font-semibold text-white">{row.team}</div>
                            <div className="text-xs text-slate-500">Standings: #{row.standingsRank}</div>
                          </div>
                        </div>
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          {row.movement > 0 && (
                            <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                          {row.movement < 0 && (
                            <svg className="w-4 h-4 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                          <span className={`font-semibold ${movementColor}`}>{movementDisplay}</span>
                        </div>
                      </td>
                      <td className="font-semibold">{row.record}</td>
                      <td>{row.points}</td>
                      <td>{pct(row.pointPctg)}</td>
                      <td>
                        <span className={row.goalDifferential >= 0 ? "text-green-400" : "text-red-400"}>
                          {row.goalDifferential >= 0 ? "+" : ""}
                          {row.goalDifferential}
                        </span>
                      </td>
                      {row.overlay && (
                        <td className="font-semibold text-sky-400">{pct(row.overlay.avgProb)}</td>
                      )}
                      {!row.overlay && snapshots.length > 0 && <td className="text-slate-500">—</td>}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>

        {/* Methodology Note */}
        <section className="mb-16">
          <div className="card bg-slate-800/30">
            <h3 className="text-lg font-bold text-white mb-3">How Power Rankings Work</h3>
            <p className="text-sm text-slate-300 leading-relaxed mb-4">
              Our power rankings blend traditional standings metrics (points, point percentage) with advanced analytics
              (goal differential, model win rates) to provide a more complete picture of team strength. Teams that
              outperform their record (high goal differential, strong underlying metrics) rank higher than their
              standings position suggests.
            </p>
            <div className="flex flex-wrap gap-4 text-xs text-slate-400">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-sky-500"></span>
                <span>Power Score = Points × 0.4 + Goal Diff × 0.3 + Point% × 0.3</span>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
