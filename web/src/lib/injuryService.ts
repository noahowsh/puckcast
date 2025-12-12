// Injury Service - ESPN Scraping & Injury Management
// Handles injury data ingestion and tracking

import type {
  PlayerInjury,
  TeamInjuryReport,
  LeagueInjuryReport,
  InjuryChange,
  InjuryStatus,
  InjuryType,
  ESPNInjuryResponse,
  ESPN_TEAM_MAP,
  ESPN_STATUS_MAP,
} from "@/types/lineup";

// =============================================================================
// Configuration
// =============================================================================

const ESPN_INJURIES_URL = "https://www.espn.com/nhl/injuries";
const CACHE_TTL = 30 * 60 * 1000; // 30 minutes

// In-memory cache for injury data
let cachedInjuryReport: LeagueInjuryReport | null = null;
let lastFetchTime = 0;

// =============================================================================
// ESPN Injury Scraping
// =============================================================================

/**
 * Fetches and parses the ESPN NHL injuries page.
 * Note: In production, this would use a server-side scraping service.
 * For now, we'll create a structure that can be populated by external scripts.
 */
export async function fetchESPNInjuries(): Promise<LeagueInjuryReport | null> {
  // Check cache first
  const now = Date.now();
  if (cachedInjuryReport && now - lastFetchTime < CACHE_TTL) {
    return cachedInjuryReport;
  }

  try {
    // In a real implementation, this would scrape ESPN or use their API
    // For now, we'll try to load from a local data file that gets refreshed
    const report = await loadInjuryDataFromFile();
    if (report) {
      cachedInjuryReport = report;
      lastFetchTime = now;
      return report;
    }

    // Fallback: try web fetch with parsing
    const webReport = await scrapeESPNInjuries();
    if (webReport) {
      cachedInjuryReport = webReport;
      lastFetchTime = now;
      return webReport;
    }

    return null;
  } catch (error) {
    console.error("Failed to fetch ESPN injuries:", error);
    return cachedInjuryReport; // Return stale cache if available
  }
}

/**
 * Load injury data from a pre-scraped JSON file
 */
async function loadInjuryDataFromFile(): Promise<LeagueInjuryReport | null> {
  try {
    // Try to dynamically import the injury data file
    const injuryData = await import("@/data/injuries.json").catch(() => null);
    if (!injuryData) return null;

    return injuryData as LeagueInjuryReport;
  } catch {
    return null;
  }
}

/**
 * Scrape ESPN injuries page directly (for server-side use)
 * This function would be called by a cron job or data refresh script
 */
export async function scrapeESPNInjuries(): Promise<LeagueInjuryReport | null> {
  try {
    // Fetch the ESPN page
    const response = await fetch(ESPN_INJURIES_URL, {
      headers: {
        "User-Agent": "Mozilla/5.0 (compatible; Puckcast/1.0)",
      },
      cache: "no-store",
    });

    if (!response.ok) {
      console.error(`ESPN fetch failed: ${response.status}`);
      return null;
    }

    const html = await response.text();
    return parseESPNInjuriesHTML(html);
  } catch (error) {
    console.error("ESPN scraping error:", error);
    return null;
  }
}

/**
 * Parse the ESPN injuries HTML into our data structure
 */
