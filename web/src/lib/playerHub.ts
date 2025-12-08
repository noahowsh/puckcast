// Player Hub - NHL API Integration for Player & Goalie Statistics
// Fetches and processes player data from NHL APIs
// Uses roster endpoint for team info + stats endpoint for performance data

import type {
  SkaterCard,
  GoalieDetailCard,
  SkaterSeasonStats,
  GoalieSeasonStats,
  PlayerBio,
  NHLApiSkaterStats,
  NHLApiGoalieStats,
  LeagueSkaterLeaders,
  LeagueGoalieLeaders,
  TeamRoster,
  TeamLeaders,
  PlayerPosition,
  PositionType,
} from "@/types/player";

// =============================================================================
// Constants & Configuration
// =============================================================================

const CURRENT_SEASON = "20252026";
const MIN_SKATER_GAMES = 5;
const MIN_GOALIE_GAMES = 3;
const LEADERS_LIMIT = 10;
const ROSTER_CACHE_TTL = 3600; // 1 hour

// NHL API Endpoints
const NHL_STATS_API = "https://api.nhle.com/stats/rest/en";
const NHL_WEB_API = "https://api-web.nhle.com/v1";

// =============================================================================
// In-Memory Cache for Stats (prevents rate limiting during static generation)
// =============================================================================

let skaterStatsCache: Map<number, NHLApiSkaterStats> | null = null;
let goalieStatsCache: Map<number, NHLApiGoalieStats> | null = null;
let skaterStatsCachePromise: Promise<Map<number, NHLApiSkaterStats>> | null = null;
let goalieStatsCachePromise: Promise<Map<number, NHLApiGoalieStats>> | null = null;

// Realtime stats cache (hits, blocks, etc.)
let realtimeStatsCache: Map<number, { hits: number; blockedShots: number }> | null = null;
let realtimeStatsCachePromise: Promise<Map<number, { hits: number; blockedShots: number }>> | null = null;

// Roster cache by team
const rosterCache: Map<string, NHLRosterResponse> = new Map();
const rosterCachePromise: Map<string, Promise<NHLRosterResponse | null>> = new Map();

// Player-to-team lookup cache (built from all rosters)
let playerTeamLookup: Map<number, { teamAbbrev: string; headshot: string }> | null = null;
let playerTeamLookupPromise: Promise<Map<number, { teamAbbrev: string; headshot: string }>> | null = null;

// All NHL teams for building player lookup
const NHL_TEAMS = [
  "ANA", "ARI", "BOS", "BUF", "CAR", "CBJ", "CGY", "CHI", "COL", "DAL",
  "DET", "EDM", "FLA", "LAK", "MIN", "MTL", "NJD", "NSH", "NYI", "NYR",
  "OTT", "PHI", "PIT", "SEA", "SJS", "STL", "TBL", "TOR", "UTA", "VAN",
  "VGK", "WPG", "WSH"
];

// =============================================================================
// Type Definitions for NHL Web API
// =============================================================================

interface NHLRosterPlayer {
  id: number;
  headshot: string;
  firstName: { default: string };
  lastName: { default: string };
  sweaterNumber: number;
  positionCode: string;
  shootsCatches: string;
  heightInInches: number;
  weightInPounds: number;
  birthDate: string;
  birthCity: { default: string };
  birthCountry: string;
}

interface NHLRosterResponse {
  forwards: NHLRosterPlayer[];
  defensemen: NHLRosterPlayer[];
  goalies: NHLRosterPlayer[];
}

// =============================================================================
// API Fetching Functions
// =============================================================================

async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Track if we've been rate limited to add delays on subsequent requests
let lastRateLimitTime = 0;

async function fetchWithRetry<T>(url: string, options: RequestInit = {}, retries = 8): Promise<T | null> {
  // If we were rate limited recently, add initial delay
  const timeSinceRateLimit = Date.now() - lastRateLimitTime;
  if (lastRateLimitTime > 0 && timeSinceRateLimit < 30000) {
    const initialDelay = Math.max(3000 - timeSinceRateLimit, 500);
    await sleep(initialDelay);
  }

  for (let i = 0; i < retries; i++) {
    try {
      const res = await fetch(url, {
        ...options,
        next: { revalidate: ROSTER_CACHE_TTL },
      });

      // Handle redirects (NHL API sometimes returns 307)
      if (res.status === 307) {
        const redirectUrl = res.headers.get('location');
        if (redirectUrl) {
          return fetchWithRetry<T>(redirectUrl, options, retries - i);
        }
      }

      // Handle rate limiting (429) with aggressive exponential backoff
      if (res.status === 429) {
        lastRateLimitTime = Date.now();
        const backoffMs = Math.min(3000 * Math.pow(2, i), 30000); // 3s, 6s, 12s, 24s, 30s max
        console.log(`Rate limited, waiting ${backoffMs}ms before retry ${i + 1}/${retries}`);
        await sleep(backoffMs);
        continue;
      }

      if (!res.ok) {
        console.error(`API request failed: ${url} - ${res.status}`);
        if (i === retries - 1) return null;
        await sleep(1000); // Delay before retry
        continue;
      }
      return (await res.json()) as T;
    } catch (err) {
      console.error(`API request error: ${url}`, err);
      if (i === retries - 1) return null;
      await sleep(1000);
    }
  }
  return null;
}

