"use client";

import type { OnIceImpact, ImpactMetric } from "@/types/player";

// =============================================================================
// On-Ice Impact Card Component (RAPM-Style)
// =============================================================================

interface OnIceImpactCardProps {
  impact: OnIceImpact;
  playerName: string;
  age?: number;
}

export function OnIceImpactCard({ impact, playerName, age }: OnIceImpactCardProps) {
  const {
    forMetrics,
    againstMetrics,
    general,
    impactSummary,
    evTimeOnIce,
    position,
  } = impact;

  const positionLabel = position === "D" ? "Defenseman" : "Forward";

  return (
    <div className="card p-0 overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-white/[0.06] bg-gradient-to-r from-amber-500/10 to-transparent">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-white">On-Ice Impact</h3>
            <p className="text-xs text-white/50 mt-0.5">Even-Strength RAPM Analysis</p>
          </div>
          <div className="flex items-center gap-4">
            {age && (
              <div className="text-right">
                <span className="text-xs text-white/40">Age</span>
                <p className="text-sm font-semibold text-white">{age}</p>
              </div>
            )}
            <div className="text-right">
              <span className="text-xs text-white/40">Pos</span>
              <p className="text-sm font-semibold text-white">{position}</p>
            </div>
            <div className="text-right">
              <span className="text-xs text-white/40">EV TOI</span>
              <p className="text-sm font-semibold text-white">{evTimeOnIce} min</p>
            </div>
          </div>
        </div>
      </div>

      <div className="p-5 space-y-6">
        {/* FOR vs AGAINST Metrics */}
        <div>
          <div className="grid grid-cols-3 gap-2 mb-3">
            <div></div>
            <div className="text-center">
              <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">FOR</span>
            </div>
            <div className="text-center">
              <span className="text-xs font-semibold text-white/50 uppercase tracking-wider">AGAINST</span>
            </div>
          </div>

          <div className="space-y-2">
            <MetricRow
              label="Goals"
              forMetric={forMetrics.goals}
              againstMetric={againstMetrics.goals}
            />
            <MetricRow
              label="Shots"
              forMetric={forMetrics.shots}
              againstMetric={againstMetrics.shots}
            />
            <MetricRow
              label="xGoals"
              forMetric={forMetrics.expectedGoals}
              againstMetric={againstMetrics.expectedGoals}
            />
            <MetricRow
              label="Corsi"
              forMetric={forMetrics.corsi}
              againstMetric={againstMetrics.corsi}
            />
            <MetricRow
              label="Shot Quality"
              forMetric={forMetrics.shotQuality}
              againstMetric={againstMetrics.shotQuality}
            />
          </div>
        </div>

        {/* General Advanced Metrics */}
        <div>
          <h4 className="text-sm font-semibold text-white/70 uppercase tracking-wide mb-3">
            General
          </h4>
          <div className="grid grid-cols-2 gap-3">
            <GeneralMetricBox
              label="Net xGoals"
              metric={general.netExpectedGoals}
            />
            <GeneralMetricBox
              label="Net Corsi"
              metric={general.netCorsi}
            />
            <GeneralMetricBox
              label="Finishing"
              metric={general.finishing}
            />
            <GeneralMetricBox
              label="Blocking"
              metric={general.shotBlocking}
            />
          </div>
        </div>

        {/* Impact Summary */}
        <div className="p-4 bg-white/[0.02] rounded-lg border border-white/[0.04]">
          <p className="text-sm text-white/70 leading-relaxed">{impactSummary}</p>
        </div>

        {/* Legend & Notes */}
        <div className="pt-4 border-t border-white/[0.06] space-y-3">
          <div className="flex items-center justify-center gap-2 flex-wrap">
            <LegendItem color="bg-rose-500/50" label="Poor" />
            <LegendItem color="bg-amber-500/40" label="Below Avg" />
            <LegendItem color="bg-white/30" label="Average" />
            <LegendItem color="bg-emerald-500/50" label="Above Avg" />
            <LegendItem color="bg-sky-500/60" label="Elite" />
          </div>
          <p className="text-[10px] text-white/30 leading-relaxed text-center">
            RAPM (Regularized Adjusted Plus-Minus) quantifies on-ice contributions. Against metrics shown in muted colors to indicate dependency on goalie performance. Percentiles compared among {positionLabel}s.
          </p>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Helper Components
// =============================================================================

function MetricRow({
  label,
  forMetric,
  againstMetric,
}: {
  label: string;
  forMetric: ImpactMetric;
  againstMetric: ImpactMetric;
}) {
  return (
    <div className="grid grid-cols-3 gap-2 items-center">
      <div className="text-sm text-white/70 font-medium">{label}</div>
      <MetricBadge metric={forMetric} variant="for" />
      <MetricBadge metric={againstMetric} variant="against" />
    </div>
  );
}

function MetricBadge({
  metric,
  variant,
}: {
  metric: ImpactMetric;
  variant: "for" | "against";
}) {
  const { percentile, tier } = metric;
  const bgClass = variant === "against" ? getTierBackgroundMuted(tier) : getTierBackground(tier);
  const textClass = variant === "against" ? getTierTextMuted(tier) : getTierText(tier);

  return (
    <div className={`py-2 px-3 rounded-lg text-center ${bgClass}`}>
      <span className={`text-sm font-bold ${textClass}`}>{percentile}%</span>
    </div>
  );
}

function GeneralMetricBox({
  label,
  metric,
}: {
  label: string;
  metric: ImpactMetric;
}) {
  const { percentile, tier } = metric;
  const bgClass = getTierBackground(tier);
  const textClass = getTierText(tier);

  return (
    <div className={`p-3 rounded-lg ${bgClass}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs text-white/60 font-medium">{label}</span>
        <span className={`text-lg font-bold ${textClass}`}>{percentile}%</span>
      </div>
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <div className={`w-3 h-3 rounded ${color}`} />
      <span className="text-[10px] text-white/50">{label}</span>
    </div>
  );
}

// =============================================================================
// Helper Functions
// =============================================================================

function getTierBackground(tier: ImpactMetric["tier"]): string {
  switch (tier) {
    case "elite":
      return "bg-sky-500/30";
    case "above-average":
      return "bg-emerald-500/30";
    case "average":
      return "bg-white/[0.08]";
    case "below-average":
      return "bg-amber-500/20";
    case "poor":
      return "bg-rose-500/20";
  }
}

function getTierBackgroundMuted(tier: ImpactMetric["tier"]): string {
  switch (tier) {
    case "elite":
      return "bg-sky-500/15";
    case "above-average":
      return "bg-emerald-500/15";
    case "average":
      return "bg-white/[0.05]";
    case "below-average":
      return "bg-amber-500/10";
    case "poor":
      return "bg-rose-500/10";
  }
}

function getTierText(tier: ImpactMetric["tier"]): string {
  switch (tier) {
    case "elite":
      return "text-sky-300";
    case "above-average":
      return "text-emerald-400";
    case "average":
      return "text-white/80";
    case "below-average":
      return "text-amber-400";
    case "poor":
      return "text-rose-400";
  }
}

function getTierTextMuted(tier: ImpactMetric["tier"]): string {
  switch (tier) {
    case "elite":
      return "text-sky-300/70";
    case "above-average":
      return "text-emerald-400/70";
    case "average":
      return "text-white/50";
    case "below-average":
      return "text-amber-400/70";
    case "poor":
      return "text-rose-400/70";
  }
}
