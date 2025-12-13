import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProbabilityBar } from "./ProbabilityBar";

describe("ProbabilityBar", () => {
  const defaultProps = {
    homeProb: 0.65,
    awayProb: 0.35,
    homeTeam: "TOR",
    awayTeam: "MTL",
  };

  it("renders team names and percentages", () => {
    render(<ProbabilityBar {...defaultProps} />);
    expect(screen.getByText("TOR 65.0%")).toBeInTheDocument();
    expect(screen.getByText("MTL 35.0%")).toBeInTheDocument();
  });

  it("hides labels when showLabels is false", () => {
    render(<ProbabilityBar {...defaultProps} showLabels={false} />);
    expect(screen.queryByText("TOR 65.0%")).not.toBeInTheDocument();
    expect(screen.queryByText("MTL 35.0%")).not.toBeInTheDocument();
  });

  it("sets correct width for probability segments", () => {
    const { container } = render(<ProbabilityBar {...defaultProps} />);
    const segments = container.querySelectorAll(".prob-bar-segment");

    expect(segments[0]).toHaveStyle({ width: "65%" });
    expect(segments[1]).toHaveStyle({ width: "35%" });
  });

  it("applies correct height classes", () => {
    const { container: sm } = render(<ProbabilityBar {...defaultProps} height="sm" />);
    expect(sm.querySelector(".prob-bar")).toHaveClass("h-2");

    const { container: md } = render(<ProbabilityBar {...defaultProps} height="md" />);
    expect(md.querySelector(".prob-bar")).toHaveClass("h-3");

    const { container: lg } = render(<ProbabilityBar {...defaultProps} height="lg" />);
    expect(lg.querySelector(".prob-bar")).toHaveClass("h-4");
  });

  it("handles edge case probabilities", () => {
    render(<ProbabilityBar homeProb={0.99} awayProb={0.01} homeTeam="COL" awayTeam="ARI" />);
    expect(screen.getByText("COL 99.0%")).toBeInTheDocument();
    expect(screen.getByText("ARI 1.0%")).toBeInTheDocument();
  });

  it("handles 50/50 probabilities", () => {
    render(<ProbabilityBar homeProb={0.5} awayProb={0.5} homeTeam="BOS" awayTeam="NYR" />);
    expect(screen.getByText("BOS 50.0%")).toBeInTheDocument();
    expect(screen.getByText("NYR 50.0%")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(<ProbabilityBar {...defaultProps} className="my-custom-class" />);
    expect(container.firstChild).toHaveClass("my-custom-class");
  });
});
