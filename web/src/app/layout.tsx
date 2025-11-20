import type { Metadata } from "next";
import type { ReactNode } from "react";
// Using system fonts instead of Google Fonts for better reliability
// import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { SiteNav } from "@/components/SiteNav";
import { SiteFooter } from "@/components/SiteFooter";

// System fonts fallback (can re-enable Google Fonts when network is stable)
const geistSans = {
  variable: "--font-geist-sans",
};

const geistMono = {
  variable: "--font-geist-mono",
};

export const metadata: Metadata = {
  title: "Puckcast | NHL Predictions + Analytics",
  description:
    "Interactive NHL prediction hub powered by MoneyPuck ingestion, goalie form tracking, and 50k Monte Carlo simulations per matchup.",
  metadataBase: new URL("https://puckcast.ai"),
  openGraph: {
    title: "Puckcast | NHL Predictions + Analytics",
    description:
      "Win probabilities, edge summaries, and transparent notes for every NHL matchup.",
    type: "website",
    url: "https://puckcast.ai",
  },
  twitter: {
    card: "summary_large_image",
    title: "Puckcast | NHL Predictions + Analytics",
    description: "Daily NHL projections and insights sourced from the MoneyPuck feature stack.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <div className="relative min-h-screen bg-slate-950 text-white">
          <SiteNav />
        <div className="pt-24">{children}</div>
          <SiteFooter />
        </div>
      </body>
    </html>
  );
}
