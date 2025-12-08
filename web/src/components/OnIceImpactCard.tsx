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
  const { forMetrics, againstMetrics, general, impactSummary, evTimeOnIce, position } = impact;
  const positionLabel = position === "D" ? "Defenseman" : "Forward";

  return (
    <div className="relative bg-gradient-to-b from-[#1a1f2e] to-[#151922] border border-white/[0.06] rounded-xl overflow-hidden">
      {/* Header - Full width gradient */}
      <div className="relative border-b border-white/[0.06]">
        <div className="absolute inset-0 bg-gradient-to-r from-amber-500/20 via-amber-500/8 to-transparent" />
        <div className="relative flex items-center justify-between px-6 py-5">
          <div>
            <h3 className="text-lg font-bold text-white">On-Ice Impact</h3>
            <p className="text-xs text-white/50 mt-0.5">Even-Strength RAPM Analysis</p>
          </div>
          <div className="flex items-center gap-5 text-right">
            {age && (
              <div>
                <span className="text-[10px] text-white/40 block">Age</span>
                <p className="text-sm font-semibold text-white">{age}</p>
              </div>
            )}
            <div>
              <span className="text-[10px] text-white/40 block">Pos</span>
              <p className="text-sm font-semibold text-white">{position}</p>
            </div>
            <div>
              <span className="text-[10px] text-white/40 block">EV TOI</span>
              <p className="text-sm font-semibold text-white">{evTimeOnIce} min</p>
            </div>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-8">
        {/* FOR vs AGAINST Metrics Table */}
        <div className="bg-white/[0.02] rounded-lg overflow-hidden">
          {/* Header */}
          <div className="grid grid-cols-[110px_1fr_1fr] border-b border-white/[0.06]">
            <div className="py-3 px-4"></div>
            <div className="py-3 px-3 text-center">
              <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wide">FOR</span>
            </div>
            <div className="py-3 px-3 text-center">
              <span className="text-[11px] font-bold text-white/40 uppercase tracking-wide">AGAINST</span>
            </div>
          </div>
          {/* Rows */}
          <MetricRow label="Goals" forMetric={forMetrics.goals} againstMetric={againstMetrics.goals} />
          <MetricRow label="Shots" forMetric={forMetrics.shots} againstMetric={againstMetrics.shots} />
          <MetricRow label="xGoals" forMetric={forMetrics.expectedGoals} againstMetric={againstMetrics.expectedGoals} />
          <MetricRow label="Corsi" forMetric={forMetrics.corsi} againstMetric={againstMetrics.corsi} />
          <MetricRow label="Shot Quality" forMetric={forMetrics.shotQuality} againstMetric={againstMetrics.shotQuality} isLast />
        </div>

        {/* General Metrics */}
        <div>
          <h4 className="text-xs font-semibold text-white/60 uppercase tracking-wide mb-4">General</h4>
          <div className="grid grid-cols-4 gap-4">
            <GeneralMetric label="Net xGoals" metric={general.netExpectedGoals} />
            <GeneralMetric label="Net Corsi" metric={general.netCorsi} />
            <GeneralMetric label="Finishing" metric={general.finishing} />
            <GeneralMetric label="Blocking" metric={general.shotBlocking} />
          </div>
        </div>

        {/* Impact Summary */}
        <p className="text-xs text-white/60 leading-relaxed">{impactSummary}</p>

        {/* Legend & Notes */}
        <div className="pt-6 border-t border-white/[0.06] space-y-3">
          <div className="flex items-center justify-center gap-3">
            <LegendItem color="bg-rose-500/50" label="Poor" />
            <LegendItem color="bg-amber-500/40" label="Below Avg" />
            <LegendItem color="bg-white/25" label="Average" />
            <LegendItem color="bg-emerald-500/50" label="Above Avg" />
            <LegendItem color="bg-sky-500/60" label="Elite" />
          </div>
          <p className="text-[9px] text-white/30 text-center">
            RAPM quantifies on-ice contributions. Against shown muted (goalie dependency). Percentiles vs. {positionLabel}s.
          </p>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Helper Components
// =============================================================================

function MetricRow({ label, forMetric, againstMetric, isLast = false }: { label: string; forMetric: ImpactMetric; againstMetric: ImpactMetric; isLast?: boolean }) {
  return (
    <div className={`grid grid-cols-[110px_1fr_1fr] ${!isLast ? "border-b border-white/[0.04]" : ""}`}>
      <div className="py-2.5 px-4 text-xs text-white/60">{label}</div>
      <div className="py-2 px-3">
        <MetricBadge metric={forMetric} variant="for" />
      </div>
      <div className="py-2 px-3">
        <MetricBadge metric={againstMetric} variant="against" />
      </div>
    </div>
  );
}

function MetricBadge({ metric, variant }: { metric: ImpactMetric; variant: "for" | "against" }) {
  const { percentile, tier } = metric;
  const bgClass = variant === "against" ? getTierBackgroundMuted(tier) : getTierBackground(tier);
  const textClass = variant === "against" ? getTierTextMuted(tier) : getTierText(tier);

  return (
    <div className={`py-1.5 rounded text-center ${bgClass}`}>
      <span className={`text-sm font-bold ${textClass}`}>{percentile}%</span>
    </div>
  );
}

function GeneralMetric({ label, metric }: { label: string; metric: ImpactMetric }) {
  const { percentile, tier } = metric;

  return (
    <div className={`p-3 rounded-lg text-center ${getTierBackground(tier)}`}>
      <p className={`text-xl font-bold ${getTierText(tier)}`}>{percentile}%</p>
      <p className="text-[10px] text-white/50 mt-0.5">{label}</p>
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1">
      <div className={`w-2.5 h-2.5 rounded ${color}`} />
      <span className="text-[9px] text-white/40">{label}</span>
    </div>
  );
}

// =============================================================================
// Helper Functions
// =============================================================================

function getTierBackground(tier: ImpactMetric["tier"]): string {
  switch (tier) {
    case "elite": return "bg-sky-500/20";
    case "above-average": return "bg-emerald-500/20";
    case "average": return "bg-white/[0.06]";
    case "below-average": return "bg-amber-500/15";
    case "poor": return "bg-rose-500/15";
  }
}

function getTierBackgroundMuted(tier: ImpactMetric["tier"]): string {
  switch (tier) {
    case "elite": return "bg-sky-500/10";
    case "above-average": return "bg-emerald-500/10";
    case "average": return "bg-white/[0.03]";
    case "below-average": return "bg-amber-500/8";
    case "poor": return "bg-rose-500/8";
  }
}

function getTierText(tier: ImpactMetric["tier"]): string {
  switch (tier) {
    case "elite": return "text-sky-300";
    case "above-average": return "text-emerald-400";
    case "average": return "text-white/70";
    case "below-average": return "text-amber-400";
    case "poor": return "text-rose-400";
  }
}

function getTierTextMuted(tier: ImpactMetric["tier"]): string {
  switch (tier) {
    case "elite": return "text-sky-300/60";
    case "above-average": return "text-emerald-400/60";
    case "average": return "text-white/40";
    case "below-average": return "text-amber-400/60";
    case "poor": return "text-rose-400/60";
  }
}
