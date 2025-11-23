import Image from "next/image";
import { teamGradient, teamBorderColor, teamLogoUrl } from "@/lib/teamColors";

type Props = {
  abbrev: string;
  size?: number;
  className?: string;
};

export function TeamCrest({ abbrev, size = 60, className }: Props) {
  const safe = abbrev?.toUpperCase?.() ?? "";
  const src = teamLogoUrl(safe);

  return (
    <span
      className={`crest ${className ?? ""}`.trim()}
      style={{
        width: `${size}px`,
        height: `${size}px`,
        background: teamGradient(safe),
        borderColor: teamBorderColor(safe),
      }}
    >
      <Image
        src={src}
        alt={`${safe} logo`}
        width={size * 0.78}
        height={size * 0.78}
        className="crest__img"
        priority={false}
      />
    </span>
  );
}
