// Player Stats Types for Puckcast
// Comprehensive types for skater and goalie statistics from NHL API

// =============================================================================
// Base Player Types
// =============================================================================

export type PlayerPosition = "C" | "L" | "R" | "D" | "G";
export type PositionType = "forward" | "defenseman" | "goalie";
export type ShootsCatches = "L" | "R";

export type PlayerBio = {
  playerId: number;
  firstName: string;
  lastName: string;
  fullName: string;
  teamAbbrev: string;
  teamName: string;
  position: PlayerPosition;
  positionType: PositionType;
  jerseyNumber: number | null;
  shootsCatches: ShootsCatches;
  heightInInches: number | null;
  weightInPounds: number | null;
  birthDate: string | null;
  birthCity: string | null;
  birthCountry: string | null;
  nationality: string | null;
  isActive: boolean;
  isRookie: boolean;
  headshot: string | null;
};

// =============================================================================
// Skater Stats Types
// =============================================================================

export type SkaterSeasonStats = {
  playerId: number;
  season: string; // e.g., "20242025"
  teamAbbrev: string;
  gamesPlayed: number;
  goals: number;
  assists: number;
  points: number;
  plusMinus: number;
  penaltyMinutes: number;
  powerPlayGoals: number;
  powerPlayPoints: number;
  shorthandedGoals: number;
  shorthandedPoints: number;
  gameWinningGoals: number;
  overtimeGoals: number;
  shots: number;
  shootingPct: number; // e.g., 0.125 for 12.5%
  timeOnIcePerGame: string; // e.g., "18:32"
  faceoffWinPct: number | null; // For centers
  blockedShots: number;
  hits: number;
  takeaways: number;
  giveaways: number;
};

export type SkaterAdvancedStats = {
  playerId: number;
  season: string;
  // Per 60 stats
  goalsPerGame: number;
  assistsPerGame: number;
  pointsPerGame: number;
  shotsPerGame: number;
  // Possession (if available)
  corsiForPct: number | null;
  fenwickForPct: number | null;
  // Other advanced
  offensiveZoneStartPct: number | null;
  pdo: number | null;
};

export type SkaterCard = {
  bio: PlayerBio;
  stats: SkaterSeasonStats;
  advanced?: SkaterAdvancedStats | null;
  recentForm?: SkaterRecentForm | null;
  leagueRanks?: SkaterLeagueRanks | null;
};

export type SkaterRecentForm = {
  last5Games: {
    goals: number;
    assists: number;
    points: number;
    shots: number;
    plusMinus: number;
  };
  last10Games: {
    goals: number;
    assists: number;
    points: number;
    shots: number;
    plusMinus: number;
  };
  streak: {
    type: "points" | "goals" | "assists" | "none";
    count: number;
  } | null;
  trend: "hot" | "cold" | "steady";
};

export type SkaterLeagueRanks = {
  goals: number | null;
  assists: number | null;
  points: number | null;
  plusMinus: number | null;
  powerPlayGoals: number | null;
  shots: number | null;
  hits: number | null;
  blockedShots: number | null;
  timeOnIce: number | null;
};

// =============================================================================
// Goalie Stats Types
// =============================================================================

export type GoalieSeasonStats = {
  playerId: number;
  season: string;
  teamAbbrev: string;
  gamesPlayed: number;
  gamesStarted: number;
  wins: number;
  losses: number;
  otLosses: number;
  shotsAgainst: number;
  goalsAgainst: number;
  saves: number;
  savePct: number; // e.g., 0.915 for 91.5%
  goalsAgainstAverage: number;
  shutouts: number;
  timeOnIce: string; // Total TOI
  qualityStarts: number | null;
  qualityStartsPct: number | null;
};

export type GoalieAdvancedStats = {
  playerId: number;
  season: string;
  // Goals Saved Above Expected
  goalsAboveExpected: number | null;
  goalsAboveExpectedPer60: number | null;
  // High danger save %
  highDangerSavePct: number | null;
  highDangerShotsAgainst: number | null;
  // Medium danger save %
  mediumDangerSavePct: number | null;
  mediumDangerShotsAgainst: number | null;
  // Low danger save %
  lowDangerSavePct: number | null;
  lowDangerShotsAgainst: number | null;
  // Rebound control
  reboundGoalsAgainst: number | null;
  reboundGoalsAgainstPct: number | null;
};

export type GoalieDetailCard = {
  bio: PlayerBio;
  stats: GoalieSeasonStats;
  advanced?: GoalieAdvancedStats | null;
  recentForm?: GoalieRecentForm | null;
  leagueRanks?: GoalieLeagueRanks | null;
};

