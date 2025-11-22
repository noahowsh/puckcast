import React from 'react';

interface StatCardProps {
  label: string;
  value: string | number;
  change?: {
    value: string | number;
    isPositive: boolean;
  };
  icon?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg';
  compact?: boolean;
  className?: string;
}

export function StatCard({
  label,
  value,
  change,
  icon,
  size = 'md',
  compact = false,
  className = ''
}: StatCardProps) {
  const sizeClasses = {
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8'
  };

  const paddingClass = compact ? 'p-4' : sizeClasses[size];

  const valueSizes = {
    sm: 'text-2xl',
    md: 'text-3xl',
    lg: 'text-4xl'
  };

  return (
    <div className={`stat-card ${paddingClass} ${compact ? 'stat-card-compact' : ''} ${className}`}>
      <div className="flex items-start justify-between mb-2">
        <p className="stat-label">{label}</p>
        {icon && (
          <div className="text-slate-400">
            {icon}
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-3">
        <p className={`stat-value ${valueSizes[size]}`}>
          {value}
        </p>

        {change && (
          <span className={
            change.isPositive
              ? 'stat-change-positive'
              : 'stat-change-negative'
          }>
            {change.isPositive ? '+' : ''}{change.value}
          </span>
        )}
      </div>
    </div>
  );
}
