"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import Image from "next/image";

const links = [
  { href: "/", label: "Overview" },
  { href: "/predictions", label: "Predictions" },
  { href: "/leaderboards", label: "Power Rankings" },
  { href: "/teams", label: "Teams" },
  { href: "/players", label: "Players" },
  { href: "/performance", label: "Performance" },
];

export function SiteNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <header className="nav-shell">
      <div className="container">
        <div className="nav-inner">
          <Link href="/" className="nav-brand" onClick={() => setOpen(false)}>
            <div className="nav-mark-clean">
              <Image
                src="/puckcastai.png"
                alt="Puckcast"
                width={44}
                height={44}
              />
            </div>
            <div className="nav-text">
              <span className="nav-title">Puckcast.ai</span>
            </div>
          </Link>

          <nav className="nav-links">
            {links.map((link) => {
              const active = pathname === link.href;
              return (
                <Link key={link.href} href={link.href} className={`nav-link ${active ? "nav-link--active" : ""}`}>
                  {link.label}
                </Link>
              );
            })}
          </nav>

          <div className="nav-actions">
            <Link href="https://x.com/puckcastai" className="nav-cta nav-cta--ghost" target="_blank" rel="noreferrer">
              Follow on X
            </Link>
            <button
              className={`nav-toggle ${open ? "nav-toggle--open" : ""}`}
              onClick={() => setOpen((prev) => !prev)}
              aria-label="Toggle navigation"
            >
              <span />
              <span />
            </button>
          </div>
        </div>
      </div>

      <div className={`nav-drawer ${open ? "nav-drawer--open" : ""}`}>
        <div className="nav-drawer__content">
          {links.map((link) => {
            const active = pathname === link.href;
            return (
              <Link key={link.href} href={link.href} className={`nav-drawer__link ${active ? "is-active" : ""}`} onClick={() => setOpen(false)}>
                <span>{link.label}</span>
                {active && <span className="nav-drawer__dot" aria-hidden />}
              </Link>
            );
          })}
          <div className="nav-drawer__cta">
            <Link href="https://x.com/puckcastai" className="nav-cta nav-cta--ghost" target="_blank" rel="noreferrer" onClick={() => setOpen(false)}>
              Follow on X
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}
