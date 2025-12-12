// Starting Goalie Types
// Comprehensive types for multi-source starting goalie detection

// =============================================================================
// Source Types
// =============================================================================

export type GoalieSource =
  | "nhl_api"        // Official NHL API confirmation (highest confidence)
  | "daily_faceoff"  // Daily Faceoff predictions/confirmations
  | "goalie_pulse"   // Our internal prediction model
  | "pattern"        // Historical pattern analysis
  | "user_report";   // Manual/user-submitted info

export type ConfidenceLevel =
  | "confirmed"      // Officially confirmed (1.0)
  | "likely"         // High confidence (0.75-0.99)
  | "probable"       // Medium-high confidence (0.5-0.74)
  | "projected"      // Statistical projection (0.25-0.49)
  | "uncertain";     // Low confidence (<0.25)

export type GoalieStatus =
  | "confirmed_starter"
  | "expected_starter"
  | "projected_starter"
  | "backup"
  | "injured"
  | "unknown";

// =============================================================================
// Core Goalie Types
// =============================================================================

export type StartingGoalieInfo = {
  playerId: number | null;
  playerName: string | null;
  teamAbbrev: string;
  status: GoalieStatus;
  confidence: number;           // 0-1 scale
  confidenceLevel: ConfidenceLevel;
  source: GoalieSource;
  alternateSource: GoalieSource | null;
  // Performance metrics
  seasonRecord: string | null;  // "12-5-2"
  seasonGAA: number | null;
  seasonSavePct: number | null;
  last5GAA: number | null;
  last5SavePct: number | null;
  gsaRolling: number | null;    // Goals Saved Above Expected
  // Recent usage
  restDays: number | null;
  gamesLast7Days: number | null;
  lastStartDate: string | null;
  // Trend analysis
  trend: "surging" | "steady" | "cooling" | "struggling" | "unknown";
  // Timing
  confirmedAt: string | null;   // When was this confirmed
  updatedAt: string;
};

export type GameGoalieReport = {
  gameId: string;
  gameDate: string;
  startTimeEt: string | null;
  homeTeam: string;
  awayTeam: string;
  venue: string | null;
  homeGoalie: StartingGoalieInfo;
  awayGoalie: StartingGoalieInfo;
  // Aggregate confidence
  overallConfidence: number;    // Average of both goalies
  bothConfirmed: boolean;
  // Matchup analysis
  homeGoalieAdvantage: number;  // Positive = home goalie advantage
  significance: "high" | "medium" | "low"; // How much this affects predictions
  // Timing info
  hoursUntilPuck: number | null;
  typicalConfirmTime: string | null; // When starters are usually confirmed
};

export type DailyGoalieReport = {
  date: string;
  updatedAt: string;
  games: GameGoalieReport[];
  // Summary stats
  confirmedCount: number;
  likelyCount: number;
  uncertainCount: number;
  // Data freshness
  lastNHLCheck: string | null;
  lastDailyFaceoffCheck: string | null;
  nextRefresh: string | null;
};

// =============================================================================
// Source-Specific Types
// =============================================================================

export type NHLApiStarterResponse = {
  gameId: string;
  homeGoalie: string | null;
  awayGoalie: string | null;
  homeGoalieId: number | null;
  awayGoalieId: number | null;
  isConfirmed: boolean;
  fetchedAt: string;
};

export type DailyFaceoffEntry = {
  team: string;
  goalieName: string;
  status: "confirmed" | "expected" | "probable" | "unconfirmed";
  opponent: string;
  gameTime: string | null;
  source: string;  // e.g., "Coach confirmed", "Beat reporter"
  updatedAt: string;
};

export type GoaliePulseEntry = {
  name: string;
  team: string;
  rollingGsa: number;
  seasonGsa: number;
  restDays: number;
  startLikelihood: number;
  trend: string;
  nextOpponent: string | null;
  note: string;
};

// =============================================================================
// Pattern Analysis Types
// =============================================================================

export type GoalieUsagePattern = {
  teamAbbrev: string;
  goalieName: string;
  playerId: number;
  // Usage stats
  gamesPlayed: number;
  starts: number;
  startPercentage: number;
  avgRestBetweenStarts: number;
  // Pattern detection
  typicalStartDays: string[];   // ["Monday", "Thursday", "Saturday"]
  backToBackStarter: boolean;
  heavyLoadGoalie: boolean;     // >60% starts
  // Recent pattern
  last10Starts: number;
  startedLastGame: boolean;
  daysRest: number;
};

export type TeamGoalieSituation = {
  teamAbbrev: string;
  teamName: string;
  // Goalies
  primaryGoalie: {
    name: string;
    playerId: number;
    startPercentage: number;
    gaa: number;
    savePct: number;
  } | null;
  backupGoalie: {
    name: string;
    playerId: number;
    startPercentage: number;
    gaa: number;
    savePct: number;
  } | null;
  thirdGoalie: {
    name: string;
    playerId: number;
  } | null;
  // Situation
  situationType: "clear_starter" | "tandem" | "committee" | "injury_situation" | "unknown";
  injuredGoalies: string[];
  notes: string | null;
};

// =============================================================================
// Utility Functions
// =============================================================================

export function getConfidenceLevel(confidence: number): ConfidenceLevel {
  if (confidence >= 1.0) return "confirmed";
  if (confidence >= 0.75) return "likely";
  if (confidence >= 0.5) return "probable";
  if (confidence >= 0.25) return "projected";
  return "uncertain";
}

export function getGoalieStatus(confidence: number, isConfirmed: boolean): GoalieStatus {
  if (isConfirmed) return "confirmed_starter";
  if (confidence >= 0.75) return "expected_starter";
  if (confidence >= 0.4) return "projected_starter";
  return "unknown";
}

export function getSourceWeight(source: GoalieSource): number {
  switch (source) {
    case "nhl_api": return 1.0;
    case "daily_faceoff": return 0.85;
    case "goalie_pulse": return 0.6;
    case "pattern": return 0.4;
    case "user_report": return 0.3;
  }
}

export function combineConfidence(sources: { source: GoalieSource; confidence: number }[]): number {
  if (sources.length === 0) return 0;

  // Weighted average based on source reliability
  let totalWeight = 0;
  let weightedSum = 0;

  for (const s of sources) {
    const weight = getSourceWeight(s.source);
    weightedSum += s.confidence * weight;
    totalWeight += weight;
  }

  return totalWeight > 0 ? weightedSum / totalWeight : 0;
}

export function formatConfidence(confidence: number): string {
  const level = getConfidenceLevel(confidence);
  const pct = Math.round(confidence * 100);

  switch (level) {
    case "confirmed": return "Confirmed";
    case "likely": return `Likely (${pct}%)`;
    case "probable": return `Probable (${pct}%)`;
    case "projected": return `Projected (${pct}%)`;
    case "uncertain": return `Uncertain (${pct}%)`;
  }
}

export function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.9) return "#10b981";  // Green - confirmed
  if (confidence >= 0.7) return "#3b82f6";  // Blue - likely
  if (confidence >= 0.5) return "#f59e0b";  // Amber - probable
  if (confidence >= 0.3) return "#f97316";  // Orange - projected
  return "#ef4444";  // Red - uncertain
}
