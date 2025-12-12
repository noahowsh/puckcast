// Starting Goalie Display Components
// Visual components for showing starting goalie intelligence

import Link from "next/link";
import type {
  StartingGoalieInfo,
  GameGoalieReport,
  ConfidenceLevel,
} from "@/types/startingGoalie";
import { getConfidenceColor, formatConfidence } from "@/types/startingGoalie";

// =============================================================================
// Status Badge
// =============================================================================

function StatusBadge({ status, confidence }: { status: string; confidence: number }) {
  const color = getConfidenceColor(confidence);
  const label = status.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());

  return (
    <span style={{
      display: "inline-flex",
      alignItems: "center",
      gap: "0.35rem",
      padding: "0.25rem 0.5rem",
      borderRadius: "0.375rem",
      fontSize: "0.7rem",
      fontWeight: 600,
      textTransform: "uppercase",
      background: `${color}20`,
      color: color,
      border: `1px solid ${color}40`,
    }}>
      <span style={{
        width: "6px",
        height: "6px",
        borderRadius: "50%",
        background: color,
      }} />
      {label}
    </span>
  );
}

// =============================================================================
// Confidence Meter
// =============================================================================

function ConfidenceMeter({ confidence, showLabel = true }: { confidence: number; showLabel?: boolean }) {
  const color = getConfidenceColor(confidence);
  const pct = Math.round(confidence * 100);

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
      <div style={{
        flex: 1,
        height: "6px",
        background: "rgba(255,255,255,0.1)",
        borderRadius: "3px",
        overflow: "hidden",
      }}>
        <div style={{
          width: `${pct}%`,
          height: "100%",
          background: color,
          borderRadius: "3px",
          transition: "width 0.3s ease",
        }} />
      </div>
      {showLabel && (
        <span style={{ fontSize: "0.75rem", fontWeight: 600, color, minWidth: "3rem" }}>
          {pct}%
        </span>
      )}
    </div>
  );
}

// =============================================================================
// Goalie Card - Compact View
// =============================================================================

