import { NextResponse } from "next/server";
import { buildStatusSnapshot } from "@/lib/status";

export const dynamic = "force-dynamic";

export function GET() {
  const snapshot = buildStatusSnapshot();
  return NextResponse.json(snapshot, {
    headers: {
      "Cache-Control": "public, max-age=30, stale-while-revalidate=120",
    },
  });
}
