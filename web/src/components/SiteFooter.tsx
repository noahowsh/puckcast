import Image from "next/image";

const SITE_VERSION = "v7.0";

export function SiteFooter() {
  const currentYear = new Date().getFullYear();
  const links = [
    { href: "/", label: "Overview" },
    { href: "/predictions", label: "Predictions" },
    { href: "/leaderboards", label: "Power Rankings" },
    { href: "/performance", label: "Performance" },
    { href: "/teams", label: "Teams" },
  ];

  return (
    <footer className="footer-shell">
      <div className="container footer-grid">
        <div className="footer-left">
          <div className="footer-brand">
            <div className="footer-mark-clean">
              <Image
                src="/puckcastai.png"
                alt="Puckcast"
                width={42}
                height={42}
              />
            </div>
            <div>
              <p className="footer-title">Puckcast.ai</p>
              <p className="footer-sub">Predictions &amp; Power Index</p>
            </div>
          </div>
          <p className="footer-copy">
            Daily AI-powered win probabilities and weekly power rankings built from real NHL data. Clarity for fans who want signal over noise.
          </p>
          <div className="footer-links">
            {links.map((link) => (
              <a key={link.href} href={link.href} className="footer-link">
                {link.label}
              </a>
            ))}
            <a href="mailto:hello@owshunlimited.com" className="footer-link">
              Contact
            </a>
          </div>
        </div>

        <div className="footer-right">
          <a className="footer-cta" href="https://x.com/puckcastai" target="_blank" rel="noreferrer">
            Follow on X
          </a>
          <div className="footer-meta">
            <span className="footer-note">Not affiliated with the NHL. Data from public NHL API. Analytics only, not betting advice.</span>
            <span className="footer-note">© {currentYear} Puckcast.ai · OWSH Unlimited LLC · {SITE_VERSION}</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