function parseESPNInjuriesHTML(html: string): LeagueInjuryReport {
  const teams: Record<string, TeamInjuryReport> = {};
  const recentChanges: InjuryChange[] = [];

  // Simple regex-based parsing (would need refinement for production)
  // ESPN structure: team sections with player rows

  // Match team sections
  const teamSectionRegex = /<h2[^>]*>([^<]+)<\/h2>[\s\S]*?<tbody>([\s\S]*?)<\/tbody>/gi;
  let teamMatch;

  while ((teamMatch = teamSectionRegex.exec(html)) !== null) {
    const teamName = teamMatch[1].trim();
    const teamAbbrev = mapTeamNameToAbbrev(teamName);
    if (!teamAbbrev) continue;

    const tableBody = teamMatch[2];
    const injuries: PlayerInjury[] = [];

    // Match player rows
    const playerRowRegex = /<tr[^>]*>[\s\S]*?<td[^>]*>([^<]+)<\/td>[\s\S]*?<td[^>]*>([^<]+)<\/td>[\s\S]*?<td[^>]*>([^<]+)<\/td>[\s\S]*?<td[^>]*>([^<]+)<\/td>/gi;
    let playerMatch;

    while ((playerMatch = playerRowRegex.exec(tableBody)) !== null) {
      const playerName = playerMatch[1].trim();
      const position = playerMatch[2].trim();
      const statusText = playerMatch[3].trim().toLowerCase();
      const injuryDesc = playerMatch[4].trim();

      const status = mapStatusText(statusText);
      const injuryType = parseInjuryType(injuryDesc);

      injuries.push({
        playerId: generatePlayerId(playerName, teamAbbrev),
        playerName,
        teamAbbrev,
        position: normalizePosition(position),
        status,
        injuryType,
        injuryDescription: injuryDesc,
        dateInjured: null, // Would need additional parsing
        expectedReturn: parseExpectedReturn(injuryDesc),
        lastUpdated: new Date().toISOString(),
        isOut: isPlayerOutFromStatus(status),
      });
    }

    const forwardsOut = injuries.filter(i => i.isOut && isForward(i.position)).length;
    const defensemenOut = injuries.filter(i => i.isOut && i.position === "D").length;
    const goaliesOut = injuries.filter(i => i.isOut && i.position === "G").length;

    teams[teamAbbrev] = {
      teamAbbrev,
      teamName,
      injuries,
      totalOut: injuries.filter(i => i.isOut).length,
      forwardsOut,
      defensemenOut,
      goaliesOut,
      impactRating: calculateInjuryImpact(injuries),
      lastUpdated: new Date().toISOString(),
    };
  }

  return {
    updatedAt: new Date().toISOString(),
    source: "ESPN",
    teams,
    totalInjuries: Object.values(teams).reduce((sum, t) => sum + t.injuries.length, 0),
    recentChanges,
  };
}

// =============================================================================
// Helper Functions
// =============================================================================

function mapTeamNameToAbbrev(name: string): string | null {
  // Direct mapping
  const directMap: Record<string, string> = {
    "Anaheim Ducks": "ANA",
    "Arizona Coyotes": "ARI",
    "Boston Bruins": "BOS",
    "Buffalo Sabres": "BUF",
    "Calgary Flames": "CGY",
    "Carolina Hurricanes": "CAR",
    "Chicago Blackhawks": "CHI",
    "Colorado Avalanche": "COL",
    "Columbus Blue Jackets": "CBJ",
    "Dallas Stars": "DAL",
    "Detroit Red Wings": "DET",
    "Edmonton Oilers": "EDM",
    "Florida Panthers": "FLA",
    "Los Angeles Kings": "LAK",
    "Minnesota Wild": "MIN",
    "Montreal Canadiens": "MTL",
    "Nashville Predators": "NSH",
    "New Jersey Devils": "NJD",
    "New York Islanders": "NYI",
    "New York Rangers": "NYR",
    "Ottawa Senators": "OTT",
    "Philadelphia Flyers": "PHI",
    "Pittsburgh Penguins": "PIT",
    "San Jose Sharks": "SJS",
    "Seattle Kraken": "SEA",
    "St. Louis Blues": "STL",
    "Tampa Bay Lightning": "TBL",
    "Toronto Maple Leafs": "TOR",
    "Utah Hockey Club": "UTA",
    "Vancouver Canucks": "VAN",
    "Vegas Golden Knights": "VGK",
    "Washington Capitals": "WSH",
    "Winnipeg Jets": "WPG",
  };

  if (directMap[name]) return directMap[name];

  // Try partial matching
  const lowerName = name.toLowerCase();
  for (const [key, value] of Object.entries(directMap)) {
    if (lowerName.includes(key.toLowerCase().split(" ")[0])) {
      return value;
    }
  }

  return null;
}

