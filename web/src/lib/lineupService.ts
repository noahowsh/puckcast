// Lineup Projection Service
// Builds projected lineups based on player performance and injury status

import type {
  TeamLineup,
  LineupPlayer,
  GoalieLineup,
  LineupStrengthMetrics,
  MissingPlayerImpact,
  LineupFeatures,
  TeamLineupPattern,
  PositionGroup,
} from "@/types/lineup";
import type { SkaterCard, GoalieDetailCard } from "@/types/player";
import { fetchTeamRoster } from "./playerHub";
import { getTeamInjuries } from "./injuryService";
import { getGoaliePulse } from "./data";

// =============================================================================
// Configuration
// =============================================================================

// Default lineup sizes (used when no historical data available)
const DEFAULT_FORWARD_SLOTS = 12;
const DEFAULT_DEFENSE_SLOTS = 6;
const DEFAULT_GOALIE_SLOTS = 2;

// Weights for ranking players
const RANKING_WEIGHTS = {
  timeOnIce: 0.40,  // TOI is most important
  points: 0.25,
  pointsPerGame: 0.20,
  plusMinus: 0.10,
  gamesPlayed: 0.05,
};

// =============================================================================
// Main Lineup Projection Function
// =============================================================================

/**
 * Build a projected lineup for a team
 */
export async function buildProjectedLineup(teamAbbrev: string): Promise<TeamLineup> {
  // Fetch roster and injuries in parallel
  const [roster, injuries, goaliePulse] = await Promise.all([
    fetchTeamRoster(teamAbbrev),
    getTeamInjuries(teamAbbrev),
    Promise.resolve(getGoaliePulse()),
  ]);

  // Get injury names for filtering
  const injuredNames = new Set(
    injuries?.injuries
      .filter(i => i.isOut)
      .map(i => i.playerName.toLowerCase()) || []
  );

  // Convert roster to lineup players and mark injuries
  const forwards = roster.forwards.map(p => skaterToLineupPlayer(p, injuredNames));
  const defensemen = roster.defensemen.map(p => skaterToLineupPlayer(p, injuredNames));
  const goalies = roster.goalies.map(g => goalieToLineupGoalie(g, injuredNames, goaliePulse, teamAbbrev));

  // Rank players by performance
  const rankedForwards = rankPlayers(forwards);
  const rankedDefensemen = rankPlayers(defensemen);
  const rankedGoalies = rankGoalies(goalies);

  // Detect typical lineup sizes from roster size (or use defaults)
  const typicalForwards = Math.min(forwards.length, DEFAULT_FORWARD_SLOTS);
  const typicalDefensemen = Math.min(defensemen.length, DEFAULT_DEFENSE_SLOTS);
  const typicalGoalies = Math.min(goalies.length, DEFAULT_GOALIE_SLOTS);

  // Build projected roster (healthy players only, up to typical slots)
  const healthyForwards = rankedForwards.filter(p => p.isHealthy);
  const healthyDefensemen = rankedDefensemen.filter(p => p.isHealthy);
  const healthyGoalies = rankedGoalies.filter(g => g.isHealthy);

  const projectedForwards = healthyForwards.slice(0, typicalForwards);
  const projectedDefensemen = healthyDefensemen.slice(0, typicalDefensemen);
  const projectedGoalies = healthyGoalies.slice(0, typicalGoalies);

  // Healthy scratches (healthy but not in projected lineup)
  const healthyScratches = [
    ...healthyForwards.slice(typicalForwards),
    ...healthyDefensemen.slice(typicalDefensemen),
  ];

  // Calculate lineup strength metrics
  const lineupStrength = calculateLineupStrength(
    projectedForwards,
    projectedDefensemen,
    projectedGoalies,
    rankedForwards,
    rankedDefensemen,
    rankedGoalies
  );

  return {
    teamAbbrev,
    teamName: roster.teamName,
    forwards: rankedForwards,
    defensemen: rankedDefensemen,
    goalies: rankedGoalies,
    typicalForwards,
    typicalDefensemen,
    typicalGoalies,
    projectedForwards,
    projectedDefensemen,
    projectedGoalies,
    healthyScratches,
    lineupStrength,
    lastUpdated: new Date().toISOString(),
  };
}

// =============================================================================
// Player Conversion Functions
// =============================================================================

