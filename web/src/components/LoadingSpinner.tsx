import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  message?: string;
  center?: boolean;
}

export function LoadingSpinner({
  size = 'md',
  message,
  center = false
}: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-6 h-6 border-2',
    md: 'w-10 h-10 border-3',
    lg: 'w-16 h-16 border-4'
  };

  const spinner = (
    <div className="inline-flex flex-col items-center gap-3">
      <div className={`spinner ${sizeClasses[size]}`} />
      {message && (
        <p className="text-sm text-slate-400 animate-pulse-subtle">
          {message}
        </p>
      )}
    </div>
  );

  if (center) {
    return (
      <div className="flex items-center justify-center min-h-[300px] w-full">
        {spinner}
      </div>
    );
  }

  return spinner;
}

export function LoadingSkeleton({
  count = 1,
  height = 'h-20',
  className = ''
}: {
  count?: number;
  height?: string;
  className?: string;
}) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={`skeleton ${height} w-full ${className}`}
        />
      ))}
    </>
  );
}
