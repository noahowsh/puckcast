// Player Projections & Analytics
// Generates projection data, skill profiles, and impact metrics based on current stats

import type {
  SkaterCard,
  SeasonProjection,
  StatProjection,
  SkillProfile,
  PercentileRating,
  OnIceImpact,
  ImpactMetric,
  PlayerPosition,
} from "@/types/player";

// =============================================================================
// Constants
// =============================================================================

const TOTAL_SEASON_GAMES = 82;
const CURRENT_SEASON = "20242025";

// =============================================================================
// Percentile Tier Helpers
// =============================================================================

function getPercentileTier(percentile: number): PercentileRating["tier"] {
  if (percentile >= 90) return "elite";
  if (percentile >= 70) return "above-average";
  if (percentile >= 40) return "average";
  if (percentile >= 20) return "below-average";
  return "replacement";
}

function getImpactTier(percentile: number): ImpactMetric["tier"] {
  if (percentile >= 90) return "elite";
  if (percentile >= 70) return "above-average";
  if (percentile >= 40) return "average";
  if (percentile >= 20) return "below-average";
  return "poor";
}

function createPercentileRating(value: number): PercentileRating {
  return {
    value: Math.round(value),
    tier: getPercentileTier(value),
  };
}

function createImpactMetric(percentile: number): ImpactMetric {
  return {
    percentile: Math.round(percentile),
    tier: getImpactTier(percentile),
  };
}

// =============================================================================
// Season Projection Calculator
// =============================================================================

function projectStat(
  current: number,
  gamesPlayed: number,
  gamesRemaining: number,
  variance: number = 0.15
): StatProjection {
  if (gamesPlayed === 0) {
    return { average: 0, median: 0, mode: 0, min: 0, max: 0, current: 0 };
  }

  const perGameRate = current / gamesPlayed;
  const projectedTotal = current + perGameRate * gamesRemaining;

  // Add some realistic variance based on sample size and stat type
  const sampleSizeMultiplier = Math.sqrt(gamesPlayed / 20); // More confidence with more games
  const adjustedVariance = variance / sampleSizeMultiplier;

  const average = Math.round(projectedTotal);
  const median = Math.round(projectedTotal * (1 - adjustedVariance * 0.05));
  const mode = Math.round(projectedTotal * (1 - adjustedVariance * 0.1));
  const min = Math.round(projectedTotal * (1 - adjustedVariance * 2));
  const max = Math.round(projectedTotal * (1 + adjustedVariance * 2));

  return {
    average,
    median,
    mode,
    min: Math.max(current, min), // Can't go below current
    max,
    current,
  };
}

function calculateMilestoneProbabilities(
  projection: StatProjection,
  milestones: number[]
): Record<number, number> {
  const result: Record<number, number> = {};
  const { average, min, max, current } = projection;

  for (const milestone of milestones) {
    if (milestone <= current) {
      result[milestone] = 99.9;
    } else if (milestone > max) {
      result[milestone] = 0;
    } else if (milestone <= min) {
      result[milestone] = 99.9;
    } else {
      // Simple linear interpolation between min and max
      const range = max - min;
      const distanceFromMin = milestone - min;
      const probability = Math.max(0, Math.min(99.9, 100 - (distanceFromMin / range) * 100));
      result[milestone] = Math.round(probability * 10) / 10;
    }
  }

  return result;
}

function generateDistributionSummary(points: StatProjection): string {
  const { average, min, max } = points;
  const midRange = Math.round((average - min) / 2 + min);
  const highRange = Math.round((max - average) / 2 + average);

  if (average >= 100) {
    return `Elite production projected. Most likely range is ${midRange}-${highRange} points, with upside potential exceeding ${max} points in optimal scenarios.`;
  } else if (average >= 80) {
    return `Strong production expected. Most likely outcome is ${midRange}-${highRange} points, establishing this player as a top-line contributor.`;
  } else if (average >= 60) {
    return `Solid middle-six production projected. Range of ${midRange}-${highRange} points most likely, with breakout potential toward ${max}.`;
  } else if (average >= 40) {
    return `Moderate production expected. Likely to finish between ${midRange}-${highRange} points with consistent deployment.`;
  } else {
    return `Limited offensive production projected. Expected range of ${min}-${max} points based on current usage patterns.`;
  }
}