function skaterToLineupPlayer(skater: SkaterCard, injuredNames: Set<string>): LineupPlayer {
  const isHealthy = !injuredNames.has(skater.bio.fullName.toLowerCase());

  // Calculate TOI in seconds from "MM:SS" format
  const toiParts = skater.stats.timeOnIcePerGame.split(":");
  const toiSeconds = toiParts.length === 2
    ? parseInt(toiParts[0], 10) * 60 + parseInt(toiParts[1], 10)
    : 0;

  return {
    playerId: skater.bio.playerId,
    playerName: skater.bio.fullName,
    position: skater.bio.position,
    jerseyNumber: skater.bio.jerseyNumber,
    gamesPlayed: skater.stats.gamesPlayed,
    timeOnIcePerGame: toiSeconds,
    goals: skater.stats.goals,
    assists: skater.stats.assists,
    points: skater.stats.points,
    plusMinus: skater.stats.plusMinus,
    rankingScore: 0, // Will be calculated
    isHealthy,
    injuryStatus: isHealthy ? null : "out",
  };
}

function goalieToLineupGoalie(
  goalie: GoalieDetailCard,
  injuredNames: Set<string>,
  goaliePulse: ReturnType<typeof getGoaliePulse>,
  teamAbbrev: string
): GoalieLineup {
  const isHealthy = !injuredNames.has(goalie.bio.fullName.toLowerCase());

  // Find goalie in pulse data
  const pulseData = goaliePulse.goalies.find(
    g => g.name.toLowerCase().includes(goalie.bio.lastName.toLowerCase()) && g.team === teamAbbrev
  );

  return {
    playerId: goalie.bio.playerId,
    playerName: goalie.bio.fullName,
    jerseyNumber: goalie.bio.jerseyNumber,
    gamesPlayed: goalie.stats.gamesPlayed,
    gamesStarted: goalie.stats.gamesStarted,
    wins: goalie.stats.wins,
    savePct: goalie.stats.savePct,
    goalsAgainstAverage: goalie.stats.goalsAgainstAverage,
    rankingScore: 0, // Will be calculated
    isHealthy,
    isProjectedStarter: false, // Will be determined
    startLikelihood: pulseData?.startLikelihood || 0.5,
    restDays: pulseData?.restDays || 0,
  };
}

// =============================================================================
// Ranking Functions
// =============================================================================

function rankPlayers(players: LineupPlayer[]): LineupPlayer[] {
  // Calculate ranking scores
  const maxTOI = Math.max(...players.map(p => p.timeOnIcePerGame), 1);
  const maxPoints = Math.max(...players.map(p => p.points), 1);
  const maxPPG = Math.max(...players.map(p => p.gamesPlayed > 0 ? p.points / p.gamesPlayed : 0), 1);
  const maxPlusMinus = Math.max(...players.map(p => Math.abs(p.plusMinus)), 1);
  const maxGP = Math.max(...players.map(p => p.gamesPlayed), 1);

  const rankedPlayers = players.map(player => {
    const toiScore = (player.timeOnIcePerGame / maxTOI) * RANKING_WEIGHTS.timeOnIce;
    const pointsScore = (player.points / maxPoints) * RANKING_WEIGHTS.points;
    const ppgScore = player.gamesPlayed > 0
      ? ((player.points / player.gamesPlayed) / maxPPG) * RANKING_WEIGHTS.pointsPerGame
      : 0;
    const pmScore = ((player.plusMinus + maxPlusMinus) / (2 * maxPlusMinus)) * RANKING_WEIGHTS.plusMinus;
    const gpScore = (player.gamesPlayed / maxGP) * RANKING_WEIGHTS.gamesPlayed;

    const rankingScore = (toiScore + pointsScore + ppgScore + pmScore + gpScore) * 100;

    return {
      ...player,
      rankingScore: Math.round(rankingScore * 10) / 10,
    };
  });

  // Sort by ranking score descending
  return rankedPlayers.sort((a, b) => b.rankingScore - a.rankingScore);
}

function rankGoalies(goalies: GoalieLineup[]): GoalieLineup[] {
  // Rank goalies by combination of wins, save%, and start likelihood
  const maxWins = Math.max(...goalies.map(g => g.wins), 1);
  const maxGP = Math.max(...goalies.map(g => g.gamesPlayed), 1);

  const rankedGoalies = goalies.map(goalie => {
    const winsScore = (goalie.wins / maxWins) * 0.30;
    const svpScore = goalie.savePct * 0.30; // Already 0-1
    const gaaScore = Math.max(0, (4 - goalie.goalsAgainstAverage) / 4) * 0.20;
    const likelihoodScore = goalie.startLikelihood * 0.10;
    const gpScore = (goalie.gamesPlayed / maxGP) * 0.10;

    const rankingScore = (winsScore + svpScore + gaaScore + likelihoodScore + gpScore) * 100;

    return {
      ...goalie,
      rankingScore: Math.round(rankingScore * 10) / 10,
    };
  });

  // Sort by ranking score descending
  const sorted = rankedGoalies.sort((a, b) => b.rankingScore - a.rankingScore);

  // Mark the top healthy goalie as projected starter
  let starterFound = false;
  return sorted.map(g => ({
    ...g,
    isProjectedStarter: !starterFound && g.isHealthy ? (starterFound = true, true) : false,
  }));
}

