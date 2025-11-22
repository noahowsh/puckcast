import React from 'react';

interface PageHeaderProps {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export function PageHeader({
  title,
  description,
  icon,
  action,
  className = ''
}: PageHeaderProps) {
  return (
    <header className={`section ${className}`}>
      <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between md:gap-8">
        <div className="flex items-start gap-5 min-w-0">
          {icon && (
            <div className="hidden h-16 w-16 flex-shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-400/20 to-cyan-400/20 ring-1 ring-white/10 md:flex">
              <div className="text-sky-300">{icon}</div>
            </div>
          )}
          <div className="min-w-0">
            <p className="text-xs uppercase tracking-[0.26em] text-white/50 mb-2">Puckcast Intelligence</p>
            <h1 className="text-gradient mb-4 leading-tight">{title}</h1>
            {description && (
              <p className="text-base leading-relaxed text-white/70 md:text-lg max-w-3xl">
                {description}
              </p>
            )}
          </div>
        </div>

        {action && <div className="flex-shrink-0">{action}</div>}
      </div>
      <div className="mt-8 h-px w-full bg-gradient-to-r from-transparent via-white/10 to-transparent" />
    </header>
  );
}
