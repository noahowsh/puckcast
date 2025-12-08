// Starting Goalie Service
// Aggregates multiple sources for starting goalie detection

import type {
  StartingGoalieInfo,
  GameGoalieReport,
  DailyGoalieReport,
  GoalieSource,
  GoaliePulseEntry,
  ConfidenceLevel,
} from "@/types/startingGoalie";
import {
  getConfidenceLevel,
  getGoalieStatus,
  combineConfidence,
  getSourceWeight,
} from "@/types/startingGoalie";

// =============================================================================
// Data Loading
// =============================================================================

let cachedGoaliePulse: GoaliePulseEntry[] | null = null;
let cachedStartingGoalies: StartingGoaliesPayload | null = null;

type StartingGoaliesPayload = {
  generatedAt: string;
  date: string;
  games: {
    gameId: string;
    homeTeam: string;
    awayTeam: string;
    homeGoalie: string | null;
    awayGoalie: string | null;
    source: string;
    confidence: number;
  }[];
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
// Daily Faceoff Integration
// =============================================================================

const DAILY_FACEOFF_URL = "https://www.dailyfaceoff.com/starting-goalies/";

/**
 * Fetch and parse Daily Faceoff starting goalies
 * This provides earlier confirmation than NHL API
 */
export async function fetchDailyFaceoffStarters(): Promise<Map<string, { goalie: string; status: string }>> {
  const starters = new Map<string, { goalie: string; status: string }>();

  try {
    // In production, this would fetch and parse Daily Faceoff
    // For now, we'll use the pattern-based approach
    // Daily Faceoff structure: Team abbreviation -> Goalie name + status

    const response = await fetch(DAILY_FACEOFF_URL, {
      headers: {
        "User-Agent": "Mozilla/5.0 (compatible; Puckcast/1.0)",
      },
      cache: "no-store",
    });

    if (!response.ok) {
      console.warn(`Daily Faceoff fetch failed: ${response.status}`);
      return starters;
    }

    const html = await response.text();
    return parseDailyFaceoffHTML(html);
  } catch (error) {
    console.warn("Daily Faceoff fetch error:", error);
    return starters;
  }
}

/**
 * Parse Daily Faceoff HTML to extract starters
 */
function parseDailyFaceoffHTML(html: string): Map<string, { goalie: string; status: string }> {
  const starters = new Map<string, { goalie: string; status: string }>();

  // Daily Faceoff uses specific CSS classes for status:
  // - "confirmed" (green checkmark)
  // - "expected" (likely to start)
  // - "probable"
  // - "unconfirmed"

  // Match team and goalie sections
  // Pattern varies by site structure - this is a simplified approach
  const teamRegex = /data-team="([A-Z]{3})"[^>]*>[\s\S]*?class="goalie-name"[^>]*>([^<]+)<[\s\S]*?class="status-([^"]+)"/gi;
  let match;

  while ((match = teamRegex.exec(html)) !== null) {
    const team = match[1];
    const goalieName = match[2].trim();
    const status = match[3].toLowerCase();

    starters.set(team, { goalie: goalieName, status });
  }

  // Fallback: simpler parsing if structured differently
  if (starters.size === 0) {
    // Try alternative parsing patterns
    const altRegex = /<div[^>]*class="[^"]*team-([A-Z]{3})[^"]*"[^>]*>[\s\S]*?<span[^>]*class="[^"]*goalie[^"]*"[^>]*>([^<]+)<[\s\S]*?<span[^>]*class="[^"]*status[^"]*"[^>]*>([^<]+)</gi;
    while ((match = altRegex.exec(html)) !== null) {
      const team = match[1];
      const goalieName = match[2].trim();
      const statusText = match[3].trim().toLowerCase();

      const status = statusText.includes("confirmed") ? "confirmed"
        : statusText.includes("expected") ? "expected"
        : statusText.includes("probable") ? "probable"
        : "unconfirmed";

      starters.set(team, { goalie: goalieName, status });
    }
  }

  return starters;
}

// =============================================================================
// Goalie Info Building
// =============================================================================

/**
 * Build comprehensive goalie info from multiple sources
 */
