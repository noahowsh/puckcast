import { NextResponse } from "next/server";
import insightsData from "@/data/modelInsights.json";

export const dynamic = "force-dynamic";

/**
 * GET /api/insights
 * Returns model performance insights and analytics
 *
 * Query params:
 * - metric: Specific metric to return (overall, strategies, confidenceBuckets, etc.)
 */
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const metric = searchParams.get("metric");

    // If specific metric requested, return just that
    if (metric && metric in insightsData) {
      return NextResponse.json({
        generatedAt: insightsData.generatedAt,
        [metric]: insightsData[metric as keyof typeof insightsData],
      });
    }

    // Return all insights
    return NextResponse.json(insightsData);
  } catch (error) {
    console.error("API /insights error:", error);
    return NextResponse.json({ error: "Failed to fetch insights" }, { status: 500 });
  }
}
