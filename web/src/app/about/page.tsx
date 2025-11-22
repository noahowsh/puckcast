import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";

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

        {/* Model Overview */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">How the model works</h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {[{ title: "Data collection", body: "Official NHL Stats API covering 3 seasons (2021-2024): play-by-play, player stats, team metrics, xG, Corsi, and situational splits." },
              { title: "Feature engineering", body: "204 features including Elo, rolling xG differential, goalie GSAx, rest days, home/away splits, special teams efficiency, travel distance, schedule strength." },
              { title: "Model training", body: "Logistic regression (C=1.0) on 2,460 games from 2021-2023. Simple, interpretable, and less prone to overfitting than black-box models." },
              { title: "Validation & testing", body: "Full 2023-24 season (1,230 games) held out for testing. Strict separation keeps real-world accuracy honest." }
            ].map((item) => (
              <div key={item.title} className="card">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-white/[0.04] flex items-center justify-center border border-white/10">
                    <svg className="w-5 h-5 text-sky-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-white">{item.title}</h3>
                </div>
                <p className="text-sm text-white/75 leading-relaxed">{item.body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Key Features */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">204 features explained</h2>
          <div className="card">
            <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
              <div>
                <h4 className="text-sm font-bold text-sky-300 uppercase mb-3">Team metrics</h4>
                <ul className="space-y-2 text-sm text-white/75">
                  <li>- Elo ratings (offense & defense)</li>
                  <li>- xG for/against (rolling windows)</li>
                  <li>- Power play & penalty kill %</li>
                  <li>- Corsi & Fenwick differentials</li>
                  <li>- Shots for/against per game</li>
                  <li>- Faceoff win percentage</li>
                </ul>
              </div>
              <div>
                <h4 className="text-sm font-bold text-cyan-300 uppercase mb-3">Goalie metrics</h4>
                <ul className="space-y-2 text-sm text-white/75">
                  <li>- Goals Saved Above Expected (GSAx)</li>
                  <li>- Save percentage (rolling)</li>
                  <li>- High-danger save %</li>
                  <li>- Games started in last 7 days</li>
                  <li>- Rest day advantage</li>
                  <li>- Home vs away splits</li>
                </ul>
              </div>
              <div>
                <h4 className="text-sm font-bold text-emerald-300 uppercase mb-3">Context factors</h4>
                <ul className="space-y-2 text-sm text-white/75">
                  <li>- Home ice advantage</li>
                  <li>- Back-to-back games</li>
                  <li>- Travel distance</li>
                  <li>- Days since last game</li>
                  <li>- Recent form (L5, L10)</li>
                  <li>- Schedule strength</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Performance Highlights */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Performance highlights</h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Test accuracy" value="59.3%" change={{ value: "vs 53.7% baseline", isPositive: true }} />
            <StatCard label="A+ confidence" value="69.5%" change={{ value: "20+ pt edges", isPositive: true }} />
            <StatCard label="Log loss" value="0.676" change={{ value: "Calibration", isPositive: true }} />
            <StatCard label="Test games" value="1,230" change={{ value: "2023-24 season", isPositive: true }} />
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
      "We generate fresh predictions daily at 11:00 AM UTC (6:00 AM ET) via automated GitHub Actions. The model pulls the latest stats from the NHL API and recalculates all 204 features before making predictions.",
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