// =============================================================================
// Lineup Strength Calculation
// =============================================================================

function calculateLineupStrength(
  projectedForwards: LineupPlayer[],
  projectedDefensemen: LineupPlayer[],
  projectedGoalies: GoalieLineup[],
  allForwards: LineupPlayer[],
  allDefensemen: LineupPlayer[],
  allGoalies: GoalieLineup[]
): LineupStrengthMetrics {
  // Calculate offensive strength from forwards
  const avgForwardPoints = projectedForwards.length > 0
    ? projectedForwards.reduce((sum, p) => sum + p.points, 0) / projectedForwards.length
    : 0;
  const avgForwardTOI = projectedForwards.length > 0
    ? projectedForwards.reduce((sum, p) => sum + p.timeOnIcePerGame, 0) / projectedForwards.length
    : 0;
  const topLineStrength = projectedForwards.slice(0, 3).reduce((sum, p) => sum + p.rankingScore, 0) / 3;

  // Calculate defensive strength
  const avgDefensemanPoints = projectedDefensemen.length > 0
    ? projectedDefensemen.reduce((sum, p) => sum + p.points, 0) / projectedDefensemen.length
    : 0;
  const avgDefensemanTOI = projectedDefensemen.length > 0
    ? projectedDefensemen.reduce((sum, p) => sum + p.timeOnIcePerGame, 0) / projectedDefensemen.length
    : 0;
  const topPairStrength = projectedDefensemen.slice(0, 2).reduce((sum, p) => sum + p.rankingScore, 0) / 2;

  // Calculate goalie strength
  const starter = projectedGoalies.find(g => g.isProjectedStarter);
  const backup = projectedGoalies.find(g => !g.isProjectedStarter);
  const starterRating = starter ? starter.rankingScore : 0;
  const backupRating = backup ? backup.rankingScore : 0;
  const goalieStrength = starterRating * 0.7 + backupRating * 0.3;

  // Calculate missing player impact
  const missingPlayers: MissingPlayerImpact[] = [];

  // Check injured forwards
  const injuredForwards = allForwards.filter(p => !p.isHealthy);
  for (const player of injuredForwards) {
    const ppg = player.gamesPlayed > 0 ? player.points / player.gamesPlayed : 0;
    missingPlayers.push({
      playerId: player.playerId,
      playerName: player.playerName,
      position: player.position,
      impactScore: Math.min(10, player.rankingScore / 10),
      statsLost: {
        pointsPerGame: ppg,
        toiPerGame: player.timeOnIcePerGame / 60, // Convert to minutes
      },
    });
  }

  // Check injured defensemen
  const injuredDefensemen = allDefensemen.filter(p => !p.isHealthy);
  for (const player of injuredDefensemen) {
    const ppg = player.gamesPlayed > 0 ? player.points / player.gamesPlayed : 0;
    missingPlayers.push({
      playerId: player.playerId,
      playerName: player.playerName,
      position: player.position,
      impactScore: Math.min(10, player.rankingScore / 10),
      statsLost: {
        pointsPerGame: ppg,
        toiPerGame: player.timeOnIcePerGame / 60,
      },
    });
  }

  // Check injured goalies
  const injuredGoalies = allGoalies.filter(g => !g.isHealthy);
  for (const goalie of injuredGoalies) {
    missingPlayers.push({
      playerId: goalie.playerId,
      playerName: goalie.playerName,
      position: "G",
      impactScore: Math.min(10, goalie.rankingScore / 10),
      statsLost: {
        pointsPerGame: 0,
        toiPerGame: 60, // Goalies play full games
      },
    });
  }

  // Calculate injury impact
  const injuryImpact = -missingPlayers.reduce((sum, p) => sum + p.impactScore, 0);

  // Calculate overall strength scores (0-100)
  const offensiveStrength = Math.min(100, (avgForwardPoints * 2 + topLineStrength) / 3 * 10);
  const defensiveStrength = Math.min(100, (avgDefensemanPoints * 2 + topPairStrength) / 3 * 10);

  // Overall quality combines all factors
  const overallQuality = Math.min(100, Math.max(0,
    offensiveStrength * 0.35 +
    defensiveStrength * 0.30 +
    goalieStrength * 0.35 +
    injuryImpact // Negative adjustment
  ));

  // Calculate percent of full strength
  const fullStrengthScore = allForwards.reduce((sum, p) => sum + p.rankingScore, 0) +
    allDefensemen.reduce((sum, p) => sum + p.rankingScore, 0) +
    allGoalies.reduce((sum, g) => sum + g.rankingScore, 0);

  const currentStrengthScore = projectedForwards.reduce((sum, p) => sum + p.rankingScore, 0) +
    projectedDefensemen.reduce((sum, p) => sum + p.rankingScore, 0) +
    projectedGoalies.reduce((sum, g) => sum + g.rankingScore, 0);

  const percentOfFullStrength = fullStrengthScore > 0
    ? Math.round((currentStrengthScore / fullStrengthScore) * 100)
    : 100;

  return {
    overallQuality: Math.round(overallQuality),
    offensiveStrength: Math.round(offensiveStrength),
    avgForwardPoints: Math.round(avgForwardPoints * 10) / 10,
    avgForwardTOI: Math.round(avgForwardTOI),
    topLineStrength: Math.round(topLineStrength),
    defensiveStrength: Math.round(defensiveStrength),
    avgDefensemanPoints: Math.round(avgDefensemanPoints * 10) / 10,
    avgDefensemanTOI: Math.round(avgDefensemanTOI),
    topPairStrength: Math.round(topPairStrength),
    goalieStrength: Math.round(goalieStrength),
    starterRating: Math.round(starterRating),
    backupRating: Math.round(backupRating),
    injuryImpact: Math.round(injuryImpact),
    missingPlayerImpact: missingPlayers.sort((a, b) => b.impactScore - a.impactScore),
    percentOfFullStrength,
  };
}

