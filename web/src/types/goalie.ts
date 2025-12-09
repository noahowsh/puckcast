export type GoalieCard = {
  name: string;
  team: string;
  gamesPlayed?: number;
  record?: string;
  wins?: number;
  losses?: number;
  otLosses?: number;
  gaa?: number;
  savePct?: number;
  shutouts?: number;
  goalsAgainst?: number;
  shotsAgainst?: number;
  saves?: number;
  shotsAgainstPerGame?: number;
  savesPerGame?: number;
  expectedGoalsAgainst?: number;
  gsax?: number;
  rollingGsa: number;
  seasonGsa: number;
  restDays: number;
  startLikelihood: number; // 0-1
  trend: "surging" | "steady" | "fresh" | "fatigue watch" | "stable" | string;
  note: string;
  strengths: string[];
  watchouts: string[];
  nextOpponent: string;
};

export type GoalieStarter = {
  name: string;
  team: string;
  startLikelihood: number;
  restDays: number;
  record: string;
};

export type GoalieMatchup = {
  gameId: number;
  home: GoalieStarter | null;
  away: GoalieStarter | null;
  startTimeEt?: string;
  startTimeUtc?: string;
};

export type GoalieLeaderboards = {
  byGsax: Array<{ rank: number; name: string; team: string; gsax: number }>;
  bySavePct: Array<{ rank: number; name: string; team: string; savePct: number }>;
  byGaa: Array<{ rank: number; name: string; team: string; gaa: number }>;
  byWins: Array<{ rank: number; name: string; team: string; wins: number }>;
};

export type GoaliePulse = {
  updatedAt: string;
  notes: string;
  goalies: GoalieCard[];
  tonight?: {
    games: GoalieMatchup[];
  };
  leaderboards?: GoalieLeaderboards;
};
