import { describe, it, expect } from "vitest";
import { selectCurrentSlate } from "./data";
import type { Prediction } from "@/types/prediction";

describe("selectCurrentSlate", () => {
  const createGame = (gameDate: string, id: string): Prediction => ({
    id,
    gameDate,
    startTimeEt: "7:00 PM ET",
    startTimeUtc: "",
    homeTeam: { name: "Home", abbrev: "HOM" },
    awayTeam: { name: "Away", abbrev: "AWY" },
    homeWinProb: 0.55,
    awayWinProb: 0.45,
    confidenceScore: 0.1,
    confidenceGrade: "C",
    edge: 0.05,
    summary: "Test game",
    modelFavorite: "home",
    venue: "Arena",
    season: "20252026",
  });

  it("returns empty array for empty input", () => {
    expect(selectCurrentSlate([])).toEqual([]);
  });

  it("returns all games if they have the same date", () => {
    const games = [
      createGame("2025-01-15", "1"),
      createGame("2025-01-15", "2"),
      createGame("2025-01-15", "3"),
    ];
    const result = selectCurrentSlate(games);
    expect(result).toHaveLength(3);
  });

  it("returns only games from the earliest date", () => {
    const games = [
      createGame("2025-01-16", "1"),
      createGame("2025-01-15", "2"),
      createGame("2025-01-17", "3"),
      createGame("2025-01-15", "4"),
    ];
    const result = selectCurrentSlate(games);
    expect(result).toHaveLength(2);
    expect(result.every((g) => g.gameDate === "2025-01-15")).toBe(true);
  });

  it("handles games with missing dates", () => {
    const games = [
      createGame("2025-01-15", "1"),
      { ...createGame("", "2"), gameDate: undefined } as unknown as Prediction,
      createGame("2025-01-15", "3"),
    ];
    const result = selectCurrentSlate(games);
    expect(result).toHaveLength(2);
    expect(result.every((g) => g.gameDate === "2025-01-15")).toBe(true);
  });

  it("returns all games if all dates are missing", () => {
    const games = [
      { ...createGame("", "1"), gameDate: undefined },
      { ...createGame("", "2"), gameDate: undefined },
    ] as unknown as Prediction[];
    const result = selectCurrentSlate(games);
    expect(result).toHaveLength(2);
  });

  it("handles single game", () => {
    const games = [createGame("2025-01-15", "1")];
    const result = selectCurrentSlate(games);
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe("1");
  });
});
