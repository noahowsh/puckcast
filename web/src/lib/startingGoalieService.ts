// Starting Goalie Service
// Aggregates multiple sources for starting goalie detection

import type {
  StartingGoalieInfo,
  GameGoalieReport,
  DailyGoalieReport,
  GoalieSource,
  GoaliePulseEntry,
} from "@/types/startingGoalie";
import {
  getConfidenceLevel,
} from "@/types/startingGoalie";

// =============================================================================
// Data Loading
// =============================================================================

let cachedGoaliePulse: GoaliePulseEntry[] | null = null;
let cachedStartingGoalies: StartingGoaliesPayload | null = null;

type GoalieEntry = {
  team: string;
  playerId: number | null;
  goalieName: string | null;
  confirmedStart: boolean;
  statusCode: string;
  statusDescription: string;
  lastUpdated: string;
};

type StartingGoaliesPayload = {
  generatedAt: string;
  source: string;
  date: string;
  teams: Record<string, GoalieEntry>;
  games: {
    gameId: string;
    gameDate: string;
    startTimeUTC: string;
    homeTeam: string;
    awayTeam: string;
    homeGoalie: GoalieEntry;
    awayGoalie: GoalieEntry;
  }[];
};

// Map Daily Faceoff status to confidence
const STATUS_TO_CONFIDENCE: Record<string, number> = {
  confirmed: 0.99,
  expected: 0.85,
  likely: 0.75,
  probable: 0.65,
  unconfirmed: 0.40,
  predicted: 0.60,
  unknown: 0.30,
};

type GoaliePulsePayload = {
  updatedAt: string;
  goalies: GoaliePulseEntry[];
};

/**
 * Load goalie pulse data (performance metrics and predictions)
 */
async function loadGoaliePulse(): Promise<GoaliePulseEntry[]> {
  if (cachedGoaliePulse) return cachedGoaliePulse;

  try {
    const data = await import("@/data/goaliePulse.json") as GoaliePulsePayload;
    cachedGoaliePulse = data.goalies || [];
    return cachedGoaliePulse;
  } catch {
    console.warn("Could not load goaliePulse.json");
    return [];
  }
}

/**
 * Load starting goalies data
 */
async function loadStartingGoalies(): Promise<StartingGoaliesPayload | null> {
  if (cachedStartingGoalies) return cachedStartingGoalies;

  try {
    const data = await import("@/data/startingGoalies.json") as StartingGoaliesPayload;
    cachedStartingGoalies = data;
    return data;
  } catch {
    console.warn("Could not load startingGoalies.json");
    return null;
  }
}

// =============================================================================
// NOTE: Daily Faceoff scraping is handled by the Python scraper
// (src/nhl_prediction/starting_goalie_scraper.py)
// The scraped data is stored in startingGoalies.json with status fields
// =============================================================================

// =============================================================================
// Goalie Info Building
// =============================================================================

/**
 * Build comprehensive goalie info from multiple sources
 *
 * The Python scraper (starting_goalie_scraper.py) handles Daily Faceoff scraping
 * and stores the status in startingGoalies.json. We just need to use that data.
 */
function buildGoalieInfo(
  teamAbbrev: string,
  goalieName: string | null,
  status: string,  // From Daily Faceoff: "confirmed", "expected", "probable", etc.
  pulseData: GoaliePulseEntry[],
  source: string
): StartingGoalieInfo {
  // Find in goalie pulse for additional metrics
  const pulseEntry = pulseData.find(
    g => g.team === teamAbbrev && (
      goalieName
        ? g.name.toLowerCase().includes(goalieName.toLowerCase().split(" ").pop() || "")
        : g.startLikelihood > 0.7
    )
  );

  // Determine best goalie name
  const resolvedName = goalieName || pulseEntry?.name || null;

  // Use status from Daily Faceoff (via Python scraper) to determine confidence
  const statusConfidence = STATUS_TO_CONFIDENCE[status.toLowerCase()] ?? 0.5;

  // Combine with pulse data if available
  let combinedConfidence = statusConfidence;
  if (pulseEntry && source !== "daily_faceoff") {
    // Weight pulse data more if we don't have Daily Faceoff confirmation
    combinedConfidence = (statusConfidence * 0.7) + (pulseEntry.startLikelihood * 0.3);
  }

  // Determine if this is a confirmed starter
  const isConfirmed = status.toLowerCase() === "confirmed" ||
    (source === "nhl_api" && statusConfidence >= 0.95);

  // Map status string to GoalieStatus type
  const goalieStatus = isConfirmed ? "confirmed_starter"
    : status.toLowerCase() === "expected" ? "expected_starter"
    : status.toLowerCase() === "probable" || status.toLowerCase() === "likely" ? "projected_starter"
    : "unknown";

  return {
    playerId: null,
    playerName: resolvedName,
    teamAbbrev,
    status: goalieStatus as StartingGoalieInfo["status"],
    confidence: combinedConfidence,
    confidenceLevel: getConfidenceLevel(combinedConfidence),
    source: source as GoalieSource,
    alternateSource: pulseEntry ? "goalie_pulse" : null,
    // Performance metrics from pulse
    seasonRecord: null,
    seasonGAA: null,
    seasonSavePct: null,
    last5GAA: null,
    last5SavePct: null,
    gsaRolling: pulseEntry?.rollingGsa ?? null,
    // Usage info
    restDays: pulseEntry?.restDays ?? null,
    gamesLast7Days: null,
    lastStartDate: null,
    // Trend
    trend: (pulseEntry?.trend as StartingGoalieInfo["trend"]) ?? "unknown",
    // Timing
    confirmedAt: isConfirmed ? new Date().toISOString() : null,
    updatedAt: new Date().toISOString(),
  };
}

