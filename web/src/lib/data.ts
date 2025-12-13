// Simple error logging (Sentry integration can be added later)
const captureException = (error: unknown) => {
  console.error("Error:", error);
};

import goaliePulseRaw from "@/data/goaliePulse.json";
import predictionsRaw from "@/data/todaysPredictions.json";
import insightsRaw from "@/data/modelInsights.json";
import startingGoaliesRaw from "@/data/startingGoalies.json";
import playerInjuriesRaw from "@/data/playerInjuries.json";
import type { Prediction, PredictionsPayload, PlayerInjuriesPayload, StartingGoaliesPayload } from "@/types/prediction";
import type { GoaliePulse } from "@/types/goalie";
import type { ModelInsights } from "@/types/insights";

export function getPredictionsPayload(): PredictionsPayload {
  return predictionsRaw as PredictionsPayload;
}

export function getGoaliePulse(): GoaliePulse {
  try {
    return goaliePulseRaw as GoaliePulse;
  } catch (error) {
    captureException(error);
    throw error;
  }
}

export function getModelInsights(): ModelInsights {
  try {
    return insightsRaw as ModelInsights;
  } catch (error) {
    captureException(error);
    throw error;
  }
}

export function getStartingGoalies(): StartingGoaliesPayload {
  try {
    return startingGoaliesRaw as StartingGoaliesPayload;
  } catch (error) {
    captureException(error);
    throw error;
  }
}

export function getPlayerInjuries(): PlayerInjuriesPayload {
  try {
    return playerInjuriesRaw as PlayerInjuriesPayload;
  } catch (error) {
    captureException(error);
    throw error;
  }
}

export function selectCurrentSlate(games: Prediction[]): Prediction[] {
  if (!games.length) {
    return [];
  }

  const dates = games
    .map((game) => game.gameDate)
    .filter((date): date is string => Boolean(date))
    .sort();

  const earliestDate = dates[0];
  if (!earliestDate) {
    return games;
  }

  return games.filter((game) => game.gameDate === earliestDate);
}
