import { PageHeader } from "@/components/PageHeader";

export default function AboutPage() {
  return (
    <div className="min-h-screen">
      <div className="container" style={{ paddingTop: "8rem" }}>
        <PageHeader
          title="About Puckcast"
          description="Transparency, methodology, and the story behind our NHL prediction model."
          icon={
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />

        {/* Mission */}
        <section className="mb-12">
          <div className="card-elevated text-center max-w-4xl mx-auto">
            <h2 className="text-3xl font-bold text-white mb-4">Our mission</h2>
            <p className="text-lg text-white/75 leading-relaxed">
              Bring transparency and data-first storytelling to NHL analytics. We share the full methodology, publish accuracy honestly, and help fans
              read the game through machine learning without the jargon overload.
            </p>
          </div>
        </section>

        {/* Model Pipeline Visualization */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">How the model works</h2>
          <div className="card-elevated">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', flexWrap: 'wrap', padding: '1.5rem 0' }}>
              {[
                { icon: '📊', label: 'NHL API', desc: '8 seasons of data' },
                { icon: '⚙️', label: '39 Features', desc: 'Engineered signals' },
                { icon: '🧠', label: 'Training', desc: '4-season window' },
                { icon: '🎯', label: 'Calibration', desc: 'Isotonic regression' },
                { icon: '📈', label: 'Prediction', desc: '60.9% accuracy' },
              ].map((step, idx) => (
                <div key={step.label} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    padding: '1rem 1.5rem',
                    background: 'rgba(126, 227, 255, 0.08)',
                    border: '1px solid rgba(126, 227, 255, 0.2)',
                    borderRadius: '0.75rem',
                    minWidth: '120px'
                  }}>
                    <span style={{ fontSize: '1.75rem', marginBottom: '0.5rem' }}>{step.icon}</span>
                    <span style={{ fontWeight: 700, color: 'var(--aqua)', fontSize: '0.9rem' }}>{step.label}</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginTop: '0.25rem' }}>{step.desc}</span>
                  </div>
                  {idx < 4 && (
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" style={{ color: 'var(--text-tertiary)', flexShrink: 0 }}>
                      <path d="M9 18l6-6-6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Accuracy Comparison Visual */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Model vs baseline</h2>
          <div className="card-elevated">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', alignItems: 'center' }}>
              {/* Bar comparison */}
              <div>
                <div style={{ marginBottom: '1.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Home team baseline</span>
                    <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-tertiary)' }}>53.9%</span>
                  </div>
                  <div style={{ height: '2rem', background: 'rgba(255,255,255,0.1)', borderRadius: '0.5rem', overflow: 'hidden' }}>
                    <div style={{ width: '53.9%', height: '100%', background: 'rgba(255,255,255,0.3)', borderRadius: '0.5rem' }} />
                  </div>
                </div>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--aqua)' }}>Puckcast V7.0</span>
                    <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--mint)' }}>60.9%</span>
                  </div>
                  <div style={{ height: '2rem', background: 'rgba(255,255,255,0.1)', borderRadius: '0.5rem', overflow: 'hidden' }}>
                    <div style={{ width: '60.9%', height: '100%', background: 'linear-gradient(90deg, var(--aqua), var(--mint))', borderRadius: '0.5rem' }} />
                  </div>
                </div>
              </div>
              {/* Stats */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ textAlign: 'center', padding: '1.25rem', background: 'rgba(110, 240, 194, 0.1)', borderRadius: '0.75rem', border: '1px solid rgba(110, 240, 194, 0.2)' }}>
                  <p style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--mint)', lineHeight: 1 }}>+7.0</p>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>percentage points above baseline</p>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div style={{ textAlign: 'center', padding: '0.75rem', background: 'rgba(255,255,255,0.04)', borderRadius: '0.5rem' }}>
                    <p style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>5,002</p>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>test games</p>
                  </div>
                  <div style={{ textAlign: 'center', padding: '0.75rem', background: 'rgba(255,255,255,0.04)', borderRadius: '0.5rem' }}>
                    <p style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>0.655</p>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>log loss</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Key Features with Visual Breakdown */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">39 features explained (V7.0)</h2>
          <div className="card-elevated">
            <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '2rem', alignItems: 'start' }}>
              {/* Donut Chart Visual */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <svg viewBox="0 0 100 100" style={{ width: '160px', height: '160px' }}>
                  {/* Background circle */}
                  <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="12" />
                  {/* Elo segment (7/39 = 18%) - blue */}
                  <circle cx="50" cy="50" r="40" fill="none" stroke="rgb(56, 189, 248)" strokeWidth="12"
                    strokeDasharray="45.2 251.3" strokeDashoffset="0" transform="rotate(-90 50 50)" />
                  {/* Rolling segment (20/39 = 51%) - cyan */}
                  <circle cx="50" cy="50" r="40" fill="none" stroke="rgb(34, 211, 238)" strokeWidth="12"
                    strokeDasharray="128.7 251.3" strokeDashoffset="-45.2" transform="rotate(-90 50 50)" />
                  {/* Rest segment (12/39 = 31%) - green */}
                  <circle cx="50" cy="50" r="40" fill="none" stroke="rgb(52, 211, 153)" strokeWidth="12"
                    strokeDasharray="77.4 251.3" strokeDashoffset="-173.9" transform="rotate(-90 50 50)" />
                  {/* Center text */}
                  <text x="50" y="46" textAnchor="middle" fill="white" fontSize="16" fontWeight="bold">39</text>
                  <text x="50" y="58" textAnchor="middle" fill="rgba(255,255,255,0.6)" fontSize="7">features</text>
                </svg>
                {/* Legend */}
                <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.8rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div style={{ width: '12px', height: '12px', borderRadius: '2px', background: 'rgb(56, 189, 248)' }} />
                    <span style={{ color: 'var(--text-secondary)' }}>Elo (7)</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div style={{ width: '12px', height: '12px', borderRadius: '2px', background: 'rgb(34, 211, 238)' }} />
                    <span style={{ color: 'var(--text-secondary)' }}>Rolling (20)</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div style={{ width: '12px', height: '12px', borderRadius: '2px', background: 'rgb(52, 211, 153)' }} />
                    <span style={{ color: 'var(--text-secondary)' }}>Rest & Goalie (12)</span>
                  </div>
                </div>
              </div>
              {/* Feature lists */}
              <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
                <div>
                  <h4 className="text-sm font-bold text-sky-400 uppercase mb-3">Elo & Team Strength (7)</h4>
                  <ul className="space-y-2 text-sm text-white/75">
                    <li>• League home win rate</li>
                    <li>• Elo ratings (50% carryover)</li>
                    <li>• Elo expectation</li>
                    <li>• Season win pct diff</li>
                    <li>• Goal differential</li>
                    <li>• xG differential</li>
                    <li>• Shot margin</li>
                  </ul>
                </div>
                <div>
                  <h4 className="text-sm font-bold text-cyan-400 uppercase mb-3">Rolling Stats (20)</h4>
                  <ul className="space-y-2 text-sm text-white/75">
                    <li>• Win pct (3, 5, 10 game)</li>
                    <li>• Goal diff (3, 5, 10 game)</li>
                    <li>• xG diff (3, 5, 10 game)</li>
                    <li>• Corsi/Fenwick metrics</li>
                    <li>• High-danger shots</li>
                    <li>• Faceoff % (5 game)</li>
                    <li>• Shot volume (10 game)</li>
                  </ul>
                </div>
                <div>
                  <h4 className="text-sm font-bold text-emerald-400 uppercase mb-3">Rest & Goaltending (12)</h4>
                  <ul className="space-y-2 text-sm text-white/75">
                    <li>• Rest days differential</li>
                    <li>• Back-to-back flags</li>
                    <li>• Games in last 3/6 days</li>
                    <li>• Save pct rolling diffs</li>
                    <li>• Goalie GSAx (5, 10)</li>
                    <li>• Goalie trend scoring</li>
                    <li>• Momentum indicators</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Confidence Tiers Visual */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Confidence tiers</h2>
          <div className="card-elevated">
            <p className="text-white/70 mb-6">Higher confidence = higher historical accuracy. Our grading system helps you focus on the best opportunities.</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {[
                { grade: 'A+', range: '≥25 pts', accuracy: 79.3, color: 'var(--aqua)', games: 333 },
                { grade: 'A', range: '20-25 pts', accuracy: 72.0, color: 'var(--aqua)', games: 404 },
                { grade: 'B+', range: '15-20 pts', accuracy: 67.3, color: 'var(--amber)', games: 687 },
                { grade: 'B', range: '10-15 pts', accuracy: 62.0, color: 'var(--amber)', games: 975 },
                { grade: 'C+', range: '5-10 pts', accuracy: 57.8, color: 'rgba(255,255,255,0.4)', games: 1231 },
                { grade: 'C', range: '0-5 pts', accuracy: 51.9, color: 'rgba(255,255,255,0.25)', games: 1372 },
              ].map((tier) => (
                <div key={tier.grade} style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <span style={{
                    width: '2.5rem',
                    fontSize: '0.95rem',
                    fontWeight: 800,
                    color: tier.color
                  }}>{tier.grade}</span>
                  <span style={{ width: '5rem', fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>{tier.range}</span>
                  <div style={{ flex: 1, height: '1.5rem', background: 'rgba(255,255,255,0.08)', borderRadius: '0.375rem', overflow: 'hidden' }}>
                    <div style={{
                      width: `${tier.accuracy}%`,
                      height: '100%',
                      background: tier.grade.startsWith('A') ? 'linear-gradient(90deg, var(--aqua), var(--mint))' : tier.grade.startsWith('B') ? 'var(--amber)' : 'rgba(255,255,255,0.3)',
                      borderRadius: '0.375rem',
                      transition: 'width 0.3s ease'
                    }} />
                  </div>
                  <span style={{ width: '3.5rem', fontSize: '0.9rem', fontWeight: 700, textAlign: 'right' }}>{tier.accuracy}%</span>
                  <span style={{ width: '4rem', fontSize: '0.75rem', color: 'var(--text-tertiary)', textAlign: 'right' }}>{tier.games} games</span>
                </div>
              ))}
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginTop: '1rem', textAlign: 'center' }}>
              Based on 5,002 holdout games across 4 seasons
            </p>
          </div>
        </section>

        {/* Tech Stack */}
        <section className="mb-12 grid gap-6 md:grid-cols-2">
          <div className="card">
            <h3 className="text-lg font-bold text-white mb-4">Machine learning</h3>
            <ul className="space-y-2 text-sm text-white/75">
              <li>- Python 3.11</li>
              <li>- scikit-learn (logistic regression)</li>
              <li>- pandas & numpy</li>
              <li>- NHL Stats API (official data)</li>
            </ul>
          </div>

          <div className="card">
            <h3 className="text-lg font-bold text-white mb-4">Frontend</h3>
            <ul className="space-y-2 text-sm text-white/75">
              <li>- Next.js 16 + TypeScript</li>
              <li>- Tailwind CSS v4</li>
              <li>- Vercel hosting</li>
            </ul>
          </div>
        </section>

        {/* Limitations */}
        <section className="mb-12">
          <div className="card bg-amber-500/5 border-amber-500/20">
            <h2 className="text-2xl font-bold text-white mb-3">Known limitations</h2>
            <p className="text-white/75 mb-4 leading-relaxed">What the model cannot do:</p>
            <ul className="space-y-2 text-sm text-white/75">
              <li>- Last-minute injuries: cannot predict surprise scratches announced near puck drop.</li>
              <li>- Intangibles: rivalry games and playoff emotions are not fully captured.</li>
              <li>- Lineup changes: mid-game adjustments and line shuffles are unpredictable.</li>
              <li>- Randomness: a 60% prediction still loses 40% of the time.</li>
              <li>- Future uncertainty: past performance does not guarantee future results.</li>
            </ul>
          </div>
        </section>

        {/* FAQs */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-4">Frequently asked questions</h2>
          <div className="space-y-4">
            {faqItems.map((item) => (
              <details key={item.question} className="card group">
                <summary className="cursor-pointer font-semibold text-white list-none flex items-center justify-between">
                  <span>{item.question}</span>
                  <svg className="w-5 h-5 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </summary>
                <p className="mt-4 text-sm text-white/75 leading-relaxed">{item.answer}</p>
              </details>
            ))}
          </div>
        </section>

        {/* Contact */}
        <section className="mb-12">
          <div className="card-elevated bg-sky-500/5 border-sky-500/20 text-center max-w-2xl mx-auto">
            <h2 className="text-2xl font-bold text-white mb-4">Get in touch</h2>
            <p className="text-white/75 mb-6">Questions, feedback, or just want to chat hockey analytics? We would love to hear from you.</p>
            <div className="flex flex-wrap items-center justify-center gap-4">
              <a href="https://x.com/puckcastai" target="_blank" rel="noopener noreferrer" className="btn btn-primary">
                Follow on X
              </a>
              <a href="https://github.com/noahowsh/puckcast" target="_blank" rel="noopener noreferrer" className="btn btn-secondary">
                View on GitHub
              </a>
              <a href="mailto:team@puckcast.ai" className="btn btn-ghost">
                Email us
              </a>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

const faqItems = [
  {
    question: "How often do you update predictions?",
    answer:
      "We generate fresh predictions daily at 10:00 AM and 10:00 PM UTC via automated GitHub Actions. The model pulls the latest stats from the NHL API and recalculates all 39 curated features (V7.0) before making predictions.",
  },
  {
    question: "Do you sell picks or betting advice?",
    answer:
      "No. Puckcast is an analytics and educational platform. We do not sell picks, offer betting advice, or take a cut of wagers.",
  },
  {
    question: "Is the source code open source?",
    answer:
      "Yes. The entire codebase is available on GitHub. You can inspect the model training code, feature engineering pipeline, and website frontend.",
  },
  {
    question: "Why logistic regression instead of neural networks?",
    answer:
      "Interpretability. Logistic regression exposes feature coefficients and is less prone to overfitting on limited data. For sports prediction, knowing why matters as much as what.",
  },
];