// =============================================================================
// Main Service Functions
// =============================================================================

/**
 * Get starting goalie report for a specific game
 *
 * Uses pre-scraped data from startingGoalies.json (populated by Python scraper
 * which fetches from Daily Faceoff).
 */
export async function getGameGoalieReport(gameId: string): Promise<GameGoalieReport | null> {
  const [startingData, pulseData] = await Promise.all([
    loadStartingGoalies(),
    loadGoaliePulse(),
  ]);

  const gameData = startingData?.games.find(g => g.gameId === gameId);
  if (!gameData) return null;

  // Build goalie info using status from JSON (pre-scraped from Daily Faceoff)
  const homeGoalie = buildGoalieInfo(
    gameData.homeTeam,
    gameData.homeGoalie.goalieName,
    gameData.homeGoalie.statusCode || "unknown",
    pulseData,
    startingData?.source || "nhl_api"
  );

  const awayGoalie = buildGoalieInfo(
    gameData.awayTeam,
    gameData.awayGoalie.goalieName,
    gameData.awayGoalie.statusCode || "unknown",
    pulseData,
    startingData?.source || "nhl_api"
  );

  const overallConfidence = (homeGoalie.confidence + awayGoalie.confidence) / 2;

  // Calculate goalie advantage (positive = home goalie better)
  const homeGSA = homeGoalie.gsaRolling ?? 0;
  const awayGSA = awayGoalie.gsaRolling ?? 0;
  const goalieAdvantage = homeGSA - awayGSA;

  // Determine significance
  const significance = Math.abs(goalieAdvantage) > 2 ? "high"
    : Math.abs(goalieAdvantage) > 1 ? "medium"
    : "low";

  return {
    gameId,
    gameDate: startingData?.date || new Date().toISOString().split("T")[0],
    startTimeEt: null,
    homeTeam: gameData.homeTeam,
    awayTeam: gameData.awayTeam,
    venue: null,
    homeGoalie,
    awayGoalie,
    overallConfidence,
    bothConfirmed: homeGoalie.status === "confirmed_starter" && awayGoalie.status === "confirmed_starter",
    homeGoalieAdvantage: goalieAdvantage,
    significance,
    hoursUntilPuck: null,
    typicalConfirmTime: "10:00 AM ET", // Most starters confirmed by morning skate
  };
}

/**
 * Get daily goalie report for all games
 *
 * Uses pre-scraped data from startingGoalies.json (populated by Python scraper
 * which fetches from Daily Faceoff).
 */
export async function getDailyGoalieReport(date?: string): Promise<DailyGoalieReport> {
  const targetDate = date || new Date().toISOString().split("T")[0];

  const [startingData, pulseData] = await Promise.all([
    loadStartingGoalies(),
    loadGoaliePulse(),
  ]);

  const games: GameGoalieReport[] = [];

  for (const gameData of startingData?.games || []) {
    const homeGoalie = buildGoalieInfo(
      gameData.homeTeam,
      gameData.homeGoalie.goalieName,
      gameData.homeGoalie.statusCode || "unknown",
      pulseData,
      startingData?.source || "nhl_api"
    );

    const awayGoalie = buildGoalieInfo(
      gameData.awayTeam,
      gameData.awayGoalie.goalieName,
      gameData.awayGoalie.statusCode || "unknown",
      pulseData,
      startingData?.source || "nhl_api"
    );

    const overallConfidence = (homeGoalie.confidence + awayGoalie.confidence) / 2;
    const homeGSA = homeGoalie.gsaRolling ?? 0;
    const awayGSA = awayGoalie.gsaRolling ?? 0;
    const goalieAdvantage = homeGSA - awayGSA;

    games.push({
      gameId: gameData.gameId,
      gameDate: startingData?.date || targetDate,
      startTimeEt: null,
      homeTeam: gameData.homeTeam,
      awayTeam: gameData.awayTeam,
      venue: null,
      homeGoalie,
      awayGoalie,
      overallConfidence,
      bothConfirmed: homeGoalie.status === "confirmed_starter" && awayGoalie.status === "confirmed_starter",
      homeGoalieAdvantage: goalieAdvantage,
      significance: Math.abs(goalieAdvantage) > 2 ? "high" : Math.abs(goalieAdvantage) > 1 ? "medium" : "low",
      hoursUntilPuck: null,
      typicalConfirmTime: "10:00 AM ET",
    });
  }

  // Count by confidence level
  const confirmedCount = games.filter(g => g.bothConfirmed).length;
  const likelyCount = games.filter(g => !g.bothConfirmed && g.overallConfidence >= 0.7).length;
  const uncertainCount = games.filter(g => g.overallConfidence < 0.5).length;

  // Check if data source is Daily Faceoff
  const hasDailyFaceoffData = startingData?.source === "daily_faceoff";

  return {
    date: targetDate,
    updatedAt: new Date().toISOString(),
    games,
    confirmedCount,
    likelyCount,
    uncertainCount,
    lastNHLCheck: startingData?.generatedAt || null,
    lastDailyFaceoffCheck: hasDailyFaceoffData ? startingData?.generatedAt || null : null,
    nextRefresh: null,
  };
}

