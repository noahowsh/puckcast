import { NextResponse } from "next/server";
import { fetchNextGamesMap } from "@/lib/nextGames";
import { getCurrentStandings } from "@/lib/current";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const teams = getCurrentStandings().map((t) => t.abbrev);
    const map = await fetchNextGamesMap(teams, 14);
    return NextResponse.json({ nextGames: map });
  } catch (error) {
    console.error("API /next-games error:", error);
    return NextResponse.json({ error: "Failed to fetch next games" }, { status: 500 });
  }
}
