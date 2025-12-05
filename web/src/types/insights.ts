export type StrategySummary = {
  name: string;
  bets: number;
  winRate: number;
  units: number;
  note: string;
  avgEdge: number;
};

export type ConfidenceBucket = {
  label: string;
  grade: string;
  min: number;
  max: number | null;
  accuracy: number;
  count: number;
  coverage?: number;
};

export type TeamPerformance = {
  team: string;
  abbrev: string;
  conference: string;
  division: string;
  games: number;
  wins: number;
  losses: number;
  record: string;
  points: number;
  modelAccuracy: number;
  winPct: number;
  correct: number;
};

export type StandingEntry = {
  team: string;
  abbrev: string;
  record: string;
  points: number;
  winPct: number;
};

export type MatchupInsight = {
  teams: string;
  games: number;
  correct: number;
  accuracy: number;
};

export type FeatureImportance = {
  feature: string;
  coefficient: number;
  absImportance: number;
};

export type DistributionFinding = {
  metric: string;
  correctMean: number;
  incorrectMean: number;
};

export type HeroStat = {
  label: string;
  value: string;
  detail: string;
};

export type HeadlineInsight = {
  title: string;
  detail: string;
};

export type BankrollPoint = {
  label: string;
  units: number;
};

export type ModelInsights = {
  generatedAt: string;
  overall: {
    games: number;
    accuracy: number;
    baseline: number;
    homeWinRate: number;
    brier: number;
    logLoss: number;
    avgEdge: number;
  };
  heroStats: HeroStat[];
  insights: HeadlineInsight[];
  strategies: StrategySummary[];
  confidenceBuckets: ConfidenceBucket[];
  teamPerformance: TeamPerformance[];
  standings: {
    east: StandingEntry[];
    west: StandingEntry[];
  };
  matchupInsights: {
    consistent: MatchupInsight[];
    volatile: MatchupInsight[];
  };
  featureImportance: FeatureImportance[];
  distributionFindings: DistributionFinding[];
  bankrollSeries: BankrollPoint[];
};
