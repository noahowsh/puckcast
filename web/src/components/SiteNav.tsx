"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Overview" },
  { href: "/predictions", label: "Predictions" },
  { href: "/leaderboards", label: "Power Rankings" },
  { href: "/performance", label: "Performance" },
  { href: "/methodology", label: "Methodology" },
  { href: "/analytics", label: "Analytics" },
  { href: "/about", label: "About" },
];

export function SiteNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 top-0 z-50 border-b border-white/10 bg-slate-950/90 backdrop-blur supports-[backdrop-filter]:backdrop-blur-xl shadow-2xl shadow-black/40">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-5 text-[0.82rem] font-semibold uppercase tracking-[0.3em] text-white/80 lg:flex-nowrap lg:px-10 lg:py-6">
        <Link href="/" className="flex items-center gap-3 text-white transition hover:text-lime-200">
          <Image src="/logo.svg" alt="Puckcast logo" width={34} height={34} className="h-9 w-9" priority />
          <span className="text-[0.95rem]">Puckcast</span>
        </Link>
        <div className="flex flex-1 items-center justify-center gap-2 overflow-x-auto whitespace-nowrap lg:justify-end">
          {links.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-full px-4 py-1.5 transition ${
                  active ? "bg-white text-slate-900" : "text-white/60 hover:text-white"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
