import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Epilogue, Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import { SiteNav } from "@/components/SiteNav";
import { SiteFooter } from "@/components/SiteFooter";
import { PageTransition } from "@/components/PageTransition";
import { Analytics } from "@/components/Analytics";
import Script from "next/script";

const display = Epilogue({
  subsets: ["latin"],
  weight: ["600", "700", "800"],
  variable: "--font-display",
  display: "swap",
});

const body = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-body",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Puckcast | NHL Predictions + Analytics",
  description:
    "Data-driven NHL predictions powered by the official NHL API with 60%+ accuracy. Advanced analytics, goalie tracking, and real-time game predictions.",
  metadataBase: new URL("https://puckcast.ai"),
  icons: {
    icon: "/puckcastai.png",
    apple: "/puckcastai.png",
  },
  openGraph: {
    title: "Puckcast | NHL Predictions + Analytics",
    description:
      "60%+ accurate NHL predictions using 204 engineered features from official NHL data. Win probabilities and betting insights for every matchup.",
    type: "website",
    url: "https://puckcast.ai",
    images: [
      {
        url: "/puckcastsocial.png",
        width: 1200,
        height: 630,
        alt: "Puckcast social preview",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Puckcast | NHL Predictions + Analytics",
    description: "Data-driven NHL predictions with 60%+ accuracy. Powered by official NHL API and advanced machine learning.",
    images: ["/puckcastsocial.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${display.variable} ${body.variable} antialiased`}>
        <Script
          src="https://www.googletagmanager.com/gtag/js?id=G-ZSYWJKWQM3"
          strategy="afterInteractive"
        />
        <Script id="ga-gtag" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-ZSYWJKWQM3');
          `}
        </Script>
        <Analytics />
        <div className="relative min-h-screen overflow-hidden text-white">
          <div
            className="pointer-events-none fixed inset-0"
            aria-hidden
          >
            <div className="absolute inset-0 bg-gradient-to-b from-white/[0.02] via-transparent to-white/[0.04]" />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(103,232,249,0.08),transparent_35%)]" />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_0%,rgba(52,211,153,0.08),transparent_32%)]" />
          </div>
          <SiteNav />
          <PageTransition>
            <main className="pb-0" style={{ paddingTop: "calc(var(--nav-height) + 2.5rem)" }}>
              {children}
            </main>
          </PageTransition>
          <SiteFooter />
        </div>
      </body>
    </html>
  );
}