export type GoalieRecentForm = {
  last5Starts: {
    wins: number;
    losses: number;
    savePct: number;
    goalsAgainstAverage: number;
  };
  last10Starts: {
    wins: number;
    losses: number;
    savePct: number;
    goalsAgainstAverage: number;
  };
  currentStreak: {
    type: "W" | "L" | "OTL";
    count: number;
  } | null;
  trend: "hot" | "cold" | "steady";
  restDays: number;
};

export type GoalieLeagueRanks = {
  wins: number | null;
  savePct: number | null;
  goalsAgainstAverage: number | null;
  shutouts: number | null;
  gamesPlayed: number | null;
  qualityStartsPct: number | null;
};

// =============================================================================
// Team Roster & Leaders Types
// =============================================================================

export type TeamRoster = {
  teamAbbrev: string;
  teamName: string;
  forwards: SkaterCard[];
  defensemen: SkaterCard[];
  goalies: GoalieDetailCard[];
};

export type TeamLeaders = {
  teamAbbrev: string;
  points: SkaterCard | null;
  goals: SkaterCard | null;
  assists: SkaterCard | null;
  plusMinus: SkaterCard | null;
  goalie: GoalieDetailCard | null;
};

// =============================================================================
// League Leaders Types
// =============================================================================

export type LeagueSkaterLeaders = {
  updatedAt: string;
  season: string;
  points: SkaterCard[];
  goals: SkaterCard[];
  assists: SkaterCard[];
  plusMinus: SkaterCard[];
  powerPlayGoals: SkaterCard[];
  gameWinningGoals: SkaterCard[];
  shots: SkaterCard[];
  hits: SkaterCard[];
  blockedShots: SkaterCard[];
  timeOnIce: SkaterCard[];
  rookies: SkaterCard[];
};

export type LeagueGoalieLeaders = {
  updatedAt: string;
  season: string;
  wins: GoalieDetailCard[];
  savePct: GoalieDetailCard[];
  goalsAgainstAverage: GoalieDetailCard[];
  shutouts: GoalieDetailCard[];
  gamesPlayed: GoalieDetailCard[];
};

// =============================================================================
// API Response Types (NHL API)
// =============================================================================

export type NHLApiSkaterStats = {
  playerId: number;
  skaterFullName: string;
  lastName: string;
  teamAbbrevs: string;
  positionCode: string;
  gamesPlayed: number;
  goals: number;
  assists: number;
  points: number;
  plusMinus: number;
  penaltyMinutes: number;
  ppGoals: number;
  ppPoints: number;
  shGoals: number;
  shPoints: number;
  gameWinningGoals: number;
  otGoals: number;
  shots: number;
  shootingPct: number;
  timeOnIcePerGame: number; // in seconds
  faceoffWinPct: number | null;
};

export type NHLApiGoalieStats = {
  playerId: number;
  goalieFullName: string;
  lastName: string;
  teamAbbrevs: string;
  gamesPlayed: number;
  gamesStarted: number;
  wins: number;
  losses: number;
  otLosses: number;
  shotsAgainst: number;
  goalsAgainst: number;
  saves: number;
  savePct: number;
  goalsAgainstAverage: number;
  shutouts: number;
  timeOnIce: number; // in seconds
};

// =============================================================================
// Player Hub Integration Types
// =============================================================================

export type PlayerHubData = {
  updatedAt: string;
  season: string;
  skaterLeaders: LeagueSkaterLeaders;
  goalieLeaders: LeagueGoalieLeaders;
  teamRosters: Record<string, TeamRoster>;
  teamLeaders: Record<string, TeamLeaders>;
};

// =============================================================================
// Utility Types
// =============================================================================

export type PlayerSortField =
  | "points" | "goals" | "assists" | "plusMinus"
  | "powerPlayGoals" | "shots" | "hits" | "blockedShots"
  | "gamesPlayed" | "timeOnIce";

export type GoalieSortField =
  | "wins" | "savePct" | "goalsAgainstAverage"
  | "shutouts" | "gamesPlayed" | "gamesStarted";

export type PlayerFilter = {
  team?: string;
  position?: PlayerPosition | PositionType;
  minGames?: number;
  isRookie?: boolean;
};

// =============================================================================
// Display Helper Types
// =============================================================================

export type StatDisplayConfig = {
  key: string;
  label: string;
  format: "number" | "decimal" | "percent" | "time" | "plusMinus";
  precision?: number;
  higherIsBetter?: boolean;
};

export const SKATER_STAT_CONFIGS: StatDisplayConfig[] = [
  { key: "gamesPlayed", label: "GP", format: "number", higherIsBetter: true },
  { key: "goals", label: "G", format: "number", higherIsBetter: true },
  { key: "assists", label: "A", format: "number", higherIsBetter: true },
  { key: "points", label: "P", format: "number", higherIsBetter: true },
  { key: "plusMinus", label: "+/-", format: "plusMinus", higherIsBetter: true },
  { key: "penaltyMinutes", label: "PIM", format: "number" },
  { key: "powerPlayGoals", label: "PPG", format: "number", higherIsBetter: true },
  { key: "powerPlayPoints", label: "PPP", format: "number", higherIsBetter: true },
  { key: "shots", label: "S", format: "number", higherIsBetter: true },
  { key: "shootingPct", label: "S%", format: "percent", precision: 1, higherIsBetter: true },
  { key: "hits", label: "HIT", format: "number", higherIsBetter: true },
  { key: "blockedShots", label: "BLK", format: "number", higherIsBetter: true },
  { key: "timeOnIcePerGame", label: "TOI", format: "time", higherIsBetter: true },
];

