"use client";

import React from "react";
import { TeamCrest } from "@/components/TeamCrest";

type NextGameInfo = { opponent: string; date: string; startTimeEt: string | null };

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

  React.useEffect(() => {
    const fetchNextGames = async () => {
      const url = "https://statsapi.web.nhl.com/api/v1/teams?expand=team.schedule.next";
      try {
        const res = await fetch(url);
        if (!res.ok) return;
        const data = await res.json();
        const map: Record<string, NextGameInfo> = {};
        const formatEt = (iso: string | undefined) => {
          if (!iso) return null;
          const dt = new Date(iso);
          return new Intl.DateTimeFormat("en-US", {
            timeZone: "America/New_York",
            hour: "numeric",
            minute: "2-digit",
          }).format(dt);
        };
        data?.teams?.forEach((team: any) => {
          const abbr = team?.abbreviation;
          const dates = team?.nextGameSchedule?.dates;
          if (!abbr || !dates || !dates.length) return;
          const game = dates[0]?.games?.[0];
          if (!game) return;
          const home = game?.teams?.home?.team?.abbreviation;
          const away = game?.teams?.away?.team?.abbreviation;
          const opponent = home === abbr ? away : home;
          const date = dates[0]?.date;
          const startTimeEt = formatEt(game?.gameDate);
          if (opponent) {
            map[abbr] = { opponent, date, startTimeEt };
          }
        });
        if (Object.keys(map).length) {
          setNextGames(map);
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
    const overlayProb = row.overlay ? formatPct(row.overlay.avgProb) : formatPct(row.pointPctg ?? 0.5);
    const next = nextGames[row.abbrev];
    const nextDisplay = next
      ? `${next.opponent} (${next.date}${next.startTimeEt ? ` · ${next.startTimeEt} ET` : ""})`
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
        <span>Model Win%</span>
        <span>Next</span>
      </div>
      {rows.map(renderRow)}
    </div>
  );
}