// =============================================================================
// Roster Fetching (Primary source for team players)
// Uses caching to prevent rate limiting during static generation
// =============================================================================

async function fetchTeamRosterFromAPIInternal(teamAbbrev: string): Promise<NHLRosterResponse | null> {
  const url = `${NHL_WEB_API}/roster/${teamAbbrev}/${CURRENT_SEASON}`;
  return fetchWithRetry<NHLRosterResponse>(url);
}

async function fetchTeamRosterFromAPI(teamAbbrev: string): Promise<NHLRosterResponse | null> {
  // Return from cache if available
  const cached = rosterCache.get(teamAbbrev);
  if (cached) {
    return cached;
  }

  // If fetch is in progress, wait for it
  const existingPromise = rosterCachePromise.get(teamAbbrev);
  if (existingPromise) {
    return existingPromise;
  }

  // Start the fetch and cache the promise
  const promise = fetchTeamRosterFromAPIInternal(teamAbbrev);
  rosterCachePromise.set(teamAbbrev, promise);

  try {
    const result = await promise;
    if (result) {
      rosterCache.set(teamAbbrev, result);
    }
    return result;
  } finally {
    rosterCachePromise.delete(teamAbbrev);
  }
}

// =============================================================================
// Player-to-Team Lookup (built from all rosters for league-wide stats enrichment)
// =============================================================================

async function buildPlayerTeamLookupInternal(): Promise<Map<number, { teamAbbrev: string; headshot: string }>> {
  const lookup = new Map<number, { teamAbbrev: string; headshot: string }>();

  // Fetch all rosters in true parallel - no delays needed for roster API
  console.log(`Building player lookup from ${NHL_TEAMS.length} teams...`);
  const rosterPromises = NHL_TEAMS.map(team => fetchTeamRosterFromAPI(team).catch(() => null));
  const rosters = await Promise.all(rosterPromises);

  rosters.forEach((roster, idx) => {
    if (!roster) return;
    const teamAbbrev = NHL_TEAMS[idx];
    [...roster.forwards, ...roster.defensemen, ...roster.goalies].forEach(player => {
      lookup.set(player.id, {
        teamAbbrev,
        headshot: player.headshot,
      });
    });
  });

  console.log(`Player lookup built with ${lookup.size} players`);
  return lookup;
}

async function getPlayerTeamLookup(): Promise<Map<number, { teamAbbrev: string; headshot: string }>> {
  // Return from cache if available
  if (playerTeamLookup) {
    return playerTeamLookup;
  }

  // If fetch is in progress, wait for it
  if (playerTeamLookupPromise) {
    return playerTeamLookupPromise;
  }

  // Start building the lookup and cache the promise
  playerTeamLookupPromise = buildPlayerTeamLookupInternal();

  try {
    playerTeamLookup = await playerTeamLookupPromise;
    return playerTeamLookup;
  } finally {
    playerTeamLookupPromise = null;
  }
}

// =============================================================================
// Stats Fetching (Secondary source for performance data)
// Uses in-memory caching to prevent rate limiting during static generation
// =============================================================================

async function fetchAllSkaterStatsMapInternal(): Promise<Map<number, NHLApiSkaterStats>> {
  const url = `${NHL_STATS_API}/skater/summary?isAggregate=true&isGame=false&limit=-1&cayenneExp=seasonId=${CURRENT_SEASON}`;
  const data = await fetchWithRetry<{ data: NHLApiSkaterStats[] }>(url);

  const map = new Map<number, NHLApiSkaterStats>();
  if (data?.data) {
    data.data.forEach(p => map.set(p.playerId, p));
  }
  return map;
}

async function fetchAllGoalieStatsMapInternal(): Promise<Map<number, NHLApiGoalieStats>> {
  const url = `${NHL_STATS_API}/goalie/summary?isAggregate=true&isGame=false&limit=-1&cayenneExp=seasonId=${CURRENT_SEASON}`;
  const data = await fetchWithRetry<{ data: NHLApiGoalieStats[] }>(url);

  const map = new Map<number, NHLApiGoalieStats>();
  if (data?.data) {
    data.data.forEach(g => map.set(g.playerId, g));
  }
  return map;
}