export const GOALIE_STAT_CONFIGS: StatDisplayConfig[] = [
  { key: "gamesPlayed", label: "GP", format: "number", higherIsBetter: true },
  { key: "gamesStarted", label: "GS", format: "number", higherIsBetter: true },
  { key: "wins", label: "W", format: "number", higherIsBetter: true },
  { key: "losses", label: "L", format: "number" },
  { key: "otLosses", label: "OTL", format: "number" },
  { key: "savePct", label: "SV%", format: "percent", precision: 3, higherIsBetter: true },
  { key: "goalsAgainstAverage", label: "GAA", format: "decimal", precision: 2, higherIsBetter: false },
  { key: "shutouts", label: "SO", format: "number", higherIsBetter: true },
  { key: "saves", label: "SV", format: "number", higherIsBetter: true },
  { key: "shotsAgainst", label: "SA", format: "number" },
];

// =============================================================================
// Season Projection Types (Inspired by Production Card)
// =============================================================================

export type StatProjection = {
  average: number;
  median: number;
  mode: number;
  min: number;
  max: number;
  current: number;
};

export type SeasonProjection = {
  playerId: number;
  season: string;
  gamesRemaining: number;
  goals: StatProjection;
  assists: StatProjection;
  points: StatProjection;
  shots?: StatProjection;
  powerPlayPoints?: StatProjection;
  // Award probabilities (0-100%)
  awardProbabilities: {
    mostPoints: number; // Art Ross
    mostGoals: number; // Rocket Richard
    mostAssists: number;
    hartTrophy?: number;
    selkeTrophy?: number;
    norrisTrophy?: number;
  };
  // Milestone probabilities (probability of reaching each threshold)
  milestoneProbabilities: {
    goals: Record<number, number>; // e.g., { 20: 95.5, 30: 78.2, 40: 45.1, 50: 12.3 }
    assists: Record<number, number>;
    points: Record<number, number>;
  };
  // Distribution description
  distributionSummary: string;
};

// =============================================================================
// Skill Profile Types (GOA%-Style Card)
// =============================================================================

export type PercentileRating = {
  value: number; // 0-100 percentile
  tier: "elite" | "above-average" | "average" | "below-average" | "replacement";
};

export type SkillProfile = {
  playerId: number;
  season: string;
  position: PlayerPosition;
  // Overall skill score (like GOA%)
  overallRating: PercentileRating;
  // Even-strength percentiles
  evenStrength: {
    offensive: PercentileRating;
    defensive: PercentileRating;
    overall: PercentileRating;
  };
  // Special teams percentiles
  specialTeams: {
    powerPlayOffense: PercentileRating;
    penaltyKillDefense: PercentileRating | null; // null if player doesn't PK
    combinedPPEV: PercentileRating;
  };
  // Talent/skill percentiles
  talents: {
    finishing: PercentileRating; // Goal scoring ability
    playmaking: PercentileRating; // Assist/setup ability
    penaltyImpact: PercentileRating; // Penalties drawn vs taken
    versatility: PercentileRating; // All-situations contribution
  };
  // Text summary of player's skill shape
  skillSummary: string;
};

// =============================================================================
// On-Ice Impact / RAPM Types
// =============================================================================

export type ImpactMetric = {
  percentile: number; // 0-100
  tier: "elite" | "above-average" | "average" | "below-average" | "poor";
};

export type OnIceImpact = {
  playerId: number;
  season: string;
  position: PlayerPosition;
  evTimeOnIce: number; // minutes
  // FOR metrics (offensive impact)
  forMetrics: {
    goals: ImpactMetric;
    shots: ImpactMetric;
    expectedGoals: ImpactMetric;
    corsi: ImpactMetric;
    shotQuality: ImpactMetric;
  };
  // AGAINST metrics (defensive impact)
  againstMetrics: {
    goals: ImpactMetric;
    shots: ImpactMetric;
    expectedGoals: ImpactMetric;
    corsi: ImpactMetric;
    shotQuality: ImpactMetric;
  };
  // General advanced metrics
  general: {
    netExpectedGoals: ImpactMetric;
    netCorsi: ImpactMetric;
    finishing: ImpactMetric;
    shotBlocking: ImpactMetric;
  };
  // Summary description
  impactSummary: string;
};