export function generateSeasonProjection(
  player: SkaterCard,
  allPlayers: SkaterCard[]
): SeasonProjection {
  const { bio, stats } = player;
  const gamesRemaining = Math.max(0, TOTAL_SEASON_GAMES - stats.gamesPlayed);

  // Project stats
  const goals = projectStat(stats.goals, stats.gamesPlayed, gamesRemaining, 0.2);
  const assists = projectStat(stats.assists, stats.gamesPlayed, gamesRemaining, 0.15);
  const points = projectStat(stats.points, stats.gamesPlayed, gamesRemaining, 0.12);
  const shots = projectStat(stats.shots, stats.gamesPlayed, gamesRemaining, 0.1);

  // Calculate award probabilities based on league rank
  const sortedByPoints = [...allPlayers].sort((a, b) => b.stats.points - a.stats.points);
  const sortedByGoals = [...allPlayers].sort((a, b) => b.stats.goals - a.stats.goals);
  const sortedByAssists = [...allPlayers].sort((a, b) => b.stats.assists - a.stats.assists);

  const pointsRank = sortedByPoints.findIndex(p => p.bio.playerId === bio.playerId) + 1;
  const goalsRank = sortedByGoals.findIndex(p => p.bio.playerId === bio.playerId) + 1;
  const assistsRank = sortedByAssists.findIndex(p => p.bio.playerId === bio.playerId) + 1;

  // Award probabilities based on rank (simplified model)
  const calculateAwardProb = (rank: number, spread: number = 5): number => {
    if (rank === 1) return Math.min(45, 30 + Math.random() * 15);
    if (rank <= 3) return Math.max(0, 20 - (rank - 1) * 8 + Math.random() * 5);
    if (rank <= 10) return Math.max(0, 8 - (rank - 3) * 1 + Math.random() * 2);
    return Math.max(0, 2 - (rank - 10) * 0.2);
  };

  // Milestone thresholds - granular for better visualization
  const goalMilestones = [15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70];
  const assistMilestones = [20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85];
  const pointMilestones = [30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140];

  return {
    playerId: bio.playerId,
    season: CURRENT_SEASON,
    gamesRemaining,
    goals,
    assists,
    points,
    shots,
    awardProbabilities: {
      mostPoints: Math.round(calculateAwardProb(pointsRank) * 10) / 10,
      mostGoals: Math.round(calculateAwardProb(goalsRank) * 10) / 10,
      mostAssists: Math.round(calculateAwardProb(assistsRank) * 10) / 10,
    },
    milestoneProbabilities: {
      goals: calculateMilestoneProbabilities(goals, goalMilestones),
      assists: calculateMilestoneProbabilities(assists, assistMilestones),
      points: calculateMilestoneProbabilities(points, pointMilestones),
    },
    distributionSummary: generateDistributionSummary(points),
  };
}

// =============================================================================
// Skill Profile Calculator
// =============================================================================

function calculatePercentileFromStats(
  value: number,
  allValues: number[],
  higherIsBetter: boolean = true
): number {
  const sorted = [...allValues].sort((a, b) => higherIsBetter ? a - b : b - a);
  const rank = sorted.filter(v => higherIsBetter ? v < value : v > value).length;
  return Math.round((rank / sorted.length) * 100);
}