/**
 * Get expected starter for a team
 */
export async function getTeamExpectedStarter(teamAbbrev: string): Promise<StartingGoalieInfo | null> {
  const pulseData = await loadGoaliePulse();

  // Find goalies for this team, sorted by start likelihood
  const teamGoalies = pulseData
    .filter(g => g.team === teamAbbrev)
    .sort((a, b) => b.startLikelihood - a.startLikelihood);

  if (teamGoalies.length === 0) return null;

  const topGoalie = teamGoalies[0];

  return {
    playerId: null,
    playerName: topGoalie.name,
    teamAbbrev,
    status: topGoalie.startLikelihood > 0.8 ? "expected_starter"
      : topGoalie.startLikelihood > 0.5 ? "projected_starter"
      : "unknown",
    confidence: topGoalie.startLikelihood,
    confidenceLevel: getConfidenceLevel(topGoalie.startLikelihood),
    source: "goalie_pulse",
    alternateSource: null,
    seasonRecord: null,
    seasonGAA: null,
    seasonSavePct: null,
    last5GAA: null,
    last5SavePct: null,
    gsaRolling: topGoalie.rollingGsa,
    restDays: topGoalie.restDays,
    gamesLast7Days: null,
    lastStartDate: null,
    trend: topGoalie.trend as StartingGoalieInfo["trend"],
    confirmedAt: null,
    updatedAt: new Date().toISOString(),
  };
}

/**
 * Get all goalies for a team with their status
 */
export async function getTeamGoalies(teamAbbrev: string): Promise<{
  starter: StartingGoalieInfo | null;
  backup: StartingGoalieInfo | null;
  all: StartingGoalieInfo[];
}> {
  const pulseData = await loadGoaliePulse();

  const teamGoalies = pulseData
    .filter(g => g.team === teamAbbrev)
    .sort((a, b) => b.startLikelihood - a.startLikelihood)
    .map(g => ({
      playerId: null,
      playerName: g.name,
      teamAbbrev,
      status: g.startLikelihood > 0.7 ? "expected_starter"
        : g.startLikelihood > 0.4 ? "backup"
        : "unknown" as StartingGoalieInfo["status"],
      confidence: g.startLikelihood,
      confidenceLevel: getConfidenceLevel(g.startLikelihood),
      source: "goalie_pulse" as GoalieSource,
      alternateSource: null,
      seasonRecord: null,
      seasonGAA: null,
      seasonSavePct: null,
      last5GAA: null,
      last5SavePct: null,
      gsaRolling: g.rollingGsa,
      restDays: g.restDays,
      gamesLast7Days: null,
      lastStartDate: null,
      trend: g.trend as StartingGoalieInfo["trend"],
      confirmedAt: null,
      updatedAt: new Date().toISOString(),
    } as StartingGoalieInfo));

  return {
    starter: teamGoalies[0] || null,
    backup: teamGoalies[1] || null,
    all: teamGoalies,
  };
}

// =============================================================================
// Refresh Functions
// =============================================================================

/**
 * Clear cache to force refresh
 */
export function clearGoalieCache(): void {
  cachedGoaliePulse = null;
  cachedStartingGoalies = null;
}

/**
 * Check if goalie data is stale
 */
export async function isGoalieDataStale(): Promise<boolean> {
  const startingData = await loadStartingGoalies();
  if (!startingData) return true;

  const generatedDate = new Date(startingData.generatedAt);
  const now = new Date();
  const hoursSinceGenerated = (now.getTime() - generatedDate.getTime()) / (1000 * 60 * 60);

  // Consider stale if more than 4 hours old
  return hoursSinceGenerated > 4;
}
