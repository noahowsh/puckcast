import { buildTeamSnapshots, computeStandingsPowerScore, getCurrentStandings, groupMatchupsByDate, type MatchupSummary, type TeamSnapshot } from "@/lib/current";
import standingsSnapshot from "@/data/currentStandings.json";

const snapshots = buildTeamSnapshots();
const snapshotMap = new Map(snapshots.map((team) => [team.abbrev, team]));
const standings = getCurrentStandings();
const standingsMeta = standingsSnapshot as { generatedAt?: string };

type LeaderboardRow = {
  currentRank: number;
  standingsRank: number;
  movement: number;
  team: string;
  abbrev: string;
  record: string;
  points: number;
  goalDifferential: number;
  pointPctg: number;
  goalsForPerGame?: number;
  goalsAgainstPerGame?: number;
  powerScore: number;
  nextGame?: TeamSnapshot["nextGame"];
  overlay?: TeamSnapshot;
};

const rowsPreSort: LeaderboardRow[] = standings.map((standing) => {
  const snap = snapshotMap.get(standing.abbrev);
  const power = computeStandingsPowerScore(standing);
  const record = `${standing.wins}-${standing.losses}-${standing.ot}`;
  return {
    currentRank: 0,
    standingsRank: standing.rank,
    movement: 0,
    team: standing.team,
    abbrev: standing.abbrev,
    record,
    points: standing.points,
    goalDifferential: standing.goalDifferential,
    pointPctg: standing.pointPctg,
    goalsForPerGame: standing.goalsForPerGame,
    goalsAgainstPerGame: standing.goalsAgainstPerGame,
    powerScore: power,
    nextGame: snap?.nextGame,
    overlay: snap,
  };
});

const rankedRows = rowsPreSort
  .sort((a, b) => b.powerScore - a.powerScore)
  .map((row, idx) => ({
    ...row,
    currentRank: idx + 1,
    movement: row.standingsRank - (idx + 1),
  }));

const biggestBoost = rankedRows.reduce<LeaderboardRow | null>((best, row) => {
  if (row.movement <= 0) return best;
  if (!best || row.movement > best.movement) {
    return row;
  }
  return best;
}, null);

const biggestSlide = rankedRows.reduce<LeaderboardRow | null>((best, row) => {
  if (row.movement >= 0) return best;
  if (!best || row.movement < best.movement) {
    return row;
  }
  return best;
}, null);

const alignedClubs = rankedRows.filter((row) => Math.abs(row.movement) <= 1).length;

const computeWeekStart = (anchor: Date) => {
  const base = new Date(anchor);
  const day = base.getUTCDay();
  const diff = (day + 6) % 7;
  base.setUTCDate(base.getUTCDate() - diff);
  base.setUTCHours(0, 0, 0, 0);
  return base;
};

const weekAnchor = standingsMeta.generatedAt ? new Date(standingsMeta.generatedAt) : new Date();
const leaderboardWeekStart = computeWeekStart(weekAnchor);
const leaderboardWeekLabel = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" }).format(leaderboardWeekStart);

const leaderboardHighlights = [
  {
    label: "Power #1",
    value: rankedRows[0]?.team ?? "—",
    detail: rankedRows[0] ? `Week of ${leaderboardWeekLabel}` : "Awaiting slate",
  },
  {
    label: "Biggest riser",
    value: biggestBoost ? `${biggestBoost.team} (+${biggestBoost.movement})` : "—",
    detail: biggestBoost ? `Standings #${biggestBoost.standingsRank}` : "No change",
  },
  {
    label: "Biggest slide",
    value: biggestSlide ? `${biggestSlide.team} (-${Math.abs(biggestSlide.movement)})` : "—",
    detail: biggestSlide ? `Standings #${biggestSlide.standingsRank}` : "No change",
  },
  {
    label: "Aligned clubs",
    value: `${alignedClubs}/32`,
    detail: "±1 spot vs standings",
  },
];

const schedule = groupMatchupsByDate().slice(0, 3);

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;
const formatGameDate = (iso?: string) => {
  if (!iso) return "TBD";
  return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" }).format(new Date(`${iso}T00:00:00Z`));
};

