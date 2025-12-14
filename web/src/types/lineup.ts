// Lineup & Injury Types for Puckcast
// Comprehensive types for injury tracking and projected lineups

// =============================================================================
// Injury Types
// =============================================================================

export type InjuryStatus =
  | "day-to-day"
  | "DTD"           // Day-to-day (alternate format)
  | "GTD"           // Game-time decision
  | "questionable"
  | "probable"
  | "out"
  | "OUT"           // Out (alternate format)
  | "IR"            // Injured Reserve (minimum 7 days)
  | "IR-LT"         // Long-Term Injured Reserve (minimum 24 days)
  | "IR-NR"         // Injured Reserve - Non-Roster
  | "INJ"           // Generic injured
  | "suspended"
  | "personal"
  | "healthy";

export type InjuryType =
  | "upper-body"
  | "lower-body"
  | "head"
  | "concussion"
  | "illness"
  | "undisclosed"
  | "knee"
  | "ankle"
  | "shoulder"
  | "back"
  | "hand"
  | "wrist"
  | "groin"
  | "hip"
  | "foot"
  | "other";

export type PlayerInjury = {
  playerId: number;
  playerName: string;
  teamAbbrev: string;
  position: string;
  status: InjuryStatus;
  injuryType: InjuryType;
  injuryDescription: string;
  dateInjured: string | null;
  expectedReturn: string | null;
  lastUpdated: string;
  isOut: boolean; // true if player cannot play
};

export type TeamInjuryReport = {
  teamAbbrev: string;
  teamName: string;
  injuries: PlayerInjury[];
  totalOut: number;
  forwardsOut: number;
  defensemenOut: number;
  goaliesOut: number;
  impactRating: number; // 0-100 scale of how much injuries hurt the team
  lastUpdated: string;
};

export type LeagueInjuryReport = {
  updatedAt: string;
  source: string;
  teams: Record<string, TeamInjuryReport>;
  totalInjuries: number;
  recentChanges: InjuryChange[];
};

export type InjuryChange = {
  playerId: number;
  playerName: string;
  teamAbbrev: string;
  changeType: "injured" | "returned" | "status_change";
  previousStatus: InjuryStatus;
  newStatus: InjuryStatus;
  timestamp: string;
};

// =============================================================================
// Lineup Types
// =============================================================================

export type LineupPlayer = {
  playerId: number;
  playerName: string;
  position: string;
  jerseyNumber: number | null;
  // Performance metrics for ranking
  gamesPlayed: number;
  timeOnIcePerGame: number; // in seconds
  goals: number;
  assists: number;
  points: number;
  plusMinus: number;
  // Additional stats
  shots: number;
  shootingPct: number;
  powerPlayGoals: number;
  powerPlayPoints: number;
  hits: number;
  blockedShots: number;
  // Computed ranking score
  rankingScore: number;
  // Status
  isHealthy: boolean;
  injuryStatus: InjuryStatus | null;
};

export type GoalieLineup = {
  playerId: number;
  playerName: string;
  jerseyNumber: number | null;
  gamesPlayed: number;
  gamesStarted: number;
  wins: number;
  savePct: number;
  goalsAgainstAverage: number;
  // Ranking/status
  rankingScore: number;
  isHealthy: boolean;
  isProjectedStarter: boolean;
  startLikelihood: number;
  restDays: number;
};

export type TeamLineup = {
  teamAbbrev: string;
  teamName: string;
  // Position groups
  forwards: LineupPlayer[];
  defensemen: LineupPlayer[];
  goalies: GoalieLineup[];
  // Detected lineup sizes (from historical data)
  typicalForwards: number;  // Usually 12-14
  typicalDefensemen: number; // Usually 6-8
  typicalGoalies: number;    // Usually 2
  // Projected active roster
  projectedForwards: LineupPlayer[];
  projectedDefensemen: LineupPlayer[];
  projectedGoalies: GoalieLineup[];
  // Scratches (healthy but not dressing)
  healthyScratches: LineupPlayer[];
  // Metrics
  lineupStrength: LineupStrengthMetrics;
  lastUpdated: string;
};

// =============================================================================
// Lineup Strength Metrics
// =============================================================================

export type LineupStrengthMetrics = {
  // Overall quality index (0-100)
  overallQuality: number;
  // Offensive metrics
  offensiveStrength: number;
  avgForwardPoints: number;
  avgForwardTOI: number;
  topLineStrength: number;
  // Defensive metrics
  defensiveStrength: number;
  avgDefensemanPoints: number;
  avgDefensemanTOI: number;
  topPairStrength: number;
  // Goaltending
  goalieStrength: number;
  starterRating: number;
  backupRating: number;
  // Impact adjustments
  injuryImpact: number;  // Negative number showing strength lost
  missingPlayerImpact: MissingPlayerImpact[];
  // Comparison to full strength
  percentOfFullStrength: number;
};