function mapStatusText(text: string): InjuryStatus {
  const lower = text.toLowerCase();

  if (lower.includes("day-to-day") || lower.includes("dtd")) return "day-to-day";
  if (lower.includes("long-term") || lower.includes("ltir") || lower.includes("ir-lt")) return "IR-LT";
  if (lower.includes("injured reserve") || lower === "ir") return "IR";
  if (lower.includes("suspended")) return "suspended";
  if (lower.includes("personal")) return "personal";
  if (lower.includes("out")) return "out";

  return "out"; // Default for unknown statuses
}

function parseInjuryType(desc: string): InjuryType {
  const lower = desc.toLowerCase();

  if (lower.includes("upper body") || lower.includes("upper-body")) return "upper-body";
  if (lower.includes("lower body") || lower.includes("lower-body")) return "lower-body";
  if (lower.includes("concussion")) return "concussion";
  if (lower.includes("head")) return "head";
  if (lower.includes("knee")) return "knee";
  if (lower.includes("ankle")) return "ankle";
  if (lower.includes("shoulder")) return "shoulder";
  if (lower.includes("back")) return "back";
  if (lower.includes("hand")) return "hand";
  if (lower.includes("wrist")) return "wrist";
  if (lower.includes("groin")) return "groin";
  if (lower.includes("hip")) return "hip";
  if (lower.includes("foot")) return "foot";
  if (lower.includes("illness") || lower.includes("flu") || lower.includes("sick")) return "illness";
  if (lower.includes("undisclosed")) return "undisclosed";

  return "other";
}

function parseExpectedReturn(desc: string): string | null {
  // Look for date patterns or timeframes
  const dateMatch = desc.match(/(\d{1,2}\/\d{1,2})/);
  if (dateMatch) {
    const [month, day] = dateMatch[1].split("/");
    const year = new Date().getFullYear();
    return `${year}-${month.padStart(2, "0")}-${day.padStart(2, "0")}`;
  }

  // Look for "X weeks" or "X days"
  const weeksMatch = desc.match(/(\d+)\s*weeks?/i);
  if (weeksMatch) {
    const weeks = parseInt(weeksMatch[1], 10);
    const returnDate = new Date();
    returnDate.setDate(returnDate.getDate() + weeks * 7);
    return returnDate.toISOString().split("T")[0];
  }

  const daysMatch = desc.match(/(\d+)\s*days?/i);
  if (daysMatch) {
    const days = parseInt(daysMatch[1], 10);
    const returnDate = new Date();
    returnDate.setDate(returnDate.getDate() + days);
    return returnDate.toISOString().split("T")[0];
  }

  return null;
}

function normalizePosition(pos: string): string {
  const upper = pos.toUpperCase();
  if (upper === "LW" || upper === "RW" || upper === "W" || upper === "F") return "L"; // Forward
  if (upper === "C" || upper === "L" || upper === "R" || upper === "D" || upper === "G") return upper;
  return "L"; // Default to forward
}

function isForward(position: string): boolean {
  return ["C", "L", "R", "LW", "RW", "W", "F"].includes(position.toUpperCase());
}

function isPlayerOutFromStatus(status: InjuryStatus): boolean {
  return status !== "healthy" && status !== "day-to-day";
}

function generatePlayerId(name: string, team: string): number {
  // Generate a deterministic ID from name and team
  // In production, we'd match against actual NHL player IDs
  let hash = 0;
  const str = `${name}${team}`;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return Math.abs(hash);
}

