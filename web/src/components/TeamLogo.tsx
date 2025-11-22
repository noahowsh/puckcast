"use client";

import Image from "next/image";
import { useState } from 'react';

interface TeamLogoProps {
  teamAbbrev: string;
  teamName?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  showName?: boolean;
  className?: string;
}

export function TeamLogo({
  teamAbbrev,
  teamName,
  size = 'md',
  showName = false,
  className = ''
}: TeamLogoProps) {
  const [hasError, setHasError] = useState(false);

  const sizeMap = {
    xs: 24,
    sm: 32,
    md: 48,
    lg: 64,
    xl: 80
  };

  const pixelSize = sizeMap[size];
  const logoUrl = `https://assets.nhle.com/logos/nhl/svg/${teamAbbrev}_light.svg`;

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {!hasError ? (
        <Image
          src={logoUrl}
          alt={teamName || teamAbbrev}
          width={pixelSize}
          height={pixelSize}
          className="object-contain"
          onError={() => setHasError(true)}
        />
      ) : (
        <span
          className="font-bold text-slate-300"
          style={{ fontSize: `${pixelSize * 0.4}px` }}
        >
          {teamAbbrev}
        </span>
      )}
      {showName && teamName && (
        <span className="font-semibold text-slate-200">
          {teamName}
        </span>
      )}
    </div>
  );
}
