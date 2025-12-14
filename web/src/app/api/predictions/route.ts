import { NextResponse } from "next/server";
import { getGoaliePulse, getPredictionsPayload, getPlayerInjuries, getStartingGoalies } from "@/lib/data";
import { getPlayerHubContext } from "@/lib/playerHub";
import type { GoalieMatchup } from "@/types/goalie";
import type { PlayerInjuriesPayload, Prediction, SpecialTeamsSplit, StartingGoaliesPayload } from "@/types/prediction";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const payload = getPredictionsPayload();
    const goalies = getGoaliePulse();
    const startingGoalies = getStartingGoalies();
    const playerInjuries = getPlayerInjuries();
    const playerHub = getPlayerHubContext();
    const tonightGames = goalies.tonight?.games ?? [];
    const matchupMap = new Map<string, GoalieMatchup>(tonightGames.map((game) => [String(game.gameId), game]));
    const specialTeams = playerHub.specialTeams?.teams ?? {};
    const enrichedGames = payload.games.map((game) =>
      enhanceGame(game, matchupMap, specialTeams, startingGoalies, playerInjuries),
    );

    return NextResponse.json(
      {
        ...payload,
        games: enrichedGames,
        goalieMetadata: { updatedAt: goalies.updatedAt, projectedGames: tonightGames.length },
        specialTeams: playerHub.specialTeams ?? null,
        goalieShots: playerHub.goalieShotProfiles ?? [],
      },
      {
        headers: {
          "Cache-Control": "public, max-age=60, stale-while-revalidate=300",
        },
      },
    );
  } catch (error) {
    console.error("API /predictions error:", error);
    return NextResponse.json({ error: "Failed to fetch predictions" }, { status: 500 });
  }
}

function formatStarter(starter: GoalieMatchup["home"] | null) {
  if (!starter) return null;
  return {
    name: starter.name,
    team: starter.team,
    startLikelihood: starter.startLikelihood,
    restDays: starter.restDays,
    record: starter.record,
  };
}

function enhanceGame(
  game: Prediction,
  matchupMap: Map<string, GoalieMatchup>,
  specialTeams: Record<string, { powerPlayPct?: number | null; penaltyKillPct?: number | null }>,
  startingGoalies: StartingGoaliesPayload,
  playerInjuries: PlayerInjuriesPayload,
) {
  const match = matchupMap.get(String(game.id ?? ""));
  const enriched: Prediction = match
    ? {
        ...game,
        projectedGoalies: {
          home: formatStarter(match.home),
          away: formatStarter(match.away),
          startTimeEt: match.startTimeEt,
          startTimeUtc: match.startTimeUtc,
        },
      }
    : game;
  const homeKey = game.homeTeam.abbrev.toUpperCase();
  const awayKey = game.awayTeam.abbrev.toUpperCase();
  const homeStats = specialTeams[homeKey];
  const awayStats = specialTeams[awayKey];
  const startingTeams = startingGoalies.teams ?? {};
  const injuriesMap = playerInjuries.teams ?? {};
  const dayOfInfo = {
    homeGoalie: startingTeams[homeKey] ?? null,
    awayGoalie: startingTeams[awayKey] ?? null,
    homeInjuryCount: injuriesMap[homeKey]?.injuries?.length ?? 0,
    awayInjuryCount: injuriesMap[awayKey]?.injuries?.length ?? 0,
  };
  if (!game.specialTeams && homeStats && awayStats) {
    enriched.specialTeams = {
      home: buildSplit(homeStats.powerPlayPct, awayStats.penaltyKillPct),
      away: buildSplit(awayStats.powerPlayPct, homeStats.penaltyKillPct),
    };
  }
  enriched.dayOfInfo = dayOfInfo;
  return enriched;
}

function buildSplit(pp?: number | null, pk?: number | null): SpecialTeamsSplit {
  return {
    powerPlayPct: pp ?? null,
    opponentPenaltyKillPct: pk ?? null,
    diff: typeof pp === "number" && typeof pk === "number" ? pp - pk : null,
  };
}