// Cached versions - ensures only one API call even with concurrent requests
async function fetchAllSkaterStatsMap(): Promise<Map<number, NHLApiSkaterStats>> {
  // Return from cache if available
  if (skaterStatsCache) {
    return skaterStatsCache;
  }

  // If fetch is in progress, wait for it
  if (skaterStatsCachePromise) {
    return skaterStatsCachePromise;
  }

  // Start the fetch and cache the promise
  skaterStatsCachePromise = fetchAllSkaterStatsMapInternal();

  try {
    skaterStatsCache = await skaterStatsCachePromise;
    return skaterStatsCache;
  } finally {
    // Clear the promise (but keep the cache)
    skaterStatsCachePromise = null;
  }
}

async function fetchAllGoalieStatsMap(): Promise<Map<number, NHLApiGoalieStats>> {
  // Return from cache if available
  if (goalieStatsCache) {
    return goalieStatsCache;
  }

  // If fetch is in progress, wait for it
  if (goalieStatsCachePromise) {
    return goalieStatsCachePromise;
  }

  // Start the fetch and cache the promise
  goalieStatsCachePromise = fetchAllGoalieStatsMapInternal();

  try {
    goalieStatsCache = await goalieStatsCachePromise;
    return goalieStatsCache;
  } finally {
    // Clear the promise (but keep the cache)
    goalieStatsCachePromise = null;
  }
}

// =============================================================================
// Team-Specific Functions (NEW APPROACH)
// =============================================================================

export async function fetchTeamRoster(teamAbbrev: string): Promise<TeamRoster> {
  // Fetch roster and stats in parallel
  const [roster, skaterStatsMap, goalieStatsMap] = await Promise.all([
    fetchTeamRosterFromAPI(teamAbbrev),
    fetchAllSkaterStatsMap(),
    fetchAllGoalieStatsMap(),
  ]);

  if (!roster) {
    console.error(`Failed to fetch roster for ${teamAbbrev}`);
    return {
      teamAbbrev,
      teamName: teamAbbrev,
      forwards: [],
      defensemen: [],
      goalies: [],
    };
  }

  // Convert forwards
  const forwards: SkaterCard[] = roster.forwards
    .map(player => mergeRosterWithStats(player, skaterStatsMap.get(player.id), teamAbbrev))
    .filter((p): p is SkaterCard => p !== null)
    .sort((a, b) => b.stats.points - a.stats.points);

  // Convert defensemen
  const defensemen: SkaterCard[] = roster.defensemen
    .map(player => mergeRosterWithStats(player, skaterStatsMap.get(player.id), teamAbbrev))
    .filter((p): p is SkaterCard => p !== null)
    .sort((a, b) => b.stats.points - a.stats.points);

  // Convert goalies
  const goalies: GoalieDetailCard[] = roster.goalies
    .map(player => mergeGoalieRosterWithStats(player, goalieStatsMap.get(player.id), teamAbbrev))
    .filter((g): g is GoalieDetailCard => g !== null)
    .sort((a, b) => b.stats.wins - a.stats.wins);

  return {
    teamAbbrev,
    teamName: teamAbbrev, // Could be enhanced to get full team name
    forwards,
    defensemen,
    goalies,
  };
}

function mergeRosterWithStats(
  rosterPlayer: NHLRosterPlayer,
  statsData: NHLApiSkaterStats | undefined,
  teamAbbrev: string
): SkaterCard | null {
  const position = rosterPlayer.positionCode as PlayerPosition;
  const positionType = getPositionType(position);
  const fullName = `${rosterPlayer.firstName.default} ${rosterPlayer.lastName.default}`;

  const bio: PlayerBio = {
    playerId: rosterPlayer.id,
    firstName: rosterPlayer.firstName.default,
    lastName: rosterPlayer.lastName.default,
    fullName,
    teamAbbrev,
    teamName: teamAbbrev,
    position,
    positionType,
    jerseyNumber: rosterPlayer.sweaterNumber,
    shootsCatches: (rosterPlayer.shootsCatches === "L" ? "L" : "R") as "L" | "R",
    heightInInches: rosterPlayer.heightInInches,
    weightInPounds: rosterPlayer.weightInPounds,
    birthDate: rosterPlayer.birthDate,
    birthCity: rosterPlayer.birthCity?.default || null,
    birthCountry: rosterPlayer.birthCountry,
    nationality: rosterPlayer.birthCountry,
    isActive: true,
    isRookie: false,
    headshot: rosterPlayer.headshot,
  };

  // Use stats data if available, otherwise create empty stats
  const stats: SkaterSeasonStats = statsData ? {
    playerId: rosterPlayer.id,
    season: CURRENT_SEASON,
    teamAbbrev,
    gamesPlayed: statsData.gamesPlayed,
    goals: statsData.goals,
    assists: statsData.assists,
    points: statsData.points,
    plusMinus: statsData.plusMinus,
    penaltyMinutes: statsData.penaltyMinutes,
    powerPlayGoals: statsData.ppGoals,
    powerPlayPoints: statsData.ppPoints,
    shorthandedGoals: statsData.shGoals,
    shorthandedPoints: statsData.shPoints,
    gameWinningGoals: statsData.gameWinningGoals,
    overtimeGoals: statsData.otGoals,
    shots: statsData.shots,
    shootingPct: statsData.shootingPct || 0,
    timeOnIcePerGame: formatSecondsToTime(statsData.timeOnIcePerGame),
    faceoffWinPct: statsData.faceoffWinPct || 0,
    blockedShots: 0,
    hits: 0,
    takeaways: 0,
    giveaways: 0,
  } : {
    playerId: rosterPlayer.id,
    season: CURRENT_SEASON,
    teamAbbrev,
    gamesPlayed: 0,
    goals: 0,
    assists: 0,
    points: 0,
    plusMinus: 0,
    penaltyMinutes: 0,
    powerPlayGoals: 0,
    powerPlayPoints: 0,
    shorthandedGoals: 0,
    shorthandedPoints: 0,
    gameWinningGoals: 0,
    overtimeGoals: 0,
    shots: 0,
    shootingPct: 0,
    timeOnIcePerGame: "0:00",
    faceoffWinPct: 0,
    blockedShots: 0,
    hits: 0,
    takeaways: 0,
    giveaways: 0,
  };

  return { bio, stats };
}