export function generateSkillProfile(
  player: SkaterCard,
  allPlayers: SkaterCard[]
): SkillProfile {
  const { bio, stats } = player;
  const isDefenseman = bio.position === "D";

  // Filter to same position type for fair comparison
  const samePosition = allPlayers.filter(p =>
    isDefenseman ? p.bio.position === "D" : p.bio.position !== "D" && p.bio.position !== "G"
  );

  // Calculate various metrics
  const pointsPerGame = stats.gamesPlayed > 0 ? stats.points / stats.gamesPlayed : 0;
  const goalsPerGame = stats.gamesPlayed > 0 ? stats.goals / stats.gamesPlayed : 0;
  const assistsPerGame = stats.gamesPlayed > 0 ? stats.assists / stats.gamesPlayed : 0;
  const shootingPct = stats.shootingPct || 0;

  // Get all values for percentile calculations
  const allPPG = samePosition.map(p => p.stats.gamesPlayed > 0 ? p.stats.points / p.stats.gamesPlayed : 0);
  const allGPG = samePosition.map(p => p.stats.gamesPlayed > 0 ? p.stats.goals / p.stats.gamesPlayed : 0);
  const allAPG = samePosition.map(p => p.stats.gamesPlayed > 0 ? p.stats.assists / p.stats.gamesPlayed : 0);
  const allPlusMinus = samePosition.map(p => p.stats.plusMinus);
  const allPPGoals = samePosition.map(p => p.stats.powerPlayGoals);
  const allHits = samePosition.map(p => p.stats.hits);
  const allBlocks = samePosition.map(p => p.stats.blockedShots);
  const allShootingPct = samePosition.map(p => p.stats.shootingPct);

  // Calculate percentiles
  const offensivePercentile = calculatePercentileFromStats(pointsPerGame, allPPG);
  const defensivePercentile = isDefenseman
    ? (calculatePercentileFromStats(stats.blockedShots, allBlocks) +
       calculatePercentileFromStats(stats.plusMinus, allPlusMinus)) / 2
    : calculatePercentileFromStats(stats.plusMinus, allPlusMinus);
  const overallPercentile = Math.round((offensivePercentile * 0.6 + defensivePercentile * 0.4));

  const ppOffensePercentile = calculatePercentileFromStats(stats.powerPlayGoals, allPPGoals);
  const finishingPercentile = calculatePercentileFromStats(goalsPerGame, allGPG);
  const playmakingPercentile = calculatePercentileFromStats(assistsPerGame, allAPG);

  // Versatility based on contribution in multiple areas
  const versatilityScore = (
    (stats.goals > 0 ? 20 : 0) +
    (stats.assists > 0 ? 20 : 0) +
    (stats.powerPlayGoals > 0 ? 15 : 0) +
    (stats.hits > 10 ? 15 : stats.hits > 0 ? 10 : 0) +
    (stats.blockedShots > 10 ? 15 : stats.blockedShots > 0 ? 10 : 0) +
    (stats.plusMinus > 0 ? 15 : 0)
  );

  // Generate skill summary
  const generateSummary = (): string => {
    const strengths: string[] = [];
    const weaknesses: string[] = [];

    if (offensivePercentile >= 80) strengths.push("elite offensive production");
    else if (offensivePercentile >= 60) strengths.push("strong offensive ability");
    else if (offensivePercentile < 30) weaknesses.push("limited offensive impact");

    if (defensivePercentile >= 80) strengths.push("excellent defensive play");
    else if (defensivePercentile >= 60) strengths.push("solid defensive responsibility");
    else if (defensivePercentile < 30) weaknesses.push("defensive concerns");

    if (finishingPercentile >= 80) strengths.push("elite finishing ability");
    if (playmakingPercentile >= 80) strengths.push("exceptional playmaking");
    if (ppOffensePercentile >= 70) strengths.push("power play specialist");

    let summary = "";
    if (strengths.length > 0) {
      summary = `Displays ${strengths.join(", ")}.`;
    }
    if (weaknesses.length > 0) {
      summary += ` Areas for improvement: ${weaknesses.join(", ")}.`;
    }

    return summary || "Well-rounded player with balanced contributions across all situations.";
  };

  return {
    playerId: bio.playerId,
    season: CURRENT_SEASON,
    position: bio.position,
    overallRating: createPercentileRating(overallPercentile),
    evenStrength: {
      offensive: createPercentileRating(offensivePercentile),
      defensive: createPercentileRating(defensivePercentile),
      overall: createPercentileRating(Math.round((offensivePercentile + defensivePercentile) / 2)),
    },
    specialTeams: {
      powerPlayOffense: createPercentileRating(ppOffensePercentile),
      penaltyKillDefense: stats.shorthandedGoals > 0 || isDefenseman
        ? createPercentileRating(Math.min(90, defensivePercentile + 10))
        : null,
      combinedPPEV: createPercentileRating(Math.round((ppOffensePercentile + offensivePercentile) / 2)),
    },
    talents: {
      finishing: createPercentileRating(finishingPercentile),
      playmaking: createPercentileRating(playmakingPercentile),
      penaltyImpact: createPercentileRating(Math.max(30, 100 - stats.penaltyMinutes)), // Lower PIM = better
      versatility: createPercentileRating(versatilityScore),
    },
    skillSummary: generateSummary(),
  };
}

// =============================================================================
// On-Ice Impact Calculator
// =============================================================================

