import React from 'react';

interface ConfidenceBadgeProps {
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
