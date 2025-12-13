import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ConfidenceBadge, getConfidenceColor } from "./ConfidenceBadge";

describe("ConfidenceBadge", () => {
  it("renders the grade text", () => {
    render(<ConfidenceBadge grade="A+" />);
    expect(screen.getByText("A+")).toBeInTheDocument();
  });

  it("renders with label when showLabel is true", () => {
    render(<ConfidenceBadge grade="A" showLabel />);
    expect(screen.getByText("Grade A")).toBeInTheDocument();
  });

  it("applies correct badge class for A grade", () => {
    const { container } = render(<ConfidenceBadge grade="A" />);
    const badge = container.querySelector(".badge");
    expect(badge).toHaveClass("badge-confidence-s");
  });

  it("applies correct badge class for B grade", () => {
    const { container } = render(<ConfidenceBadge grade="B" />);
    const badge = container.querySelector(".badge");
    expect(badge).toHaveClass("badge-confidence-a");
  });

  it("applies correct badge class for C grade", () => {
    const { container } = render(<ConfidenceBadge grade="C" />);
    const badge = container.querySelector(".badge");
    expect(badge).toHaveClass("badge-confidence-b");
  });

  it("handles grade with plus/minus modifiers", () => {
    const { container } = render(<ConfidenceBadge grade="A+" />);
    const badge = container.querySelector(".badge");
    expect(badge).toHaveClass("badge-confidence-s");
  });

  it("applies correct size classes", () => {
    const { container: sm } = render(<ConfidenceBadge grade="A" size="sm" />);
    expect(sm.querySelector(".badge")).toHaveClass("text-xs");

    const { container: md } = render(<ConfidenceBadge grade="A" size="md" />);
    expect(md.querySelector(".badge")).toHaveClass("text-sm");

    const { container: lg } = render(<ConfidenceBadge grade="A" size="lg" />);
    expect(lg.querySelector(".badge")).toHaveClass("text-base");
  });
});

describe("getConfidenceColor", () => {
  it("returns correct color for A grade", () => {
    expect(getConfidenceColor("A")).toBe("var(--confidence-s)");
    expect(getConfidenceColor("A+")).toBe("var(--confidence-s)");
    expect(getConfidenceColor("A-")).toBe("var(--confidence-s)");
  });

  it("returns correct color for B grade", () => {
    expect(getConfidenceColor("B")).toBe("var(--confidence-a)");
    expect(getConfidenceColor("B+")).toBe("var(--confidence-a)");
  });

  it("returns correct color for C grade", () => {
    expect(getConfidenceColor("C")).toBe("var(--confidence-b)");
    expect(getConfidenceColor("C+")).toBe("var(--confidence-b)");
  });

  it("returns fallback color for unknown grade", () => {
    expect(getConfidenceColor("D")).toBe("var(--confidence-c)");
    expect(getConfidenceColor("F")).toBe("var(--confidence-c)");
  });
});
