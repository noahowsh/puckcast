"use client";

import React from "react";
import { TeamCrest } from "@/components/TeamCrest";
import type { NextGameInfo } from "@/lib/nextGames";

export type LeaderboardRow = {
  powerRank: number;
  standingsRank: number;
  movement: number;
  team: string;
  abbrev: string;
  record: string;
  points: number;
  goalDifferential: number;
  pointPctg: number;
  powerScore: number;
  overlay?: { avgProb: number };
};

function formatPct(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

const nameFallback: Record<string, string> = {};

export function PowerBoardClient({ rows, initialNextGames }: { rows: LeaderboardRow[]; initialNextGames?: Record<string, NextGameInfo> }) {
  const [nextGames, setNextGames] = React.useState<Record<string, NextGameInfo>>(initialNextGames || {});

  const formatDate = (date?: string | null) => {
    if (!date) return null;
    const dt = new Date(date);
    if (Number.isNaN(dt.getTime())) return date;
    return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" }).format(dt);
  };

  const formatTimeEt = (time?: string | null) => {
    if (!time) return null;
    // Ensure single ET suffix
    const trimmed = time.replace(/\s*ET$/i, "").trim();
    return `${trimmed} ET`;
  };

  React.useEffect(() => {
    const fetchNextGames = async () => {
      const url = "/api/next-games";
      try {
        const res = await fetch(url);
        if (!res.ok) return;
        const data = await res.json();
        const map: Record<string, NextGameInfo> = {};
        const incoming = data?.nextGames || {};
        if (Object.keys(incoming).length) {
          setNextGames(incoming);
        }
      } catch (err) {
        console.warn("schedule fetch failed", err);
      }
    };
    fetchNextGames();
  }, []);

  const renderRow = (row: LeaderboardRow) => {
    const movementDisplay = row.movement === 0 ? "Even" : row.movement > 0 ? `+${row.movement}` : row.movement;
    const movementTone = row.movement > 0 ? "movement--positive" : row.movement < 0 ? "movement--negative" : "movement--neutral";
    const overlayProb = row.overlay && row.overlay.avgProb ? formatPct(row.overlay.avgProb) : "—";
    const next = nextGames[row.abbrev];
    const nextDate = formatDate(next?.date);
    const nextTime = formatTimeEt(next?.startTimeEt);
    const nextDisplay = next
      ? `${next.opponent}${nextDate || nextTime ? " (" : ""}${[nextDate, nextTime].filter(Boolean).join(" · ")}${nextDate || nextTime ? ")" : ""}`
      : "Next game TBA";

    return (
      <div className="power-board__row" key={row.abbrev}>
        <div className="rank-chip">#{row.powerRank}</div>
        <div className="power-team">
          <TeamCrest abbrev={row.abbrev} />
          <div>
            <p className="power-name">{row.team}</p>
            <p className="micro-label">Standings #{row.standingsRank}</p>
          </div>
        </div>
        <span className={`movement movement--pillless ${movementTone}`}>{movementDisplay}</span>
        <span className="power-data">{row.record}</span>
        <span className="power-data">{formatPct(row.pointPctg)}</span>
        <span className={`power-data ${row.goalDifferential >= 0 ? "text-up" : "text-down"}`}>
          {row.goalDifferential >= 0 ? "+" : ""}
          {row.goalDifferential}
        </span>
        <span className="power-data">{overlayProb}</span>
        <span className="power-data">{nextDisplay}</span>
      </div>
    );
  };

  return (
    <div className="power-board">
      <div className="power-board__head">
        <span>#</span>
        <span>Team</span>
        <span>Movement</span>
        <span>Record</span>
        <span>Point %</span>
        <span>Goal Diff</span>
        <span>Strength</span>
        <span>Next</span>
      </div>
      {rows.map(renderRow)}
    </div>
  );
}
