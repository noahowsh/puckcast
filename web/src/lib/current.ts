import predictionsPayloadRaw from "@/data/todaysPredictions.json";
import standingsRaw from "@/data/currentStandings.json";
import type { Prediction, PredictionsPayload } from "@/types/prediction";

export type TeamSnapshot = {
  team: string;
  abbrev: string;
  games: number;
  avgProb: number;
  avgEdge: number;
  favoriteRate: number;
  record?: string;
  points?: number;
  pointPctg?: number;
  streak?: string;
  standingsRank?: number;
  nextGame?: {
    opponent: string;
    date: string;
    startTimeEt: string | null;
    edgeLabel: string;
    summary: string;
  };
};

export type MatchupSummary = {
  date: string;
  games: Array<{
    id: string;
    label: string;
    startTimeEt: string | null;
    edge: number;
    favorite: string;
    summary: string;
  }>;
};

export type CurrentStanding = {
  team: string;
  abbrev: string;
  wins: number;
  losses: number;
  ot: number;
  points: number;
  gamesPlayed: number;
  pointPctg: number;
  goalDifferential: number;
  goalsForPerGame?: number;
  goalsAgainstPerGame?: number;
  shotsForPerGame?: number;
  shotsAgainstPerGame?: number;
  powerPlayPct?: number;
  penaltyKillPct?: number;
};

const predictionsPayload = predictionsPayloadRaw as PredictionsPayload;
const standingsPayload = standingsRaw as { teams: CurrentStanding[] };
const standings = [...standingsPayload.teams].sort(
  (a, b) => b.points - a.points || b.wins - a.wins || b.goalDifferential - a.goalDifferential,
);
const standingsByAbbrev = new Map<string, CurrentStanding & { rank: number }>(
  standings.map((team, idx) => [team.abbrev, { ...team, rank: idx + 1 }]),
);

export function getCurrentPredictions(): PredictionsPayload {
  return predictionsPayload;
}

export function getCurrentStandings(): Array<CurrentStanding & { rank: number }> {
  return standings.map((team, idx) => ({ ...team, rank: idx + 1 }));
}

export function computeStandingsPowerScore(team: CurrentStanding & { rank?: number }): number {
  const pointComponent = team.points * 1.15;
  const pctComponent = (team.pointPctg ?? 0) * 120;
  const diffComponent = team.goalDifferential * 1.6;
  const offense = (team.goalsForPerGame ?? 0) * 14;
  const defense = (team.goalsAgainstPerGame ?? 0) * -12;
  const possession = ((team.shotsForPerGame ?? 0) - (team.shotsAgainstPerGame ?? 0)) * 1.2;
  return Math.round(pointComponent + pctComponent + diffComponent + offense + defense + possession);
}

const powerScore = (snapshot: TeamSnapshot) =>
  Math.round(snapshot.avgProb * 100 + snapshot.avgEdge * 100 * 0.5);

export function buildTeamSnapshots(games: Prediction[] = predictionsPayload.games): TeamSnapshot[] {
  const teams: Record<string, TeamSnapshot & { probSum: number; edgeSum: number; favoriteCount: number }> = {};

  const upsert = (
    teamKey: string,
    name: string,
    abbrev: string,
    opponent: string,
    winProb: number,
    signedEdge: number,
    startTimeEt: string | null,
    gameDate: string,
    summary: string,
  ) => {
    if (!teams[teamKey]) {
      teams[teamKey] = {
        team: name,
        abbrev,
        games: 0,
        avgProb: 0,
        avgEdge: 0,
        favoriteRate: 0,
        probSum: 0,
        edgeSum: 0,
        favoriteCount: 0,
      };
    }
    const record = teams[teamKey];
    record.games += 1;
    record.probSum += winProb;
    record.edgeSum += Math.abs(signedEdge);
    if (signedEdge > 0) {
      record.favoriteCount += 1;
    }
    const nextDate = record.nextGame?.date;
    if (!nextDate || gameDate < nextDate) {
      record.nextGame = {
        opponent,
        date: gameDate,
        startTimeEt,
        edgeLabel: signedEdge >= 0 ? `+${(Math.abs(signedEdge) * 100).toFixed(1)} pts` : `-${(Math.abs(signedEdge) * 100).toFixed(1)} pts`,
        summary,
      };
    }
  };

  games.forEach((game) => {
    const date = game.gameDate;
    upsert(
      `${game.homeTeam.name}-${game.homeTeam.abbrev}`,
      game.homeTeam.name,
      game.homeTeam.abbrev,
      game.awayTeam.abbrev,
      game.homeWinProb,
      game.edge,
      game.startTimeEt ?? null,
      date,
      game.summary,
    );
    upsert(
      `${game.awayTeam.name}-${game.awayTeam.abbrev}`,
      game.awayTeam.name,
      game.awayTeam.abbrev,
      game.homeTeam.abbrev,
      game.awayWinProb,
      -game.edge,
      game.startTimeEt ?? null,
      date,
      game.summary,
    );
  });

  return Object.values(teams)
    .map((record) => ({
      team: record.team,
      abbrev: record.abbrev,
      games: record.games,
      avgProb: record.games ? record.probSum / record.games : 0,
      avgEdge: record.games ? record.edgeSum / record.games : 0,
      favoriteRate: record.games ? record.favoriteCount / record.games : 0,
      record: standingsByAbbrev.get(record.abbrev)?.wins !== undefined
        ? `${standingsByAbbrev.get(record.abbrev)!.wins}-${standingsByAbbrev.get(record.abbrev)!.losses}-${standingsByAbbrev.get(record.abbrev)!.ot}`
        : undefined,
      points: standingsByAbbrev.get(record.abbrev)?.points,
      pointPctg: standingsByAbbrev.get(record.abbrev)?.pointPctg,
      standingsRank: standingsByAbbrev.get(record.abbrev)?.rank,
      nextGame: record.nextGame,
    }))
    .sort((a, b) => powerScore(b) - powerScore(a));
}

export function groupMatchupsByDate(games: Prediction[] = predictionsPayload.games): MatchupSummary[] {
  const grouped: Record<string, MatchupSummary["games"]> = {};
  games.forEach((game) => {
    const date = game.gameDate;
    if (!grouped[date]) {
      grouped[date] = [];
    }
    grouped[date].push({
      id: game.id,
      label: `${game.awayTeam.abbrev} @ ${game.homeTeam.abbrev}`,
      startTimeEt: game.startTimeEt ?? null,
      edge: Math.abs(game.edge),
      favorite: game.modelFavorite === "home" ? game.homeTeam.abbrev : game.awayTeam.abbrev,
      summary: game.summary,
    });
  });

  return Object.entries(grouped)
    .sort(([a], [b]) => (a < b ? -1 : 1))
    .map(([date, games]) => ({
      date,
      games: games.sort((a, b) => (a.startTimeEt ?? "").localeCompare(b.startTimeEt ?? "")),
    }));
}

export function formatPowerScore(snapshot: TeamSnapshot): number {
  return powerScore(snapshot);
}