function buildGoalieInfo(
  teamAbbrev: string,
  goalieName: string | null,
  pulseData: GoaliePulseEntry[],
  startingData: { source: string; confidence: number } | null,
  dailyFaceoffData: { goalie: string; status: string } | undefined
): StartingGoalieInfo {
  // Find in goalie pulse
  const pulseEntry = pulseData.find(
    g => g.team === teamAbbrev && (
      goalieName
        ? g.name.toLowerCase().includes(goalieName.toLowerCase().split(" ").pop() || "")
        : g.startLikelihood > 0.7
    )
  );

  // Determine best goalie name
  const resolvedName = goalieName
    || dailyFaceoffData?.goalie
    || pulseEntry?.name
    || null;

  // Aggregate confidence from multiple sources
  const sources: { source: GoalieSource; confidence: number }[] = [];

  if (startingData && goalieName) {
    sources.push({
      source: startingData.source as GoalieSource,
      confidence: startingData.confidence,
    });
  }

  if (dailyFaceoffData) {
    const dfConfidence = dailyFaceoffData.status === "confirmed" ? 0.95
      : dailyFaceoffData.status === "expected" ? 0.8
      : dailyFaceoffData.status === "probable" ? 0.6
      : 0.4;
    sources.push({ source: "daily_faceoff", confidence: dfConfidence });
  }

  if (pulseEntry) {
    sources.push({
      source: "goalie_pulse",
      confidence: pulseEntry.startLikelihood,
    });
  }

  const combinedConfidence = sources.length > 0 ? combineConfidence(sources) : 0;
  const isNHLConfirmed = startingData?.source === "nhl_api" && startingData.confidence >= 0.95;

  // Determine primary and alternate sources
  const primarySource = sources.sort((a, b) => getSourceWeight(b.source) - getSourceWeight(a.source))[0]?.source || "pattern";
  const alternateSource = sources[1]?.source || null;

  return {
    playerId: null, // Would need lookup
    playerName: resolvedName,
    teamAbbrev,
    status: getGoalieStatus(combinedConfidence, isNHLConfirmed),
    confidence: combinedConfidence,
    confidenceLevel: getConfidenceLevel(combinedConfidence),
    source: primarySource,
    alternateSource,
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
    confirmedAt: isNHLConfirmed ? new Date().toISOString() : null,
    updatedAt: new Date().toISOString(),
  };
}

// =============================================================================
// Main Service Functions
// =============================================================================

/**
 * Get starting goalie report for a specific game
 */
export async function getGameGoalieReport(gameId: string): Promise<GameGoalieReport | null> {
  const [startingData, pulseData] = await Promise.all([
    loadStartingGoalies(),
    loadGoaliePulse(),
  ]);

  const gameData = startingData?.games.find(g => g.gameId === gameId);
  if (!gameData) return null;

  // Try to get Daily Faceoff data
  let dailyFaceoffData: Map<string, { goalie: string; status: string }>;
  try {
    dailyFaceoffData = await fetchDailyFaceoffStarters();
  } catch {
    dailyFaceoffData = new Map();
  }

  const homeGoalie = buildGoalieInfo(
    gameData.homeTeam,
    gameData.homeGoalie,
    pulseData,
    { source: gameData.source, confidence: gameData.confidence },
    dailyFaceoffData.get(gameData.homeTeam)
  );

  const awayGoalie = buildGoalieInfo(
    gameData.awayTeam,
    gameData.awayGoalie,
    pulseData,
    { source: gameData.source, confidence: gameData.confidence },
    dailyFaceoffData.get(gameData.awayTeam)
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
 */
export async function getDailyGoalieReport(date?: string): Promise<DailyGoalieReport> {
  const targetDate = date || new Date().toISOString().split("T")[0];

  const [startingData, pulseData] = await Promise.all([
    loadStartingGoalies(),
    loadGoaliePulse(),
  ]);

  // Try Daily Faceoff
  let dailyFaceoffData: Map<string, { goalie: string; status: string }>;
  try {
    dailyFaceoffData = await fetchDailyFaceoffStarters();
  } catch {
    dailyFaceoffData = new Map();
  }

  const games: GameGoalieReport[] = [];

  for (const gameData of startingData?.games || []) {
    const homeGoalie = buildGoalieInfo(
      gameData.homeTeam,
      gameData.homeGoalie,
      pulseData,
      { source: gameData.source, confidence: gameData.confidence },
      dailyFaceoffData.get(gameData.homeTeam)
    );

    const awayGoalie = buildGoalieInfo(
      gameData.awayTeam,
      gameData.awayGoalie,
      pulseData,
      { source: gameData.source, confidence: gameData.confidence },
      dailyFaceoffData.get(gameData.awayTeam)
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

  return {
    date: targetDate,
    updatedAt: new Date().toISOString(),
    games,
    confirmedCount,
    likelyCount,
    uncertainCount,
    lastNHLCheck: startingData?.generatedAt || null,
    lastDailyFaceoffCheck: dailyFaceoffData.size > 0 ? new Date().toISOString() : null,
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
