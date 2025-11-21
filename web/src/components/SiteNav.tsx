"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const links = [
  { href: "/", label: "Overview", icon: "🏠" },
  { href: "/predictions", label: "Predictions", icon: "🎯" },
  { href: "/leaderboards", label: "Power Rankings", icon: "⚡" },
  { href: "/performance", label: "Performance", icon: "📊" },
  { href: "/goalies", label: "Goalies", icon: "🥅" },
  { href: "/betting", label: "Betting", icon: "💰" },
  { href: "/about", label: "About", icon: "ℹ️" },
];

export function SiteNav() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <nav className="fixed inset-x-0 top-0 z-50 border-b border-sky-500/20 bg-slate-950/95 backdrop-blur-xl shadow-2xl shadow-black/60">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 lg:px-8">
        {/* Logo */}
        <Link
          href="/"
          className="flex items-center gap-3 text-white transition-all duration-300 hover:scale-105 group"
        >
          <div className="relative">
            <Image
              src="/logo.svg"
              alt="Puckcast logo"
              width={40}
              height={40}
              className="h-10 w-10 transition-transform duration-300 group-hover:rotate-12"
              priority
            />
            <div className="absolute inset-0 bg-sky-500/20 blur-xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          </div>
          <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-sky-400 to-cyan-400 bg-clip-text text-transparent">
            Puckcast
          </span>
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden lg:flex items-center gap-1">
          {links.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`
                  relative px-4 py-2 rounded-lg text-sm font-semibold tracking-wide
                  transition-all duration-300
                  ${
                    active
                      ? "text-white bg-gradient-to-r from-sky-500 to-cyan-500 shadow-lg shadow-sky-500/30"
                      : "text-slate-300 hover:text-white hover:bg-white/5"
                  }
                `}
              >
                {active && (
                  <div className="absolute inset-0 bg-sky-500/20 blur-lg rounded-lg"></div>
                )}
                <span className="relative z-10">{link.label}</span>
              </Link>
            );
          })}
        </div>

        {/* Mobile Menu Button */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="lg:hidden p-2 rounded-lg bg-white/5 border border-sky-500/20 hover:bg-white/10 transition-all duration-300"
          aria-label="Toggle mobile menu"
        >
          <div className="flex flex-col gap-1.5 w-6">
            <span className={`h-0.5 bg-white rounded-full transition-all duration-300 ${mobileMenuOpen ? 'rotate-45 translate-y-2' : ''}`}></span>
            <span className={`h-0.5 bg-white rounded-full transition-all duration-300 ${mobileMenuOpen ? 'opacity-0' : ''}`}></span>
            <span className={`h-0.5 bg-white rounded-full transition-all duration-300 ${mobileMenuOpen ? '-rotate-45 -translate-y-2' : ''}`}></span>
          </div>
        </button>
      </div>

      {/* Mobile Menu Dropdown */}
      <div
        className={`
          lg:hidden overflow-hidden transition-all duration-500 ease-in-out
          ${mobileMenuOpen ? "max-h-screen opacity-100" : "max-h-0 opacity-0"}
        `}
      >
        <div className="px-4 py-4 space-y-2 bg-slate-950/98 border-t border-sky-500/10">
          {links.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`
                  flex items-center gap-3 px-4 py-3 rounded-lg text-base font-semibold
                  transition-all duration-300
                  ${
                    active
                      ? "text-white bg-gradient-to-r from-sky-500 to-cyan-500 shadow-lg shadow-sky-500/20"
                      : "text-slate-300 hover:text-white hover:bg-white/5"
                  }
                `}
              >
                <span className="text-xl">{link.icon}</span>
                <span>{link.label}</span>
                {active && (
                  <span className="ml-auto">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </span>
                )}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