export type MissingPlayerImpact = {
  playerId: number;
  playerName: string;
  position: string;
  impactScore: number; // How much their absence hurts (0-10)
  statsLost: {
    pointsPerGame: number;
    toiPerGame: number;
  };
};

// =============================================================================
// Lineup History (for detecting typical sizes)
// =============================================================================

export type LineupHistoryEntry = {
  gameId: string;
  gameDate: string;
  teamAbbrev: string;
  forwardsUsed: number;
  defensemenUsed: number;
  goaliesUsed: number;
  starterGoalieId: number;
};

export type TeamLineupPattern = {
  teamAbbrev: string;
  // Detected from last 10 games
  avgForwardsUsed: number;
  avgDefensemenUsed: number;
  medianForwardsUsed: number;
  medianDefensemenUsed: number;
  // For projections
  projectedForwardSlots: number;
  projectedDefensemanSlots: number;
};

// =============================================================================
// ESPN Scraping Types
// =============================================================================

export type ESPNInjuryEntry = {
  name: string;
  team: string;
  position: string;
  status: string;
  injury: string;
  expectedReturn: string | null;
};

export type ESPNInjuryResponse = {
  teams: {
    name: string;
    abbrev: string;
    injuries: ESPNInjuryEntry[];
  }[];
  scrapedAt: string;
};

// =============================================================================
// Model Feature Types
// =============================================================================

export type LineupFeatures = {
  teamAbbrev: string;
  gameId: string;
  // Raw strength metrics
  lineupQuality: number;
  offensiveStrength: number;
  defensiveStrength: number;
  goalieStrength: number;
  // Injury impact
  injuryImpact: number;
  keyPlayersOut: number;
  percentFullStrength: number;
  // Positional depth
  forwardDepth: number;
  defenseDepth: number;
  goalieDepth: number;
  // Comparative features (vs opponent)
  lineupAdvantage: number; // positive = advantage
  offensiveAdvantage: number;
  defensiveAdvantage: number;
  goalieAdvantage: number;
};

// =============================================================================
// Data Refresh Types
// =============================================================================

export type InjuryRefreshResult = {
  success: boolean;
  timestamp: string;
  teamsUpdated: number;
  injuriesFound: number;
  changesDetected: InjuryChange[];
  errors: string[];
};

export type LineupRefreshResult = {
  success: boolean;
  timestamp: string;
  teamsProcessed: number;
  playersRanked: number;
  errors: string[];
};

// =============================================================================
// Utility Types
// =============================================================================

export type PositionGroup = "forward" | "defenseman" | "goalie";

export function getPositionGroup(position: string): PositionGroup {
  if (position === "G") return "goalie";
  if (position === "D") return "defenseman";
  return "forward"; // C, L, R, LW, RW, F, W
}

export function isPlayerOut(status: InjuryStatus): boolean {
  return status !== "healthy" && status !== "day-to-day";
}

// Team abbreviation mapping for ESPN -> NHL
export const ESPN_TEAM_MAP: Record<string, string> = {
  "Anaheim": "ANA",
  "Arizona": "ARI",
  "Boston": "BOS",
  "Buffalo": "BUF",
  "Calgary": "CGY",
  "Carolina": "CAR",
  "Chicago": "CHI",
  "Colorado": "COL",
  "Columbus": "CBJ",
  "Dallas": "DAL",
  "Detroit": "DET",
  "Edmonton": "EDM",
  "Florida": "FLA",
  "Los Angeles": "LAK",
  "Minnesota": "MIN",
  "Montreal": "MTL",
  "Nashville": "NSH",
  "New Jersey": "NJD",
  "NY Islanders": "NYI",
  "NY Rangers": "NYR",
  "Ottawa": "OTT",
  "Philadelphia": "PHI",
  "Pittsburgh": "PIT",
  "San Jose": "SJS",
  "Seattle": "SEA",
  "St. Louis": "STL",
  "Tampa Bay": "TBL",
  "Toronto": "TOR",
  "Utah": "UTA",
  "Vancouver": "VAN",
  "Vegas": "VGK",
  "Washington": "WSH",
  "Winnipeg": "WPG",
};

// Status mapping from ESPN text to our types
export const ESPN_STATUS_MAP: Record<string, InjuryStatus> = {
  "day-to-day": "day-to-day",
  "out": "out",
  "injured reserve": "IR",
  "ir": "IR",
  "long-term injured reserve": "IR-LT",
  "ir-lt": "IR-LT",
  "ltir": "IR-LT",
  "suspended": "suspended",
  "personal": "personal",
  "out indefinitely": "out",
  "out for season": "IR-LT",
};