function mergeGoalieRosterWithStats(
  rosterPlayer: NHLRosterPlayer,
  statsData: NHLApiGoalieStats | undefined,
  teamAbbrev: string
): GoalieDetailCard | null {
  const fullName = `${rosterPlayer.firstName.default} ${rosterPlayer.lastName.default}`;

  const bio: PlayerBio = {
    playerId: rosterPlayer.id,
    firstName: rosterPlayer.firstName.default,
    lastName: rosterPlayer.lastName.default,
    fullName,
    teamAbbrev,
    teamName: teamAbbrev,
    position: "G",
    positionType: "goalie",
    jerseyNumber: rosterPlayer.sweaterNumber,
    shootsCatches: (rosterPlayer.shootsCatches === "R" ? "R" : "L") as "L" | "R",
    heightInInches: rosterPlayer.heightInInches,
    weightInPounds: rosterPlayer.weightInPounds,
    birthDate: rosterPlayer.birthDate,
    birthCity: rosterPlayer.birthCity?.default || null,
    birthCountry: rosterPlayer.birthCountry,
    nationality: rosterPlayer.birthCountry,
    isActive: true,
    isRookie: false,
    headshot: rosterPlayer.headshot,
  };

  // Use stats data if available, otherwise create empty stats
  const stats: GoalieSeasonStats = statsData ? {
    playerId: rosterPlayer.id,
    season: CURRENT_SEASON,
    teamAbbrev,
    gamesPlayed: statsData.gamesPlayed,
    gamesStarted: statsData.gamesStarted,
    wins: statsData.wins,
    losses: statsData.losses,
    otLosses: statsData.otLosses,
    shotsAgainst: statsData.shotsAgainst,
    goalsAgainst: statsData.goalsAgainst,
    saves: statsData.saves,
    savePct: statsData.savePct,
    goalsAgainstAverage: statsData.goalsAgainstAverage,
    shutouts: statsData.shutouts,
    timeOnIce: formatSecondsToTime(statsData.timeOnIce),
    qualityStarts: null,
    qualityStartsPct: null,
  } : {
    playerId: rosterPlayer.id,
    season: CURRENT_SEASON,
    teamAbbrev,
    gamesPlayed: 0,
    gamesStarted: 0,
    wins: 0,
    losses: 0,
    otLosses: 0,
    shotsAgainst: 0,
    goalsAgainst: 0,
    saves: 0,
    savePct: 0,
    goalsAgainstAverage: 0,
    shutouts: 0,
    timeOnIce: "0:00",
    qualityStarts: null,
    qualityStartsPct: null,
  };

  return { bio, stats };
}

// =============================================================================
// League-Wide Stats Functions (for leaders, search, etc.)
// Uses cached maps to prevent rate limiting during static generation
// =============================================================================

