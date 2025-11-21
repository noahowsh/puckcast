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
    <div className={`mb-8 md:mb-12 ${className}`}>
      <div className="flex items-start justify-between gap-6">
        <div className="flex items-center gap-4">
          {icon && (
            <div className="hidden md:flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-sky-500/20 to-cyan-500/20 border border-sky-500/30">
              <div className="text-sky-400">
                {icon}
              </div>
            </div>
          )}
          <div>
            <h1 className="text-gradient mb-2">{title}</h1>
            {description && (
              <p className="text-slate-400 text-lg max-w-3xl leading-relaxed">
                {description}
              </p>
            )}
          </div>
        </div>

        {action && (
          <div className="flex-shrink-0">
            {action}
          </div>
        )}
      </div>
    </div>
  );
}