export default function LeaderboardsPage() {
  return (
    <div className="relative min-h-screen bg-slate-950">
      {/* Subtle background gradient */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-b from-sky-950/20 via-slate-950 to-slate-950" />
      </div>

      <div className="relative mx-auto max-w-7xl px-6 py-16 lg:px-8">
        {/* Header */}
        <section className="mb-32">
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-sky-500/20 bg-sky-500/5 px-3 py-1">
            <span className="text-xs font-medium text-sky-400">Power Rankings</span>
          </div>
          <h1 className="mb-8 text-6xl font-extrabold text-white lg:text-7xl">Live power rankings</h1>
          <p className="max-w-3xl text-xl text-slate-300">
            Composite scores based on points, goal differential, tempo, and shot share. Updated every Monday to capture the current week's snapshot.
          </p>
          <p className="mt-2 text-sm text-slate-500">Week of {leaderboardWeekLabel}</p>
        </section>

        {/* Highlights */}
        <section className="mb-32">
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {leaderboardHighlights.map((card) => (
              <div key={card.label} className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
                <p className="text-sm font-medium text-slate-400">{card.label}</p>
                <p className="mt-2 text-2xl font-bold text-white">{card.value}</p>
                <p className="mt-1 text-sm text-slate-500">{card.detail}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Rankings Table */}
        <section className="mb-32">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-2xl font-extrabold text-white">Full Rankings</h2>
              <p className="text-sm text-slate-500">Week of {leaderboardWeekLabel}</p>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="border-b border-slate-800">
                  <tr className="text-slate-400">
                    <th className="py-3 pr-4 text-left font-medium">Rank</th>
                    <th className="py-3 px-4 text-left font-medium">Team</th>
                    <th className="py-3 px-4 text-left font-medium">Record</th>
                    <th className="py-3 px-4 text-left font-medium">Points</th>
                    <th className="py-3 px-4 text-left font-medium">Goal Diff</th>
                    <th className="py-3 px-4 text-left font-medium">Power Score</th>
                    <th className="py-3 px-4 text-left font-medium">Movement</th>
                    <th className="py-3 px-4 text-left font-medium">Model Win %</th>
                    <th className="py-3 px-4 text-left font-medium">Next Game</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {rankedRows.map((row) => (
                    <tr key={row.team} className="text-slate-300">
                      <td className="py-3 pr-4 font-semibold text-white">#{row.currentRank}</td>
                      <td className="py-3 px-4">
                        <p className="font-semibold text-white">{row.team}</p>
                        <p className="text-xs text-slate-500">Standings #{row.standingsRank}</p>
                      </td>
                      <td className="py-3 px-4">{row.record}</td>
                      <td className="py-3 px-4">{row.points}</td>
                      <td className="py-3 px-4">
                        <span className={row.goalDifferential >= 0 ? "text-sky-400" : "text-slate-400"}>
                          {row.goalDifferential >= 0 ? "+" : ""}
                          {row.goalDifferential}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <p className="font-semibold text-white">{row.powerScore}</p>
                        <p className="text-xs text-slate-500">{pct(row.pointPctg)} pts</p>
                      </td>
                      <td className="py-3 px-4">
                        <Movement movement={row.movement} />
                      </td>
                      <td className="py-3 px-4">
                        {row.overlay ? (
                          <div className="text-xs text-slate-400">
                            <p>{pct(row.overlay.avgProb)} win</p>
                            <p className="text-slate-500">{(row.overlay.avgEdge * 100).toFixed(1)} pts edge</p>
                          </div>
                        ) : (
                          <p className="text-xs text-slate-500">No data</p>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        {row.nextGame ? (
                          <div className="text-xs text-slate-400">
                            <p>vs {row.nextGame.opponent}</p>
                            <p className="text-slate-500">
                              {formatGameDate(row.nextGame.date)} · {row.nextGame.startTimeEt ?? "TBD"}
                            </p>
                          </div>
                        ) : (
                          <p className="text-xs text-slate-500">Idle</p>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Upcoming Schedule */}
        <section className="mb-32">
          <h2 className="mb-10 text-3xl font-extrabold text-white">Upcoming Schedule</h2>
          <div className="space-y-8">
            {schedule.map((day) => (
              <DateGroup key={day.date} day={day} />
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

function DateGroup({ day }: { day: MatchupSummary }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
      <p className="mb-4 text-sm font-medium text-slate-400">{day.date}</p>
      <div className="space-y-4">
        {day.games.map((game) => (
          <article key={game.id} className="rounded-lg border border-slate-800/50 bg-slate-950/50 p-4">
            <p className="text-sm font-semibold text-white">{game.label}</p>
            <p className="mt-1 text-xs text-slate-400">
              {game.startTimeEt ?? "TBD"} · Favorite: {game.favorite} · Edge: {(game.edge * 100).toFixed(1)} pts
            </p>
            <p className="mt-2 text-xs text-slate-300">{game.summary}</p>
          </article>
        ))}
      </div>
    </div>
  );
}

function Movement({ movement }: { movement: number }) {
  if (movement > 0) {
    return (
      <div className="text-xs">
        <p className="font-medium text-sky-400">▲ +{movement}</p>
        <p className="text-slate-500">Boost</p>
      </div>
    );
  }
  if (movement < 0) {
    return (
      <div className="text-xs">
        <p className="font-medium text-slate-400">▼ {Math.abs(movement)}</p>
        <p className="text-slate-500">Dip</p>
      </div>
    );
  }
  return (
    <div className="text-xs">
      <p className="font-medium text-slate-400">—</p>
      <p className="text-slate-500">Stable</p>
    </div>
  );
}
