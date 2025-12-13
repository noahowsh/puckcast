/**
 * ConfidenceBadge - Displays prediction confidence as a color-coded grade badge
 *
 * Used throughout the site to show model confidence levels:
 * - S/A grade (green): High confidence predictions
 * - B grade (yellow): Medium confidence
 * - C grade (orange): Lower confidence
 * - D/F grade (red): Low confidence
 */
import React from 'react';

interface ConfidenceBadgeProps {
  /** The confidence grade (e.g., "A+", "B", "C-") */
  grade: string;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function ConfidenceBadge({
  grade,
  showLabel = false,
  size = 'md'
}: ConfidenceBadgeProps) {
  // Determine badge style based on grade
  const getBadgeClass = (grade: string): string => {
    const normalizedGrade = grade.replace(/[+-]/g, '').toUpperCase();

    if (normalizedGrade === 'A' || normalizedGrade === 'S') {
      return 'badge-confidence-s';
    } else if (normalizedGrade === 'B') {
      return 'badge-confidence-a';
    } else if (normalizedGrade === 'C') {
      return 'badge-confidence-b';
    } else {
      return 'badge-confidence-c';
    }
  };

  const sizeClasses = {
    sm: 'text-xs px-2 py-1',
    md: 'text-sm px-3 py-1.5',
    lg: 'text-base px-4 py-2'
  };

  const gradeLabel = showLabel ? `Grade ${grade}` : grade;

  return (
    <span className={`badge ${getBadgeClass(grade)} ${sizeClasses[size]}`}>
      {gradeLabel}
    </span>
  );
}

/**
 * Returns the CSS color variable for a given confidence grade.
 * @param grade - The confidence grade (e.g., "A+", "B", "C-")
 * @returns CSS variable string for the grade color
 */
export function getConfidenceColor(grade: string): string {
  const normalizedGrade = grade.replace(/[+-]/g, '').toUpperCase();

  if (normalizedGrade === 'A' || normalizedGrade === 'S') {
    return 'var(--confidence-s)';
  } else if (normalizedGrade === 'B') {
    return 'var(--confidence-a)';
  } else if (normalizedGrade === 'C') {
    return 'var(--confidence-b)';
  } else {
    return 'var(--confidence-c)';
  }
}