export function GoalieStarterCard({ goalie, isHome }: { goalie: StartingGoalieInfo; isHome: boolean }) {
  const hasGoalie = goalie.playerName !== null;

  return (
    <div className="card" style={{
      padding: "1rem",
      borderLeft: `3px solid ${getConfidenceColor(goalie.confidence)}`,
    }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: "0.75rem" }}>
        <div>
          <p style={{ fontSize: "0.65rem", color: "var(--text-tertiary)", textTransform: "uppercase", marginBottom: "0.25rem" }}>
            {isHome ? "Home" : "Away"} Starter
          </p>
          <p style={{ fontSize: "1rem", fontWeight: 600, color: "white" }}>
            {hasGoalie ? goalie.playerName : "TBD"}
          </p>
        </div>
        <StatusBadge status={goalie.status} confidence={goalie.confidence} />
      </div>

      {hasGoalie && (
        <>
          <ConfidenceMeter confidence={goalie.confidence} />

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.5rem", marginTop: "0.75rem" }}>
            {goalie.gsaRolling !== null && (
              <div style={{ textAlign: "center", padding: "0.35rem", background: "rgba(255,255,255,0.03)", borderRadius: "0.375rem" }}>
                <p style={{ fontSize: "0.9rem", fontWeight: 700, color: goalie.gsaRolling > 0 ? "#10b981" : "#f59e0b" }}>
                  {goalie.gsaRolling > 0 ? "+" : ""}{goalie.gsaRolling.toFixed(1)}
                </p>
                <p style={{ fontSize: "0.55rem", color: "var(--text-tertiary)", textTransform: "uppercase" }}>GSA</p>
              </div>
            )}
            {goalie.restDays !== null && (
              <div style={{ textAlign: "center", padding: "0.35rem", background: "rgba(255,255,255,0.03)", borderRadius: "0.375rem" }}>
                <p style={{ fontSize: "0.9rem", fontWeight: 700, color: goalie.restDays >= 2 ? "#10b981" : goalie.restDays === 1 ? "#f59e0b" : "#ef4444" }}>
                  {goalie.restDays}
                </p>
                <p style={{ fontSize: "0.55rem", color: "var(--text-tertiary)", textTransform: "uppercase" }}>Rest</p>
              </div>
            )}
            <div style={{ textAlign: "center", padding: "0.35rem", background: "rgba(255,255,255,0.03)", borderRadius: "0.375rem" }}>
              <p style={{
                fontSize: "0.7rem",
                fontWeight: 600,
                color: goalie.trend === "surging" ? "#10b981"
                  : goalie.trend === "steady" ? "#3b82f6"
                  : goalie.trend === "cooling" ? "#f59e0b"
                  : "var(--text-tertiary)",
              }}>
                {goalie.trend.charAt(0).toUpperCase() + goalie.trend.slice(1)}
              </p>
              <p style={{ fontSize: "0.55rem", color: "var(--text-tertiary)", textTransform: "uppercase" }}>Trend</p>
            </div>
          </div>

          <div style={{ marginTop: "0.75rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "0.65rem", color: "var(--text-tertiary)" }}>
              Source: {goalie.source.replace(/_/g, " ")}
              {goalie.alternateSource && ` + ${goalie.alternateSource.replace(/_/g, " ")}`}
            </span>
          </div>
        </>
      )}

      {!hasGoalie && (
        <div style={{ marginTop: "0.5rem" }}>
          <p style={{ fontSize: "0.8rem", color: "var(--text-tertiary)" }}>
            Starter not yet announced. Check back closer to game time.
          </p>
          <p style={{ fontSize: "0.7rem", color: "var(--text-tertiary)", marginTop: "0.35rem" }}>
            Typical confirmation: 10:00 AM ET (morning skate)
          </p>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Game Goalie Matchup
// =============================================================================

export function GoalieMatchupCard({ report }: { report: GameGoalieReport }) {
  const advantageTeam = report.homeGoalieAdvantage > 0 ? "home" : report.homeGoalieAdvantage < 0 ? "away" : null;

  return (
    <div className="card" style={{ padding: "1.25rem" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
        <h3 style={{ fontSize: "0.9rem", fontWeight: 600, color: "white" }}>Goalie Matchup</h3>
        {report.bothConfirmed ? (
          <span style={{
            padding: "0.2rem 0.5rem",
            borderRadius: "0.25rem",
            fontSize: "0.65rem",
            fontWeight: 600,
            background: "#10b98120",
            color: "#10b981",
          }}>Both Confirmed</span>
        ) : (
          <span style={{
            padding: "0.2rem 0.5rem",
            borderRadius: "0.25rem",
            fontSize: "0.65rem",
            fontWeight: 600,
            background: "#f59e0b20",
            color: "#f59e0b",
          }}>Pending Confirmation</span>
        )}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr", gap: "1rem", alignItems: "center" }}>
        {/* Home Goalie */}
        <div style={{ textAlign: "center" }}>
          <p style={{ fontSize: "0.65rem", color: "var(--text-tertiary)", textTransform: "uppercase", marginBottom: "0.25rem" }}>
            {report.homeTeam}
          </p>
          <p style={{ fontSize: "1rem", fontWeight: 600, color: "white", marginBottom: "0.35rem" }}>
            {report.homeGoalie.playerName || "TBD"}
          </p>
          <StatusBadge status={report.homeGoalie.status} confidence={report.homeGoalie.confidence} />
          {report.homeGoalie.gsaRolling !== null && (
            <p style={{
              marginTop: "0.5rem",
              fontSize: "0.85rem",
              fontWeight: 600,
              color: report.homeGoalie.gsaRolling > 0 ? "#10b981" : "#f59e0b",
            }}>
              GSA: {report.homeGoalie.gsaRolling > 0 ? "+" : ""}{report.homeGoalie.gsaRolling.toFixed(1)}
            </p>
          )}
        </div>

        {/* VS / Advantage */}
        <div style={{ textAlign: "center" }}>
          <p style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--text-tertiary)", marginBottom: "0.5rem" }}>VS</p>
          {advantageTeam && Math.abs(report.homeGoalieAdvantage) > 0.5 && (
            <div style={{
              padding: "0.35rem 0.5rem",
              borderRadius: "0.375rem",
              background: advantageTeam === "home" ? "#10b98120" : "#3b82f620",
              fontSize: "0.7rem",
              fontWeight: 600,
              color: advantageTeam === "home" ? "#10b981" : "#3b82f6",
            }}>
              {advantageTeam === "home" ? "Home" : "Away"} Edge
            </div>
          )}
        </div>

        {/* Away Goalie */}
        <div style={{ textAlign: "center" }}>
          <p style={{ fontSize: "0.65rem", color: "var(--text-tertiary)", textTransform: "uppercase", marginBottom: "0.25rem" }}>
            {report.awayTeam}
          </p>
          <p style={{ fontSize: "1rem", fontWeight: 600, color: "white", marginBottom: "0.35rem" }}>
            {report.awayGoalie.playerName || "TBD"}
          </p>
          <StatusBadge status={report.awayGoalie.status} confidence={report.awayGoalie.confidence} />
          {report.awayGoalie.gsaRolling !== null && (
            <p style={{
              marginTop: "0.5rem",
              fontSize: "0.85rem",
              fontWeight: 600,
              color: report.awayGoalie.gsaRolling > 0 ? "#10b981" : "#f59e0b",
            }}>
              GSA: {report.awayGoalie.gsaRolling > 0 ? "+" : ""}{report.awayGoalie.gsaRolling.toFixed(1)}
            </p>
          )}
        </div>
      </div>

      {/* Significance */}
      {report.significance !== "low" && (
        <div style={{
          marginTop: "1rem",
          padding: "0.5rem",
          borderRadius: "0.375rem",
          background: report.significance === "high" ? "#f59e0b10" : "#3b82f610",
          border: `1px solid ${report.significance === "high" ? "#f59e0b30" : "#3b82f630"}`,
        }}>
          <p style={{ fontSize: "0.75rem", color: report.significance === "high" ? "#f59e0b" : "#3b82f6" }}>
            {report.significance === "high"
              ? "Significant goalie advantage - may impact prediction"
              : "Moderate goalie differential"}
          </p>
        </div>
      )}

      {/* Timing Info */}
      <div style={{ marginTop: "0.75rem", fontSize: "0.7rem", color: "var(--text-tertiary)", textAlign: "center" }}>
        {report.typicalConfirmTime && !report.bothConfirmed && (
          <p>Starters typically confirmed around {report.typicalConfirmTime}</p>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// Team Goalie Situation Card
// =============================================================================

export function TeamGoalieSituationCard({
  starter,
  backup,
  teamAbbrev,
  nextOpponent,
}: {
  starter: StartingGoalieInfo | null;
  backup: StartingGoalieInfo | null;
  teamAbbrev: string;
  nextOpponent?: string;
}) {
  return (
    <div className="card" style={{ padding: "1.25rem" }}>
      <h3 style={{
        fontSize: "0.9rem",
        fontWeight: 600,
        color: "white",
        marginBottom: "1rem",
        display: "flex",
        alignItems: "center",
        gap: "0.5rem",
      }}>
        <span style={{
          width: "28px",
          height: "28px",
          borderRadius: "6px",
          background: "rgba(16,185,129,0.2)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}>
          <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </span>
        Goaltending
      </h3>

      {starter && (
        <div style={{ marginBottom: "1rem" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
            <div>
              <p style={{ fontSize: "0.65rem", color: "var(--text-tertiary)", textTransform: "uppercase" }}>Expected Starter</p>
              <p style={{ fontSize: "1.1rem", fontWeight: 600, color: "white" }}>{starter.playerName}</p>
            </div>
            <StatusBadge status={starter.status} confidence={starter.confidence} />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.5rem", marginTop: "0.5rem" }}>
            {starter.gsaRolling !== null && (
              <div style={{ textAlign: "center", padding: "0.5rem", background: "rgba(255,255,255,0.03)", borderRadius: "0.5rem" }}>
                <p style={{ fontSize: "1.1rem", fontWeight: 700, color: starter.gsaRolling > 0 ? "#10b981" : "#f59e0b" }}>
                  {starter.gsaRolling > 0 ? "+" : ""}{starter.gsaRolling.toFixed(1)}
                </p>
                <p style={{ fontSize: "0.6rem", color: "var(--text-tertiary)", textTransform: "uppercase" }}>Rolling GSA</p>
              </div>
            )}
            {starter.restDays !== null && (
              <div style={{ textAlign: "center", padding: "0.5rem", background: "rgba(255,255,255,0.03)", borderRadius: "0.5rem" }}>
                <p style={{
                  fontSize: "1.1rem",
                  fontWeight: 700,
                  color: starter.restDays >= 2 ? "#10b981" : starter.restDays === 1 ? "#f59e0b" : "#ef4444"
                }}>
                  {starter.restDays}
                </p>
                <p style={{ fontSize: "0.6rem", color: "var(--text-tertiary)", textTransform: "uppercase" }}>Days Rest</p>
              </div>
            )}
            <div style={{ textAlign: "center", padding: "0.5rem", background: "rgba(255,255,255,0.03)", borderRadius: "0.5rem" }}>
              <p style={{
                fontSize: "0.9rem",
                fontWeight: 600,
                color: starter.trend === "surging" ? "#10b981"
                  : starter.trend === "steady" ? "#3b82f6"
                  : starter.trend === "cooling" ? "#f59e0b"
                  : "var(--text-tertiary)",
              }}>
                {starter.trend.charAt(0).toUpperCase() + starter.trend.slice(1)}
              </p>
              <p style={{ fontSize: "0.6rem", color: "var(--text-tertiary)", textTransform: "uppercase" }}>Form</p>
            </div>
          </div>

          <ConfidenceMeter confidence={starter.confidence} />
        </div>
      )}

      {backup && (
        <div style={{
          padding: "0.75rem",
          background: "rgba(255,255,255,0.02)",
          borderRadius: "0.5rem",
          marginTop: "0.5rem",
        }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div>
              <p style={{ fontSize: "0.6rem", color: "var(--text-tertiary)", textTransform: "uppercase" }}>Backup</p>
              <p style={{ fontSize: "0.9rem", fontWeight: 500, color: "var(--text-secondary)" }}>{backup.playerName}</p>
            </div>
            {backup.gsaRolling !== null && (
              <span style={{ fontSize: "0.8rem", fontWeight: 600, color: backup.gsaRolling > 0 ? "#10b981" : "#f59e0b" }}>
                GSA: {backup.gsaRolling > 0 ? "+" : ""}{backup.gsaRolling.toFixed(1)}
              </span>
            )}
          </div>
        </div>
      )}

      {!starter && !backup && (
        <p style={{ fontSize: "0.85rem", color: "var(--text-tertiary)" }}>
          No goalie information available
        </p>
      )}

      {nextOpponent && (
        <p style={{ marginTop: "0.75rem", fontSize: "0.7rem", color: "var(--text-tertiary)" }}>
          Next opponent: {nextOpponent}
        </p>
      )}
    </div>
  );
}

// =============================================================================
// Compact Starter Badge (for game cards)
// =============================================================================

export function StarterBadge({ goalie }: { goalie: StartingGoalieInfo }) {
  const color = getConfidenceColor(goalie.confidence);

  if (!goalie.playerName) {
    return (
      <span style={{
        fontSize: "0.7rem",
        color: "var(--text-tertiary)",
        fontStyle: "italic",
      }}>
        TBD
      </span>
    );
  }

  return (
    <span style={{
      display: "inline-flex",
      alignItems: "center",
      gap: "0.35rem",
      padding: "0.2rem 0.4rem",
      borderRadius: "0.25rem",
      fontSize: "0.7rem",
      fontWeight: 500,
      background: `${color}15`,
      color: color,
    }}>
      <span style={{
        width: "5px",
        height: "5px",
        borderRadius: "50%",
        background: color,
      }} />
      {goalie.playerName?.split(" ").pop()}
      {goalie.status === "confirmed_starter" && (
        <svg style={{ width: "10px", height: "10px" }} fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
      )}
    </span>
  );
}