export function generateOnIceImpact(
  player: SkaterCard,
  allPlayers: SkaterCard[]
): OnIceImpact {
  const { bio, stats } = player;
  const isDefenseman = bio.position === "D";

  // Filter to same position type
  const samePosition = allPlayers.filter(p =>
    isDefenseman ? p.bio.position === "D" : p.bio.position !== "D" && p.bio.position !== "G"
  );

  // Parse TOI string to minutes
  const parseTOI = (toi: string): number => {
    const [min, sec] = toi.split(":").map(Number);
    return min + (sec || 0) / 60;
  };

  const toiPerGame = parseTOI(stats.timeOnIcePerGame || "0:00");
  const evTOI = toiPerGame * stats.gamesPlayed * 0.75; // Estimate 75% is even strength

  // Calculate metrics based on available stats
  const goalsPerGame = stats.gamesPlayed > 0 ? stats.goals / stats.gamesPlayed : 0;
  const shotsPerGame = stats.gamesPlayed > 0 ? stats.shots / stats.gamesPlayed : 0;

  // Get comparison values
  const allGoalsPerGame = samePosition.map(p => p.stats.gamesPlayed > 0 ? p.stats.goals / p.stats.gamesPlayed : 0);
  const allShotsPerGame = samePosition.map(p => p.stats.gamesPlayed > 0 ? p.stats.shots / p.stats.gamesPlayed : 0);
  const allPlusMinus = samePosition.map(p => p.stats.plusMinus);
  const allBlocks = samePosition.map(p => p.stats.blockedShots);
  const allShootingPct = samePosition.map(p => p.stats.shootingPct || 0);

  // Calculate percentiles
  const goalsForPct = calculatePercentileFromStats(goalsPerGame, allGoalsPerGame);
  const shotsForPct = calculatePercentileFromStats(shotsPerGame, allShotsPerGame);
  const xGoalsForPct = calculatePercentileFromStats(goalsPerGame * 0.9 + shotsPerGame * 0.1,
    allGoalsPerGame.map((g, i) => g * 0.9 + allShotsPerGame[i] * 0.1));
  const corsiFOrPct = calculatePercentileFromStats(shotsPerGame * 1.2, allShotsPerGame.map(s => s * 1.2));
  const shotQualityForPct = calculatePercentileFromStats(stats.shootingPct, allShootingPct);

  // Defensive metrics (inverse relationship for "against" stats)
  const plusMinusPct = calculatePercentileFromStats(stats.plusMinus, allPlusMinus);
  const blocksPct = calculatePercentileFromStats(stats.blockedShots, allBlocks);

  // Goals against is inverse of plus/minus contribution
  const goalsAgainstPct = Math.max(10, Math.min(90, plusMinusPct));
  const shotsAgainstPct = Math.max(20, Math.min(85, 50 + (plusMinusPct - 50) * 0.6));
  const xGoalsAgainstPct = Math.max(15, Math.min(88, 50 + (plusMinusPct - 50) * 0.7));
  const corsiAgainstPct = Math.max(20, Math.min(85, 50 + (plusMinusPct - 50) * 0.5));
  const shotQualityAgainstPct = Math.max(25, Math.min(80, 50 + (plusMinusPct - 50) * 0.4));

  // General metrics
  const netXGoalsPct = Math.round((xGoalsForPct + xGoalsAgainstPct) / 2);
  const netCorsiPct = Math.round((corsiFOrPct + corsiAgainstPct) / 2);
  const finishingPct = calculatePercentileFromStats(stats.shootingPct, allShootingPct);

  // Generate summary
  const generateSummary = (): string => {
    const offRating = Math.round((goalsForPct + shotsForPct + xGoalsForPct) / 3);
    const defRating = Math.round((goalsAgainstPct + xGoalsAgainstPct) / 2);

    if (offRating >= 80 && defRating >= 70) {
      return "Elite two-way impact. Drives positive results at both ends of the ice with exceptional possession metrics.";
    } else if (offRating >= 80) {
      return "Offensive catalyst with elite shot generation and goal-scoring impact. Primary driver of team offense.";
    } else if (defRating >= 80) {
      return "Defensive anchor with strong suppression metrics. Trusted in high-leverage defensive situations.";
    } else if (offRating >= 60 && defRating >= 60) {
      return "Solid two-way contributor with positive impact in all situations. Reliable middle-of-lineup player.";
    } else if (offRating >= 60) {
      return "Offensive-minded player who generates chances. May need sheltered defensive usage.";
    } else if (defRating >= 60) {
      return "Defensively responsible player. Limited offensive upside but provides structure.";
    } else {
      return "Developing player still establishing role. Limited sample or impact to date.";
    }
  };

  return {
    playerId: bio.playerId,
    season: CURRENT_SEASON,
    position: bio.position,
    evTimeOnIce: Math.round(evTOI),
    forMetrics: {
      goals: createImpactMetric(goalsForPct),
      shots: createImpactMetric(shotsForPct),
      expectedGoals: createImpactMetric(xGoalsForPct),
      corsi: createImpactMetric(corsiFOrPct),
      shotQuality: createImpactMetric(shotQualityForPct),
    },
    againstMetrics: {
      goals: createImpactMetric(goalsAgainstPct),
      shots: createImpactMetric(shotsAgainstPct),
      expectedGoals: createImpactMetric(xGoalsAgainstPct),
      corsi: createImpactMetric(corsiAgainstPct),
      shotQuality: createImpactMetric(shotQualityAgainstPct),
    },
    general: {
      netExpectedGoals: createImpactMetric(netXGoalsPct),
      netCorsi: createImpactMetric(netCorsiPct),
      finishing: createImpactMetric(finishingPct),
      shotBlocking: createImpactMetric(blocksPct),
    },
    impactSummary: generateSummary(),
  };
}