export async function fetchSkaterStats(minGames = MIN_SKATER_GAMES): Promise<SkaterCard[]> {
  // Fetch stats and team lookup in parallel
  const [statsMap, teamLookup] = await Promise.all([
    fetchAllSkaterStatsMap(),
    getPlayerTeamLookup(),
  ]);

  console.log(`Skater stats: ${statsMap.size} players, Team lookup: ${teamLookup.size} players`);

  return Array.from(statsMap.values())
    .filter((p) => p.gamesPlayed >= minGames)
    .map((p) => {
      const card = mapNHLSkaterToCard(p);
      // Enrich with team info from roster lookup
      const teamInfo = teamLookup.get(p.playerId);
      if (teamInfo) {
        card.bio.teamAbbrev = teamInfo.teamAbbrev;
        card.bio.teamName = teamInfo.teamAbbrev;
        card.bio.headshot = teamInfo.headshot;
        card.stats.teamAbbrev = teamInfo.teamAbbrev;
      }
      return card;
    })
    .sort((a, b) => b.stats.points - a.stats.points);
}

export async function fetchGoalieStats(minGames = MIN_GOALIE_GAMES): Promise<GoalieDetailCard[]> {
  // Fetch stats and team lookup in parallel
  const [statsMap, teamLookup] = await Promise.all([
    fetchAllGoalieStatsMap(),
    getPlayerTeamLookup(),
  ]);

  console.log(`Goalie stats: ${statsMap.size} goalies, Team lookup: ${teamLookup.size} players`);

  return Array.from(statsMap.values())
    .filter((g) => g.gamesPlayed >= minGames)
    .map((g) => {
      const card = mapNHLGoalieToCard(g);
      // Enrich with team info from roster lookup
      const teamInfo = teamLookup.get(g.playerId);
      if (teamInfo) {
        card.bio.teamAbbrev = teamInfo.teamAbbrev;
        card.bio.teamName = teamInfo.teamAbbrev;
        card.bio.headshot = teamInfo.headshot;
        card.stats.teamAbbrev = teamInfo.teamAbbrev;
      }
      return card;
    })
    .sort((a, b) => b.stats.wins - a.stats.wins);
}

export async function fetchSkaterLeaders(): Promise<LeagueSkaterLeaders> {
  const allSkaters = await fetchSkaterStats(MIN_SKATER_GAMES);

  const now = new Date().toISOString();

  return {
    updatedAt: now,
    season: CURRENT_SEASON,
    points: [...allSkaters].sort((a, b) => b.stats.points - a.stats.points).slice(0, LEADERS_LIMIT),
    goals: [...allSkaters].sort((a, b) => b.stats.goals - a.stats.goals).slice(0, LEADERS_LIMIT),
    assists: [...allSkaters].sort((a, b) => b.stats.assists - a.stats.assists).slice(0, LEADERS_LIMIT),
    plusMinus: [...allSkaters].sort((a, b) => b.stats.plusMinus - a.stats.plusMinus).slice(0, LEADERS_LIMIT),
    powerPlayGoals: [...allSkaters].sort((a, b) => b.stats.powerPlayGoals - a.stats.powerPlayGoals).slice(0, LEADERS_LIMIT),
    gameWinningGoals: [...allSkaters].sort((a, b) => b.stats.gameWinningGoals - a.stats.gameWinningGoals).slice(0, LEADERS_LIMIT),
    shots: [...allSkaters].sort((a, b) => b.stats.shots - a.stats.shots).slice(0, LEADERS_LIMIT),
    hits: [...allSkaters].sort((a, b) => b.stats.hits - a.stats.hits).slice(0, LEADERS_LIMIT),
    blockedShots: [...allSkaters].sort((a, b) => b.stats.blockedShots - a.stats.blockedShots).slice(0, LEADERS_LIMIT),
    timeOnIce: [...allSkaters].sort((a, b) => {
      const aMinutes = parseTimeOnIce(a.stats.timeOnIcePerGame);
      const bMinutes = parseTimeOnIce(b.stats.timeOnIcePerGame);
      return bMinutes - aMinutes;
    }).slice(0, LEADERS_LIMIT),
    rookies: allSkaters.filter((p) => p.bio.isRookie).sort((a, b) => b.stats.points - a.stats.points).slice(0, LEADERS_LIMIT),
  };
}

export async function fetchGoalieLeaders(): Promise<LeagueGoalieLeaders> {
  const allGoalies = await fetchGoalieStats(MIN_GOALIE_GAMES);

  const now = new Date().toISOString();

  // Filter for qualified goalies (enough games for rate stats)
  const qualifiedGoalies = allGoalies.filter((g) => g.stats.gamesPlayed >= 10);

  return {
    updatedAt: now,
    season: CURRENT_SEASON,
    wins: [...allGoalies].sort((a, b) => b.stats.wins - a.stats.wins).slice(0, LEADERS_LIMIT),
    savePct: [...qualifiedGoalies].sort((a, b) => b.stats.savePct - a.stats.savePct).slice(0, LEADERS_LIMIT),
    goalsAgainstAverage: [...qualifiedGoalies].sort((a, b) => a.stats.goalsAgainstAverage - b.stats.goalsAgainstAverage).slice(0, LEADERS_LIMIT),
    shutouts: [...allGoalies].sort((a, b) => b.stats.shutouts - a.stats.shutouts).slice(0, LEADERS_LIMIT),
    gamesPlayed: [...allGoalies].sort((a, b) => b.stats.gamesPlayed - a.stats.gamesPlayed).slice(0, LEADERS_LIMIT),
  };
}

