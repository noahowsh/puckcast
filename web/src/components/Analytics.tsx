import Script from "next/script";

export function Analytics() {
  // Only load in production
  if (process.env.NODE_ENV !== "production") {
    return null;
  }

  return (
    <>
      {/* Plausible Analytics - Privacy-friendly, GDPR compliant, no cookies */}
      <Script
        defer
        data-domain="puckcast.ai"
        src="https://plausible.io/js/script.js"
        strategy="afterInteractive"
      />
    </>
  );
}
