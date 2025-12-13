import { NextResponse } from "next/server";
import { getGoaliePulse } from "@/lib/data";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const payload = getGoaliePulse();
    return NextResponse.json(payload, {
      headers: {
        "Cache-Control": "public, max-age=300, stale-while-revalidate=900",
      },
    });
  } catch (error) {
    console.error("API /goalies error:", error);
    return NextResponse.json({ error: "Failed to fetch goalie data" }, { status: 500 });
  }
}