// =============================================================================
// Individual Player Functions
// =============================================================================

export async function fetchSkaterById(playerId: number): Promise<SkaterCard | null> {
  // Use cached stats map for better performance
  const statsMap = await fetchAllSkaterStatsMap();
  const statsData = statsMap.get(playerId);
  if (!statsData) return null;

  const card = mapNHLSkaterToCard(statsData);

  // Try to enrich with player landing page data
  try {
    const landingUrl = `${NHL_WEB_API}/player/${playerId}/landing`;
    const landingData = await fetchWithRetry<any>(landingUrl);
    if (landingData) {
      card.bio.headshot = landingData.headshot || card.bio.headshot;
      card.bio.heightInInches = landingData.heightInInches || null;
      card.bio.weightInPounds = landingData.weightInPounds || null;
      card.bio.birthDate = landingData.birthDate || null;
      card.bio.birthCity = landingData.birthCity?.default || null;
      card.bio.birthCountry = landingData.birthCountry || null;
      card.bio.jerseyNumber = landingData.sweaterNumber || null;
      card.bio.shootsCatches = landingData.shootsCatches || "R";
      card.bio.isRookie = landingData.isRookie || false;
      card.bio.teamAbbrev = landingData.currentTeamAbbrev || card.bio.teamAbbrev;
      card.bio.teamName = landingData.fullTeamName?.default || card.bio.teamName;
    }
  } catch {
    // Landing data optional
  }

  return card;
}

export async function fetchGoalieById(playerId: number): Promise<GoalieDetailCard | null> {
  // Use cached stats map for better performance
  const statsMap = await fetchAllGoalieStatsMap();
  const statsData = statsMap.get(playerId);
  if (!statsData) return null;

  const card = mapNHLGoalieToCard(statsData);

  // Try to enrich with player landing page data
  try {
    const landingUrl = `${NHL_WEB_API}/player/${playerId}/landing`;
    const landingData = await fetchWithRetry<any>(landingUrl);
    if (landingData) {
      card.bio.headshot = landingData.headshot || card.bio.headshot;
      card.bio.heightInInches = landingData.heightInInches || null;
      card.bio.weightInPounds = landingData.weightInPounds || null;
      card.bio.birthDate = landingData.birthDate || null;
      card.bio.birthCity = landingData.birthCity?.default || null;
      card.bio.birthCountry = landingData.birthCountry || null;
      card.bio.jerseyNumber = landingData.sweaterNumber || null;
      card.bio.shootsCatches = landingData.shootsCatches || "L";
      card.bio.teamAbbrev = landingData.currentTeamAbbrev || card.bio.teamAbbrev;
      card.bio.teamName = landingData.fullTeamName?.default || card.bio.teamName;
    }
  } catch {
    // Landing data optional
  }

  return card;
}

// Deprecated: Use fetchTeamRoster instead
export async function fetchTeamSkaters(teamAbbrev: string): Promise<SkaterCard[]> {
  const roster = await fetchTeamRoster(teamAbbrev);
  return [...roster.forwards, ...roster.defensemen];
}

// Deprecated: Use fetchTeamRoster instead
export async function fetchTeamGoalies(teamAbbrev: string): Promise<GoalieDetailCard[]> {
  const roster = await fetchTeamRoster(teamAbbrev);
  return roster.goalies;
}

export async function fetchTeamLeaders(teamAbbrev: string): Promise<TeamLeaders> {
  const roster = await fetchTeamRoster(teamAbbrev);

  const allSkaters = [...roster.forwards, ...roster.defensemen];

  return {
    teamAbbrev,
    points: allSkaters.sort((a, b) => b.stats.points - a.stats.points)[0] || null,
    goals: allSkaters.sort((a, b) => b.stats.goals - a.stats.goals)[0] || null,
    assists: allSkaters.sort((a, b) => b.stats.assists - a.stats.assists)[0] || null,
    plusMinus: allSkaters.sort((a, b) => b.stats.plusMinus - a.stats.plusMinus)[0] || null,
    goalie: roster.goalies[0] || null,
  };
}

// =============================================================================
// Mapping Functions (for league-wide stats without team info)
// =============================================================================

