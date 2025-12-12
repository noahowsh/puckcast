export type TeamInfo = {
  name: string;
  abbrev: string;
};

export type ConfidenceGrade = "A+" | "A" | "B+" | "B" | "C+" | "C";

export type Prediction = {
  id: string;
  gameDate: string;
  startTimeEt: string | null;
  startTimeUtc: string | null;
  homeTeam: TeamInfo;
  awayTeam: TeamInfo;
  homeWinProb: number;
  awayWinProb: number;
  confidenceScore: number;
  confidenceGrade: ConfidenceGrade;
  edge: number;
  modelFavorite: "home" | "away";
  summary: string;
  venue?: string | null;
  season?: string | null;
  specialTeams?: {
    home: SpecialTeamsSplit | null;
    away: SpecialTeamsSplit | null;
  };
  dayOfInfo?: DayOfInfo;
  projectedGoalies?: {
    home: {
      name: string;
      team: string;
      startLikelihood: number;
      restDays: number;
      record: string;
    } | null;
    away: {
      name: string;
      team: string;
      startLikelihood: number;
      restDays: number;
      record: string;
    } | null;
    startTimeEt?: string;
    startTimeUtc?: string;
  };
};

export type PredictionsPayload = {
  generatedAt: string;
  games: Prediction[];
};

export type SpecialTeamsSplit = {
  powerPlayPct?: number | null;
  opponentPenaltyKillPct?: number | null;
  diff?: number | null;
};

export type StartingGoalieInfo = {
  team: string;
  playerId?: number | null;
  goalieName?: string | null;
  confirmedStart: boolean;
  statusCode?: string | null;
  statusDescription?: string | null;
};

export type DayOfInfo = {
  homeGoalie?: StartingGoalieInfo | null;
  awayGoalie?: StartingGoalieInfo | null;
  homeInjuryCount?: number;
  awayInjuryCount?: number;
};

export type StartingGoaliesPayload = {
  generatedAt: string;
  date: string;
  teams?: Record<string, StartingGoalieInfo>;
  games: Array<{
    gameId: string;
    homeTeam?: string | null;
    awayTeam?: string | null;
    homeGoalie?: string | StartingGoalieInfo | null;
    awayGoalie?: string | StartingGoalieInfo | null;
    source?: string;
    confidence?: number;
  }>;
};

export type PlayerInjuryEntry = {
  team: string;
  playerId?: number | null;
  name?: string | null;
  statusCode?: string | null;
  statusDescription?: string | null;
  position?: string | null;
};

export type PlayerInjuriesPayload = {
  generatedAt: string;
  date: string;
  teams: Record<string, { injuries: PlayerInjuryEntry[] }>;
  games: Array<{
    gameId: string;
    date?: string | null;
    home?: string | null;
    away?: string | null;
    homeInjuries: PlayerInjuryEntry[];
    awayInjuries: PlayerInjuryEntry[];
  }>;
};