function calculateInjuryImpact(injuries: PlayerInjury[]): number {
  // Calculate impact based on number and positions of injured players
  let impact = 0;

  for (const injury of injuries) {
    if (!injury.isOut) continue;

    // Base impact by position
    if (injury.position === "G") impact += 25;
    else if (injury.position === "D") impact += 15;
    else impact += 10;

    // Adjust by status severity
    if (injury.status === "IR-LT") impact += 5;
    else if (injury.status === "IR") impact += 3;
  }

  return Math.min(100, impact);
}

// =============================================================================
// Public API Functions
// =============================================================================

/**
 * Get injury report for a specific team
 */
export async function getTeamInjuries(teamAbbrev: string): Promise<TeamInjuryReport | null> {
  const report = await fetchESPNInjuries();
  return report?.teams[teamAbbrev] || null;
}

/**
 * Get all injured players across the league
 */
export async function getAllInjuries(): Promise<LeagueInjuryReport | null> {
  return fetchESPNInjuries();
}

/**
 * Check if a specific player is injured
 */
export async function isPlayerInjured(playerName: string, teamAbbrev: string): Promise<PlayerInjury | null> {
  const report = await fetchESPNInjuries();
  if (!report) return null;

  const teamReport = report.teams[teamAbbrev];
  if (!teamReport) return null;

  const lowerName = playerName.toLowerCase();
  return teamReport.injuries.find(
    i => i.playerName.toLowerCase().includes(lowerName) || lowerName.includes(i.playerName.toLowerCase())
  ) || null;
}

/**
 * Get list of healthy players for a team (filters out injured)
 */
export async function getHealthyRoster(teamAbbrev: string, allPlayers: { name: string; position: string }[]): Promise<typeof allPlayers> {
  const injuries = await getTeamInjuries(teamAbbrev);
  if (!injuries) return allPlayers;

  const injuredNames = new Set(
    injuries.injuries
      .filter(i => i.isOut)
      .map(i => i.playerName.toLowerCase())
  );

  return allPlayers.filter(p => !injuredNames.has(p.name.toLowerCase()));
}

/**
 * Detect injury changes since last check
 */
export async function detectInjuryChanges(previousReport: LeagueInjuryReport | null): Promise<InjuryChange[]> {
  const currentReport = await fetchESPNInjuries();
  if (!currentReport || !previousReport) return [];

  const changes: InjuryChange[] = [];

  for (const [teamAbbrev, currentTeam] of Object.entries(currentReport.teams)) {
    const previousTeam = previousReport.teams[teamAbbrev];
    if (!previousTeam) continue;

    // Create maps for quick lookup
    const previousMap = new Map(previousTeam.injuries.map(i => [i.playerName.toLowerCase(), i]));
    const currentMap = new Map(currentTeam.injuries.map(i => [i.playerName.toLowerCase(), i]));

    // Check for new injuries
    for (const [name, injury] of currentMap) {
      const previous = previousMap.get(name);
      if (!previous) {
        // New injury
        changes.push({
          playerId: injury.playerId,
          playerName: injury.playerName,
          teamAbbrev,
          changeType: "injured",
          previousStatus: "healthy",
          newStatus: injury.status,
          timestamp: new Date().toISOString(),
        });
      } else if (previous.status !== injury.status) {
        // Status change
        changes.push({
          playerId: injury.playerId,
          playerName: injury.playerName,
          teamAbbrev,
          changeType: "status_change",
          previousStatus: previous.status,
          newStatus: injury.status,
          timestamp: new Date().toISOString(),
        });
      }
    }

    // Check for returns (was injured, now not in injury list)
    for (const [name, injury] of previousMap) {
      if (!currentMap.has(name)) {
        changes.push({
          playerId: injury.playerId,
          playerName: injury.playerName,
          teamAbbrev,
          changeType: "returned",
          previousStatus: injury.status,
          newStatus: "healthy",
          timestamp: new Date().toISOString(),
        });
      }
    }
  }

  return changes;
}

// =============================================================================
// Export for data refresh scripts
// =============================================================================

export { parseESPNInjuriesHTML };