function mapNHLSkaterToCard(data: NHLApiSkaterStats): SkaterCard {
  const position = data.positionCode as PlayerPosition;
  const positionType = getPositionType(position);

  // teamAbbrevs may be null in new API - use empty string as fallback
  const teamAbbrev = (data.teamAbbrevs || "").split(",")[0].trim().toUpperCase() || "NHL";

  const bio: PlayerBio = {
    playerId: data.playerId,
    firstName: getFirstName(data.skaterFullName),
    lastName: data.lastName,
    fullName: data.skaterFullName,
    teamAbbrev,
    teamName: teamAbbrev,
    position,
    positionType,
    jerseyNumber: null,
    shootsCatches: "R",
    heightInInches: null,
    weightInPounds: null,
    birthDate: null,
    birthCity: null,
    birthCountry: null,
    nationality: null,
    isActive: true,
    isRookie: false,
    // League stats API doesn't have team info, so headshot will be null (fallback to team logo)
    headshot: getHeadshotUrl(data.playerId, teamAbbrev),
  };

  const stats: SkaterSeasonStats = {
    playerId: data.playerId,
    season: CURRENT_SEASON,
    teamAbbrev,
    gamesPlayed: data.gamesPlayed,
    goals: data.goals,
    assists: data.assists,
    points: data.points,
    plusMinus: data.plusMinus,
    penaltyMinutes: data.penaltyMinutes,
    powerPlayGoals: data.ppGoals,
    powerPlayPoints: data.ppPoints,
    shorthandedGoals: data.shGoals,
    shorthandedPoints: data.shPoints,
    gameWinningGoals: data.gameWinningGoals,
    overtimeGoals: data.otGoals,
    shots: data.shots,
    shootingPct: data.shootingPct || 0,
    timeOnIcePerGame: formatSecondsToTime(data.timeOnIcePerGame),
    faceoffWinPct: data.faceoffWinPct || 0,
    blockedShots: 0,
    hits: 0,
    takeaways: 0,
    giveaways: 0,
  };

  return { bio, stats };
}

function mapNHLGoalieToCard(data: NHLApiGoalieStats): GoalieDetailCard {
  // teamAbbrevs may be null in new API - use empty string as fallback
  const teamAbbrev = (data.teamAbbrevs || "").split(",")[0].trim().toUpperCase() || "NHL";

  const bio: PlayerBio = {
    playerId: data.playerId,
    firstName: getFirstName(data.goalieFullName),
    lastName: data.lastName,
    fullName: data.goalieFullName,
    teamAbbrev,
    teamName: teamAbbrev,
    position: "G",
    positionType: "goalie",
    jerseyNumber: null,
    shootsCatches: "L",
    heightInInches: null,
    weightInPounds: null,
    birthDate: null,
    birthCity: null,
    birthCountry: null,
    nationality: null,
    isActive: true,
    isRookie: false,
    // League stats API doesn't have team info, so headshot will be null (fallback to team logo)
    headshot: getHeadshotUrl(data.playerId, teamAbbrev),
  };

  const stats: GoalieSeasonStats = {
    playerId: data.playerId,
    season: CURRENT_SEASON,
    teamAbbrev,
    gamesPlayed: data.gamesPlayed,
    gamesStarted: data.gamesStarted,
    wins: data.wins,
    losses: data.losses,
    otLosses: data.otLosses,
    shotsAgainst: data.shotsAgainst,
    goalsAgainst: data.goalsAgainst,
    saves: data.saves,
    savePct: data.savePct,
    goalsAgainstAverage: data.goalsAgainstAverage,
    shutouts: data.shutouts,
    timeOnIce: formatSecondsToTime(data.timeOnIce),
    qualityStarts: null,
    qualityStartsPct: null,
  };

  return { bio, stats };
}

// =============================================================================
// Utility Functions
// =============================================================================

function getPositionType(position: PlayerPosition): PositionType {
  if (position === "G") return "goalie";
  if (position === "D") return "defenseman";
  return "forward";
}

function getFirstName(fullName: string): string {
  const parts = fullName.split(" ");
  return parts.slice(0, -1).join(" ") || fullName;
}

