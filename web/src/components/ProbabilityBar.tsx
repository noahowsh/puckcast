/**
 * ProbabilityBar - Visual representation of win probability split between two teams
 *
 * Displays a horizontal bar showing the relative win probability for home vs away team.
 * Color-coded by team and includes optional percentage labels.
 */
import React from 'react';

interface ProbabilityBarProps {
  /** Home team win probability (0-1) */
  homeProb: number;
  awayProb: number;
  homeTeam: string;
  awayTeam: string;
  showLabels?: boolean;
  height?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function ProbabilityBar({
  homeProb,
  awayProb,
  homeTeam,
  awayTeam,
  showLabels = true,
  height = 'md',
  className = ''
}: ProbabilityBarProps) {
  const heightClasses = {
    sm: 'h-2',
    md: 'h-3',
    lg: 'h-4'
  };

  const homePercent = (homeProb * 100).toFixed(1);
  const awayPercent = (awayProb * 100).toFixed(1);

  return (
    <div className={className}>
      {showLabels && (
        <div className="flex justify-between items-center mb-2 text-xs font-semibold">
          <span className="text-sky-400">{homeTeam} {homePercent}%</span>
          <span className="text-cyan-400">{awayTeam} {awayPercent}%</span>
        </div>
      )}

      <div className={`prob-bar ${heightClasses[height]} rounded-full overflow-hidden`}>
        <div
          className="prob-bar-segment bg-gradient-to-r from-sky-500 to-sky-400"
          style={{ width: `${homeProb * 100}%` }}
          title={`${homeTeam}: ${homePercent}%`}
        />
        <div
          className="prob-bar-segment bg-gradient-to-r from-cyan-400 to-cyan-500"
          style={{ width: `${awayProb * 100}%` }}
          title={`${awayTeam}: ${awayPercent}%`}
        />
      </div>
    </div>
  );
}
