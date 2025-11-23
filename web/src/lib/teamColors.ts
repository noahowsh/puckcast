const TEAM_COLORS: Record<
  string,
  {
    primary: string;
    secondary?: string;
  }
> = {
  ANA: { primary: "#F47A38", secondary: "#B9975B" },
  ARI: { primary: "#8C2633", secondary: "#E2D6B5" },
  BOS: { primary: "#FFB81C", secondary: "#000000" },
  BUF: { primary: "#003087", secondary: "#FDBB2F" },
  CAR: { primary: "#CC0000", secondary: "#000000" },
  CBJ: { primary: "#002654", secondary: "#CE1126" },
  CGY: { primary: "#C8102E", secondary: "#F1BE48" },
  CHI: { primary: "#CF0A2C", secondary: "#000000" },
  COL: { primary: "#6F263D", secondary: "#236192" },
  DAL: { primary: "#006847", secondary: "#8F8F8C" },
  DET: { primary: "#CE1126", secondary: "#FFFFFF" },
  EDM: { primary: "#041E42", secondary: "#FF4C00" },
  FLA: { primary: "#041E42", secondary: "#C8102E" },
  LAK: { primary: "#111111", secondary: "#A2AAAD" },
  MIN: { primary: "#154734", secondary: "#A6192E" },
  MTL: { primary: "#AF1E2D", secondary: "#001E62" },
  NJD: { primary: "#CE1126", secondary: "#000000" },
  NSH: { primary: "#FFB81C", secondary: "#041E42" },
  NYI: { primary: "#00539B", secondary: "#F47D30" },
  NYR: { primary: "#0038A8", secondary: "#CE1126" },
  OTT: { primary: "#C8102E", secondary: "#C8B07E" },
  PHI: { primary: "#F74902", secondary: "#000000" },
  PIT: { primary: "#FFB81C", secondary: "#000000" },
  SEA: { primary: "#001628", secondary: "#99D9D9" },
  SJS: { primary: "#006272", secondary: "#EA7200" },
  STL: { primary: "#002F87", secondary: "#FCB514" },
  TBL: { primary: "#002868", secondary: "#002868" },
  TOR: { primary: "#00205B", secondary: "#FFFFFF" },
  VAN: { primary: "#00205B", secondary: "#00843D" },
  VGK: { primary: "#B4975A", secondary: "#333F42" },
  WPG: { primary: "#041E42", secondary: "#AC162C" },
  WSH: { primary: "#041E42", secondary: "#C8102E" },
};

const fallbackGradient = "linear-gradient(145deg, rgba(241, 217, 166, 0.2), rgba(126, 227, 255, 0.14))";
const fallbackBorder = "rgba(126, 227, 255, 0.55)";

const hexToRgba = (hex: string, alpha = 1) => {
  const trimmed = hex.replace("#", "");
  const bigint = parseInt(trimmed, 16);
  const r = (bigint >> 16) & 255;
  const g = (bigint >> 8) & 255;
  const b = bigint & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

const luma = (hex: string) => {
  const trimmed = hex.replace("#", "");
  const bigint = parseInt(trimmed, 16);
  const r = (bigint >> 16) & 255;
  const g = (bigint >> 8) & 255;
  const b = bigint & 255;
  return 0.299 * r + 0.587 * g + 0.114 * b;
};

export function teamGradient(abbrev: string) {
  const safe = abbrev?.toUpperCase?.() ?? "";
  const colors = TEAM_COLORS[safe];
  if (!colors) return fallbackGradient;
  const primaryLuma = luma(colors.primary);
  // Bright colors (yellows/oranges) overpower; very dark colors disappear. Bias alpha by perceived brightness.
  let primaryAlpha = primaryLuma > 190 ? 0.12 : primaryLuma < 70 ? 0.24 : 0.20;
  let secondaryAlpha = primaryLuma > 190 ? 0.08 : primaryLuma < 70 ? 0.18 : 0.15;

  // Improve contrast for deep blue logos that disappear on dark backgrounds
  if (["TBL", "TOR", "VAN"].includes(safe)) {
    primaryAlpha = 0.16;
    secondaryAlpha = 0.12;
  }
  const primary = hexToRgba(colors.primary, primaryAlpha);
  const secondary = hexToRgba(colors.secondary ?? colors.primary, secondaryAlpha);
  return `linear-gradient(145deg, ${primary}, ${secondary})`;
}

export function teamBorderColor(abbrev: string) {
  const colors = TEAM_COLORS[abbrev?.toUpperCase?.() ?? ""];
  if (!colors) return fallbackBorder;
  const alpha = luma(colors.primary) > 190 ? 0.35 : luma(colors.primary) < 70 ? 0.55 : 0.5;
  return hexToRgba(colors.primary, alpha);
}

export function teamLogoUrl(abbrev: string) {
  const safe = abbrev?.toUpperCase?.() ?? "";
  return `https://assets.nhle.com/logos/nhl/svg/${safe}_light.svg`;
}
