export type StatusSnapshot = {
  generatedAt: string;
  predictions: {
    generatedAt: string | null;
    games: number;
    staleMinutes: number | null;
  };
  goalies: {
    updatedAt: string | null;
    projectedGames: number;
    projectedStarters: number;
    staleMinutes: number | null;
  };
  standings: {
    generatedAt: string | null;
    teams: number;
    staleMinutes: number | null;
  };
  deploy: {
    commit: string | null;
    branch: string | null;
    env: string | null;
  };
};
