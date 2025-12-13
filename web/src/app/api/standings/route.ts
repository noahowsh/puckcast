import { NextResponse } from "next/server";
import standingsData from "@/data/currentStandings.json";

export const dynamic = "force-dynamic";

/**
 * GET /api/standings
 * Returns current NHL standings
 *
 * Query params:
 * - conference: Filter by conference (East, West)
 * - limit: Limit number of teams returned
 */
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = searchParams.get("limit");

    let teams = standingsData.teams;

    // Filter by conference (if we have that data)
    // Note: Current standings.json doesn't have conference, but we can add it

    // Limit results
    if (limit) {
      const limitNum = parseInt(limit, 10);
      if (!isNaN(limitNum) && limitNum > 0) {
        teams = teams.slice(0, limitNum);
      }
    }

    return NextResponse.json({
      generatedAt: standingsData.generatedAt,
      seasonId: standingsData.seasonId,
      count: teams.length,
      teams: teams,
    });
  } catch (error) {
    console.error("API /standings error:", error);
    return NextResponse.json({ error: "Failed to fetch standings" }, { status: 500 });
  }
}