function formatSecondsToTime(seconds: number): string {
  if (!seconds || isNaN(seconds)) return "0:00";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

function getHeadshotUrl(playerId: number, teamAbbrev?: string): string | null {
  // NHL headshot URLs require both player ID and team abbreviation
  // Format: https://assets.nhle.com/mugs/nhl/{SEASON}/{TEAM}/{PLAYER_ID}.png
  if (!teamAbbrev || teamAbbrev === "NHL" || teamAbbrev === "") {
    return null; // Will fallback to team logo in UI
  }
  return `https://assets.nhle.com/mugs/nhl/${CURRENT_SEASON}/${teamAbbrev}/${playerId}.png`;
}

function parseTimeOnIce(timeStr: string): number {
  if (!timeStr) return 0;
  const parts = timeStr.split(":");
  if (parts.length !== 2) return 0;
  return parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
}

// =============================================================================
// Enhanced Stats Fetching (Hits, Blocks, etc.)
// Uses caching to prevent rate limiting during static generation
// =============================================================================

async function fetchSkaterRealTimeStatsInternal(): Promise<Map<number, { hits: number; blockedShots: number }>> {
  const url = `${NHL_STATS_API}/skater/realtime?isAggregate=true&isGame=false&limit=-1&cayenneExp=seasonId=${CURRENT_SEASON}`;

  const data = await fetchWithRetry<{ data: any[] }>(url);
  const map = new Map<number, { hits: number; blockedShots: number }>();

  if (data?.data) {
    data.data.forEach((p) => {
      map.set(p.playerId, {
        hits: p.hits || 0,
        blockedShots: p.blockedShots || 0,
      });
    });
  }
  return map;
}

export async function fetchSkaterRealTimeStats(): Promise<Map<number, { hits: number; blockedShots: number }>> {
  // Return from cache if available
  if (realtimeStatsCache) {
    return realtimeStatsCache;
  }

  // If fetch is in progress, wait for it
  if (realtimeStatsCachePromise) {
    return realtimeStatsCachePromise;
  }

  // Start the fetch and cache the promise
  realtimeStatsCachePromise = fetchSkaterRealTimeStatsInternal();

  try {
    realtimeStatsCache = await realtimeStatsCachePromise;
    return realtimeStatsCache;
  } finally {
    realtimeStatsCachePromise = null;
  }
}

export async function fetchEnrichedSkaterStats(minGames = MIN_SKATER_GAMES): Promise<SkaterCard[]> {
  const [baseSkaters, realTimeStats] = await Promise.all([
    fetchSkaterStats(minGames),
    fetchSkaterRealTimeStats(),
  ]);

  return baseSkaters.map((skater) => {
    const rtStats = realTimeStats.get(skater.bio.playerId);
    if (rtStats) {
      skater.stats.hits = rtStats.hits;
      skater.stats.blockedShots = rtStats.blockedShots;
    }
    return skater;
  });
}

// =============================================================================
// Legacy Export for Backward Compatibility
// =============================================================================

export interface PlayerHubContext {
  specialTeams?: {
    teams: Record<string, any>;
  } | null;
  goalieShotProfiles?: any[];
}

export function getPlayerHubContext(): PlayerHubContext {
  return {
    specialTeams: null,
    goalieShotProfiles: [],
  };
}

// =============================================================================
// Search Functions
// =============================================================================

export async function searchPlayers(query: string): Promise<{ skaters: SkaterCard[]; goalies: GoalieDetailCard[] }> {
  const normalizedQuery = query.toLowerCase().trim();
  if (normalizedQuery.length < 2) {
    return { skaters: [], goalies: [] };
  }

  const [allSkaters, allGoalies] = await Promise.all([
    fetchSkaterStats(1),
    fetchGoalieStats(1),
  ]);

  const matchingSkaters = allSkaters.filter((p) =>
    p.bio.fullName.toLowerCase().includes(normalizedQuery) ||
    p.bio.lastName.toLowerCase().includes(normalizedQuery)
  ).slice(0, 20);

  const matchingGoalies = allGoalies.filter((g) =>
    g.bio.fullName.toLowerCase().includes(normalizedQuery) ||
    g.bio.lastName.toLowerCase().includes(normalizedQuery)
  ).slice(0, 10);

  return { skaters: matchingSkaters, goalies: matchingGoalies };
}

// =============================================================================
// Stat Formatting Utilities
// =============================================================================

export function formatStat(value: number | string | null, format: "number" | "decimal" | "percent" | "time" | "plusMinus", precision = 1): string {
  if (value === null || value === undefined) return "—";

  const num = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(num)) return "—";

  switch (format) {
    case "number":
      return num.toFixed(0);
    case "decimal":
      return num.toFixed(precision);
    case "percent":
      // If value is already a percentage (like 12.5), display as is
      // If value is a decimal (like 0.125), multiply by 100
      const pctValue = num < 1 && num > 0 ? num * 100 : num;
      return `${pctValue.toFixed(precision)}%`;
    case "time":
      return typeof value === "string" ? value : formatSecondsToTime(num);
    case "plusMinus":
      return num >= 0 ? `+${num}` : `${num}`;
    default:
      return String(value);
  }
}

export function getStatColor(value: number, higherIsBetter = true, thresholds?: { good: number; bad: number }): string {
  if (!thresholds) return "text-white";

  if (higherIsBetter) {
    if (value >= thresholds.good) return "text-emerald-400";
    if (value <= thresholds.bad) return "text-rose-400";
  } else {
    if (value <= thresholds.good) return "text-emerald-400";
    if (value >= thresholds.bad) return "text-rose-400";
  }
  return "text-white";
}