// =============================================================================
// Feature Generation for Model
// =============================================================================

/**
 * Generate lineup features for the prediction model
 */
export async function generateLineupFeatures(
  homeTeam: string,
  awayTeam: string,
  gameId: string
): Promise<{ home: LineupFeatures; away: LineupFeatures }> {
  const [homeLineup, awayLineup] = await Promise.all([
    buildProjectedLineup(homeTeam),
    buildProjectedLineup(awayTeam),
  ]);

  const homeFeatures = lineupToFeatures(homeLineup, gameId);
  const awayFeatures = lineupToFeatures(awayLineup, gameId);

  // Calculate comparative advantages
  homeFeatures.lineupAdvantage = homeFeatures.lineupQuality - awayFeatures.lineupQuality;
  homeFeatures.offensiveAdvantage = homeFeatures.offensiveStrength - awayFeatures.defensiveStrength;
  homeFeatures.defensiveAdvantage = homeFeatures.defensiveStrength - awayFeatures.offensiveStrength;
  homeFeatures.goalieAdvantage = homeFeatures.goalieStrength - awayFeatures.goalieStrength;

  awayFeatures.lineupAdvantage = -homeFeatures.lineupAdvantage;
  awayFeatures.offensiveAdvantage = -homeFeatures.offensiveAdvantage;
  awayFeatures.defensiveAdvantage = -homeFeatures.defensiveAdvantage;
  awayFeatures.goalieAdvantage = -homeFeatures.goalieAdvantage;

  return { home: homeFeatures, away: awayFeatures };
}

function lineupToFeatures(lineup: TeamLineup, gameId: string): LineupFeatures {
  const { lineupStrength } = lineup;

  return {
    teamAbbrev: lineup.teamAbbrev,
    gameId,
    lineupQuality: lineupStrength.overallQuality,
    offensiveStrength: lineupStrength.offensiveStrength,
    defensiveStrength: lineupStrength.defensiveStrength,
    goalieStrength: lineupStrength.goalieStrength,
    injuryImpact: lineupStrength.injuryImpact,
    keyPlayersOut: lineupStrength.missingPlayerImpact.filter(p => p.impactScore >= 5).length,
    percentFullStrength: lineupStrength.percentOfFullStrength,
    forwardDepth: lineup.projectedForwards.length / lineup.typicalForwards * 100,
    defenseDepth: lineup.projectedDefensemen.length / lineup.typicalDefensemen * 100,
    goalieDepth: lineup.projectedGoalies.length / lineup.typicalGoalies * 100,
    // Comparative features initialized to 0, calculated after both teams processed
    lineupAdvantage: 0,
    offensiveAdvantage: 0,
    defensiveAdvantage: 0,
    goalieAdvantage: 0,
  };
}

// =============================================================================
// Bulk Operations
// =============================================================================

/**
 * Build projected lineups for all teams
 */
export async function buildAllTeamLineups(teamAbbrevs: string[]): Promise<Record<string, TeamLineup>> {
  const lineups: Record<string, TeamLineup> = {};

  // Process in batches to avoid rate limiting
  const batchSize = 4;
  for (let i = 0; i < teamAbbrevs.length; i += batchSize) {
    const batch = teamAbbrevs.slice(i, i + batchSize);
    const results = await Promise.all(batch.map(buildProjectedLineup));

    for (let j = 0; j < batch.length; j++) {
      lineups[batch[j]] = results[j];
    }
  }

  return lineups;
}

// =============================================================================
// Export
// =============================================================================

export type { TeamLineup, LineupFeatures };
