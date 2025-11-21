import type { Metadata } from "next";
import type { ReactNode } from "react";
// Using system fonts instead of Google Fonts for better reliability
// import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { SiteNav } from "@/components/SiteNav";
import { SiteFooter } from "@/components/SiteFooter";
import { PageTransition } from "@/components/PageTransition";
import { Analytics } from "@/components/Analytics";

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
    "Data-driven NHL predictions powered by the official NHL API with 60%+ accuracy. Advanced analytics, goalie tracking, and real-time game predictions.",
  metadataBase: new URL("https://puckcast.ai"),
  openGraph: {
    title: "Puckcast | NHL Predictions + Analytics",
    description:
      "60%+ accurate NHL predictions using 204 engineered features from official NHL data. Win probabilities and betting insights for every matchup.",
    type: "website",
    url: "https://puckcast.ai",
  },
  twitter: {
    card: "summary_large_image",
    title: "Puckcast | NHL Predictions + Analytics",
    description: "Data-driven NHL predictions with 60%+ accuracy. Powered by official NHL API and advanced machine learning.",
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
        <Analytics />
        <div className="relative min-h-screen bg-slate-950 text-white">
          <SiteNav />
          <PageTransition>
            <div className="pt-24">{children}</div>
          </PageTransition>
          <SiteFooter />
        </div>
      </body>
    </html>
  );
}
