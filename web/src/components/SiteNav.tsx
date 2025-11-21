"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const links = [
  { href: "/", label: "Overview" },
  { href: "/predictions", label: "Predictions" },
  { href: "/leaderboards", label: "Power Rankings" },
  { href: "/performance", label: "Performance" },
  { href: "/goalies", label: "Goalies" },
  { href: "/betting", label: "Betting Lab" },
  { href: "/about", label: "About" },
];

export function SiteNav() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <nav className="fixed inset-x-0 top-0 z-50 border-b border-white/10 glass-effect shadow-xl">
      <div className="container">
        <div className="flex items-center justify-between py-6">
          {/* Logo */}
          <Link
            href="/"
            className="flex items-center gap-3 group"
          >
            <div className="relative">
              <Image
                src="/logo.svg"
                alt="Puckcast logo"
                width={40}
                height={40}
                className="h-10 w-10 transition-transform duration-300 group-hover:scale-110"
                priority
              />
            </div>
            <span className="text-2xl font-bold tracking-tight text-gradient">
              Puckcast
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden lg:flex items-center gap-8">
            {links.map((link) => {
              const active = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`
                    relative px-6 py-3 rounded-xl text-base font-semibold
                    transition-all duration-200
                    ${
                      active
                        ? "text-white bg-gradient-to-r from-sky-500 to-blue-600 shadow-md"
                        : "text-slate-300 hover:text-white hover:bg-white/5"
                    }
                  `}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-all"
            aria-label="Toggle mobile menu"
          >
            <div className="flex flex-col gap-1.5 w-6">
              <span className={`h-0.5 bg-white rounded-full transition-all ${mobileMenuOpen ? 'rotate-45 translate-y-2' : ''}`}></span>
              <span className={`h-0.5 bg-white rounded-full transition-all ${mobileMenuOpen ? 'opacity-0' : ''}`}></span>
              <span className={`h-0.5 bg-white rounded-full transition-all ${mobileMenuOpen ? '-rotate-45 -translate-y-2' : ''}`}></span>
            </div>
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      <div
        className={`
          lg:hidden overflow-hidden transition-all duration-300
          ${mobileMenuOpen ? "max-h-screen opacity-100" : "max-h-0 opacity-0"}
        `}
      >
        <div className="container py-4 space-y-2 border-t border-white/5">
          {links.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`
                  flex items-center justify-between px-4 py-3 rounded-lg text-base font-semibold
                  transition-all
                  ${
                    active
                      ? "text-white bg-gradient-to-r from-sky-500 to-blue-600"
                      : "text-slate-300 hover:text-white hover:bg-white/5"
                  }
                `}
              >
                <span>{link.label}</span>
                {active && (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
