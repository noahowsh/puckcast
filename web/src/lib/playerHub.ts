// Player Hub - NHL API Integration for Player & Goalie Statistics
// Fetches and processes player data from NHL Stats API

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
// API Fetching Functions
// =============================================================================

async function fetchWithRetry<T>(url: string, options: RequestInit = {}, retries = 3): Promise<T | null> {
  for (let i = 0; i < retries; i++) {
    try {
      const res = await fetch(url, {
        ...options,
        next: { revalidate: ROSTER_CACHE_TTL },
      });
      if (!res.ok) {
        console.error(`API request failed: ${url} - ${res.status}`);
        if (i === retries - 1) return null;
        continue;
      }
      return (await res.json()) as T;
    } catch (err) {
      console.error(`API request error: ${url}`, err);
      if (i === retries - 1) return null;
    }
  }
  return null;
}

// =============================================================================
// Skater Stats Functions
// =============================================================================

export async function fetchSkaterStats(minGames = MIN_SKATER_GAMES): Promise<SkaterCard[]> {
  const url = `${NHL_STATS_API}/skater/summary?isAggregate=true&isGame=false&limit=-1&cayenneExp=seasonId=${CURRENT_SEASON}`;

  const data = await fetchWithRetry<{ data: NHLApiSkaterStats[] }>(url);
  if (!data?.data) return [];

  return data.data
    .filter((p) => p.gamesPlayed >= minGames)
    .map((p) => mapNHLSkaterToCard(p))
    .sort((a, b) => b.stats.points - a.stats.points);
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

export async function fetchSkaterById(playerId: number): Promise<SkaterCard | null> {
  // First try to get from summary stats
  const url = `${NHL_STATS_API}/skater/summary?isAggregate=true&isGame=false&limit=1&cayenneExp=seasonId=${CURRENT_SEASON} and playerId=${playerId}`;

  const data = await fetchWithRetry<{ data: NHLApiSkaterStats[] }>(url);
  if (!data?.data?.[0]) return null;

  const card = mapNHLSkaterToCard(data.data[0]);

  // Try to enrich with player landing page data
  try {
    const landingUrl = `${NHL_WEB_API}/player/${playerId}/landing`;
    const landingData = await fetchWithRetry<any>(landingUrl);
    if (landingData) {
      card.bio.headshot = landingData.headshot || null;
      card.bio.heightInInches = landingData.heightInInches || null;
      card.bio.weightInPounds = landingData.weightInPounds || null;
      card.bio.birthDate = landingData.birthDate || null;
      card.bio.birthCity = landingData.birthCity?.default || null;
      card.bio.birthCountry = landingData.birthCountry || null;
      card.bio.jerseyNumber = landingData.sweaterNumber || null;
      card.bio.shootsCatches = landingData.shootsCatches || "R";
      card.bio.isRookie = landingData.isRookie || false;
    }
  } catch {
    // Landing data optional
  }

  return card;
}

export async function fetchTeamSkaters(teamAbbrev: string): Promise<SkaterCard[]> {
  const allSkaters = await fetchSkaterStats(1);
  return allSkaters.filter((p) => p.bio.teamAbbrev === teamAbbrev);
}

// =============================================================================
// Goalie Stats Functions
// =============================================================================

export async function fetchGoalieStats(minGames = MIN_GOALIE_GAMES): Promise<GoalieDetailCard[]> {
  const url = `${NHL_STATS_API}/goalie/summary?isAggregate=true&isGame=false&limit=-1&cayenneExp=seasonId=${CURRENT_SEASON}`;

  const data = await fetchWithRetry<{ data: NHLApiGoalieStats[] }>(url);
  if (!data?.data) return [];

  return data.data
    .filter((g) => g.gamesPlayed >= minGames)
    .map((g) => mapNHLGoalieToCard(g))
    .sort((a, b) => b.stats.wins - a.stats.wins);
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

export async function fetchGoalieById(playerId: number): Promise<GoalieDetailCard | null> {
  const url = `${NHL_STATS_API}/goalie/summary?isAggregate=true&isGame=false&limit=1&cayenneExp=seasonId=${CURRENT_SEASON} and playerId=${playerId}`;

  const data = await fetchWithRetry<{ data: NHLApiGoalieStats[] }>(url);
  if (!data?.data?.[0]) return null;

  const card = mapNHLGoalieToCard(data.data[0]);

  // Try to enrich with player landing page data
  try {
    const landingUrl = `${NHL_WEB_API}/player/${playerId}/landing`;
    const landingData = await fetchWithRetry<any>(landingUrl);
    if (landingData) {
      card.bio.headshot = landingData.headshot || null;
      card.bio.heightInInches = landingData.heightInInches || null;
      card.bio.weightInPounds = landingData.weightInPounds || null;
      card.bio.birthDate = landingData.birthDate || null;
      card.bio.birthCity = landingData.birthCity?.default || null;
      card.bio.birthCountry = landingData.birthCountry || null;
      card.bio.jerseyNumber = landingData.sweaterNumber || null;
      card.bio.shootsCatches = landingData.shootsCatches || "L";
    }
  } catch {
    // Landing data optional
  }

  return card;
}

export async function fetchTeamGoalies(teamAbbrev: string): Promise<GoalieDetailCard[]> {
  const allGoalies = await fetchGoalieStats(1);
  return allGoalies.filter((g) => g.bio.teamAbbrev === teamAbbrev);
}

// =============================================================================
// Team Functions
// =============================================================================

export async function fetchTeamRoster(teamAbbrev: string): Promise<TeamRoster> {
  const [skaters, goalies] = await Promise.all([
    fetchTeamSkaters(teamAbbrev),
    fetchTeamGoalies(teamAbbrev),
  ]);

  const forwards = skaters.filter((p) => p.bio.positionType === "forward");
  const defensemen = skaters.filter((p) => p.bio.positionType === "defenseman");

  // Try to get team name from first player
  const teamName = skaters[0]?.bio.teamName || goalies[0]?.bio.teamName || teamAbbrev;

  return {
    teamAbbrev,
    teamName,
    forwards: forwards.sort((a, b) => b.stats.points - a.stats.points),
    defensemen: defensemen.sort((a, b) => b.stats.points - a.stats.points),
    goalies: goalies.sort((a, b) => b.stats.wins - a.stats.wins),
  };
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
// Mapping Functions
// =============================================================================

function mapNHLSkaterToCard(data: NHLApiSkaterStats): SkaterCard {
  const position = data.positionCode as PlayerPosition;
  const positionType = getPositionType(position);

  // Parse team abbreviation (API sometimes returns multiple like "TOR, MTL")
  const teamAbbrev = (data.teamAbbrevs || "").split(",")[0].trim().toUpperCase();

  const bio: PlayerBio = {
    playerId: data.playerId,
    firstName: getFirstName(data.skaterFullName),
    lastName: data.lastName,
    fullName: data.skaterFullName,
    teamAbbrev,
    teamName: teamAbbrev, // Will be enriched later if needed
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
    headshot: getHeadshotUrl(data.playerId),
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
    shootingPct: data.shootingPct,
    timeOnIcePerGame: formatSecondsToTime(data.timeOnIcePerGame),
    faceoffWinPct: data.faceoffWinPct,
    blockedShots: 0, // Not in summary endpoint
    hits: 0, // Not in summary endpoint
    takeaways: 0,
    giveaways: 0,
  };

  return { bio, stats };
}

function mapNHLGoalieToCard(data: NHLApiGoalieStats): GoalieDetailCard {
  const teamAbbrev = (data.teamAbbrevs || "").split(",")[0].trim().toUpperCase();

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
    headshot: getHeadshotUrl(data.playerId),
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

function getHeadshotUrl(playerId: number): string {
  // NHL API standard headshot URL format
  return `https://assets.nhle.com/headshots/current/168x168/${playerId}.png`;
}

function parseTimeOnIce(timeStr: string): number {
  if (!timeStr) return 0;
  const parts = timeStr.split(":");
  if (parts.length !== 2) return 0;
  return parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
}

// =============================================================================
// Enhanced Stats Fetching (Hits, Blocks, etc.)
// =============================================================================

export async function fetchSkaterRealTimeStats(): Promise<Map<number, { hits: number; blockedShots: number }>> {
  const url = `${NHL_STATS_API}/skater/realtime?isAggregate=true&isGame=false&limit=-1&cayenneExp=seasonId=${CURRENT_SEASON}`;

  const data = await fetchWithRetry<{ data: any[] }>(url);
  if (!data?.data) return new Map();

  const map = new Map<number, { hits: number; blockedShots: number }>();
  data.data.forEach((p) => {
    map.set(p.playerId, {
      hits: p.hits || 0,
      blockedShots: p.blockedShots || 0,
    });
  });
  return map;
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
    p.bio.lastName.toLowerCase().includes(normalizedQuery) ||
    p.bio.teamAbbrev.toLowerCase() === normalizedQuery
  ).slice(0, 20);

  const matchingGoalies = allGoalies.filter((g) =>
    g.bio.fullName.toLowerCase().includes(normalizedQuery) ||
    g.bio.lastName.toLowerCase().includes(normalizedQuery) ||
    g.bio.teamAbbrev.toLowerCase() === normalizedQuery
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
