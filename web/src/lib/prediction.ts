export type GradeDetail = {
  label: string;
  description: string;
};

const tierLabelPattern = /([ABC][+-]?)(?:-|\s*)tier/gi;

export function getPredictionGrade(edge: number): GradeDetail {
  const pts = Math.abs(edge) * 100;
  if (pts >= 25) return { label: "A+", description: "Elite confidence (≥25 pts edge)" };
  if (pts >= 20) return { label: "A", description: "Strong confidence (20-25 pts edge)" };
  if (pts >= 15) return { label: "B+", description: "Good confidence (15-20 pts edge)" };
  if (pts >= 10) return { label: "B", description: "Medium confidence (10-15 pts edge)" };
  if (pts >= 5) return { label: "C+", description: "Weak confidence (5-10 pts edge)" };
  return { label: "C", description: "Coin flip (0-5 pts edge)" };
}

export function normalizeSummaryWithGrade(summary: string, gradeLabel: string): string {
  if (!summary) return summary;
  return summary.replace(tierLabelPattern, `${gradeLabel} tier`);
}
