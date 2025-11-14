import { NextResponse } from "next/server";
import { getGoaliePulse, getPredictionsPayload } from "@/lib/data";
import type { GoalieMatchup } from "@/types/goalie";

export const dynamic = "force-dynamic";

export async function GET() {
  const payload = getPredictionsPayload();
  const goalies = getGoaliePulse();
  const matchupMap = new Map<string, GoalieMatchup>(goalies.tonight.games.map((game) => [String(game.gameId), game]));
  const enrichedGames = payload.games.map((game) => {
    const key = String(game.id ?? "");
    const matchup = matchupMap.get(key);
    if (!matchup) {
      return game;
    }
    return {
      ...game,
      projectedGoalies: {
        home: simplifyStarter(matchup.home),
        away: simplifyStarter(matchup.away),
        startTimeEt: matchup.startTimeEt,
        startTimeUtc: matchup.startTimeUtc,
      },
    };
  });

  return NextResponse.json(
    {
      ...payload,
      games: enrichedGames,
      goalieMetadata: {
        updatedAt: goalies.updatedAt ?? null,
        projectedGames: goalies.tonight.games.length,
      },
    },
    {
      headers: {
        "Cache-Control": "public, max-age=60, stale-while-revalidate=300",
      },
    },
  );
}

function simplifyStarter(starter: GoalieMatchup["home"] | null) {
  if (!starter) return null;
  return {
    name: starter.name,
    team: starter.team,
    startLikelihood: starter.startLikelihood,
    restDays: starter.restDays,
    record: starter.record,
  };
}
