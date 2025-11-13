export type GoalieStarter = {
  playerId: number;
  name: string;
  team: string;
  record: string;
  seasonSavePct: number;
  seasonGaa: number;
  startLikelihood: number | null;
  restDays: number | null;
  lastStart: string | null;
  lastOpponent: string | null;
  rollingSavePct: number | null;
  rollingShots: number | null;
};

export type GoalieMatchup = {
  gameId: string;
  matchup: string;
  startTimeEt: string;
  startTimeUtc: string;
  home: GoalieStarter | null;
  away: GoalieStarter | null;
};

export type GoalieHeatEntry = {
  name: string;
  team: string;
  rollingSavePct: number | null;
  seasonSavePct: number;
  deltaSavePct: number | null;
  restDays: number | null;
  lastOpponent: string | null;
};

export type GoalieRestEntry = {
  name: string;
  team: string;
  restDays: number | null;
  lastStart: string | null;
  startLikelihood: number | null;
};

export type GoalieSeasonLeader = {
  name: string;
  team: string;
  savePct: number;
  gaa: number;
  games: number;
  record: string;
};

export type LegacyGoalieCard = {
  name: string;
  team: string;
  rollingGsa: number;
  seasonGsa: number;
  restDays: number;
  startLikelihood: number;
  trend: string;
  note: string;
  strengths: string[];
  watchouts: string[];
  nextOpponent: string;
};

export type GoaliePulse = {
  updatedAt: string;
  targetDate: string;
  notes: string;
  tonight: {
    games: GoalieMatchup[];
  };
  heatCheck: {
    surging: GoalieHeatEntry[];
    cooling: GoalieHeatEntry[];
  };
  restWatch: GoalieRestEntry[];
  seasonLeaders: GoalieSeasonLeader[];
  goalies: LegacyGoalieCard[];
};
