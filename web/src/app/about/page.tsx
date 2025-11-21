import Link from "next/link";
import { PageHeader } from "@/components/PageHeader";

export default function AboutPage() {
  return (
    <div className="min-h-screen">
      <div className="container" style={{ paddingTop: '6rem' }}>
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
        <section className="mb-12 max-w-4xl mx-auto">
          <div className="card-elevated text-center">
            <h2 className="text-3xl font-bold text-white mb-4">Our Mission</h2>
            <p className="text-lg text-slate-300 leading-relaxed">
              To bring transparency and data-driven insights to NHL analytics. We believe in open methodology,
              honest accuracy reporting, and helping fans understand the game through the lens of machine learning.
            </p>
          </div>
        </section>

        {/* Model Overview */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">How The Model Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-sky-500/20 flex items-center justify-center">
                  <svg className="w-5 h-5 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-white">Data Collection</h3>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed">
                We pull data directly from the official NHL Stats API covering 3 seasons (2021-2024). This includes
                play-by-play events, player stats, team metrics, and advanced analytics like expected goals (xG) and
                Corsi numbers.
              </p>
            </div>

            <div className="card">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center">
                  <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-white">Feature Engineering</h3>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed">
                We engineer 204 features including: Elo ratings, rolling xG differentials, goalie GSAx (Goals Saved
                Above Expected), rest days, home/away splits, power play efficiency, and schedule difficulty metrics.
              </p>
            </div>

            <div className="card">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                  <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-white">Model Training</h3>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed">
                We use logistic regression (C=1.0) trained on 2,460 games from 2021-2023 seasons. The model is
                intentionally kept simple and interpretable - no black box neural networks. You can understand
                exactly what drives each prediction.
              </p>
            </div>

            <div className="card">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-amber-500/20 flex items-center justify-center">
                  <svg className="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-white">Validation & Testing</h3>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed">
                We hold out the entire 2023-24 season (1,230 games) as a test set to measure real-world accuracy.
                This strict separation ensures we're not overfitting. Result: 59.3% accuracy vs 53.7% baseline.
              </p>
            </div>
          </div>
        </section>

        {/* Key Features */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">204 Features Explained</h2>
          <div className="card">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <h4 className="text-sm font-bold text-sky-400 uppercase mb-3">Team Metrics</h4>
                <ul className="space-y-2 text-sm text-slate-300">
                  <li>• Elo ratings (offensive & defensive)</li>
                  <li>• xG for/against (rolling windows)</li>
                  <li>• Power play & penalty kill %</li>
                  <li>• Corsi & Fenwick differentials</li>
                  <li>• Shots for/against per game</li>
                  <li>• Faceoff win percentage</li>
                </ul>
              </div>
              <div>
                <h4 className="text-sm font-bold text-cyan-400 uppercase mb-3">Goalie Metrics</h4>
                <ul className="space-y-2 text-sm text-slate-300">
                  <li>• Goals Saved Above Expected (GSAx)</li>
                  <li>• Save percentage (rolling)</li>
                  <li>• High-danger save %</li>
                  <li>• Games started in last 7 days</li>
                  <li>• Rest day advantage</li>
                  <li>• Home vs away splits</li>
                </ul>
              </div>
              <div>
                <h4 className="text-sm font-bold text-green-400 uppercase mb-3">Context Factors</h4>
                <ul className="space-y-2 text-sm text-slate-300">
                  <li>• Home ice advantage</li>
                  <li>• Back-to-back games</li>
                  <li>• Travel distance</li>
                  <li>• Days since last game</li>
                  <li>• Recent form (L5, L10)</li>
                  <li>• Schedule strength</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Performance Highlights */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Performance Highlights</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="stat-card">
              <div className="stat-label">Test Accuracy</div>
              <div className="stat-value">59.3%</div>
              <div className="text-sm text-slate-400 mt-2">vs 53.7% baseline</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">A+ Confidence</div>
              <div className="stat-value">69.5%</div>
              <div className="text-sm text-slate-400 mt-2">≥20pt edge games</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Log Loss</div>
              <div className="stat-value">0.676</div>
              <div className="text-sm text-slate-400 mt-2">Calibration metric</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Test Games</div>
              <div className="stat-value">1,230</div>
              <div className="text-sm text-slate-400 mt-2">2023-24 season</div>
            </div>
          </div>
        </section>

        {/* Tech Stack */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Tech Stack</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-lg font-bold text-white mb-4">Machine Learning</h3>
              <ul className="space-y-2 text-sm text-slate-300">
                <li>• <strong>Python 3.11</strong> - Core language</li>
                <li>• <strong>scikit-learn</strong> - Logistic regression model</li>
                <li>• <strong>pandas & numpy</strong> - Data processing</li>
                <li>• <strong>NHL Stats API</strong> - Official data source</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="text-lg font-bold text-white mb-4">Frontend</h3>
              <ul className="space-y-2 text-sm text-slate-300">
                <li>• <strong>Next.js 16</strong> - React framework</li>
                <li>• <strong>TypeScript</strong> - Type safety</li>
                <li>• <strong>Tailwind CSS v4</strong> - Styling</li>
                <li>• <strong>Vercel</strong> - Hosting & deployment</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Limitations */}
        <section className="mb-12">
          <div className="card bg-amber-500/5 border-amber-500/20">
            <h2 className="text-2xl font-bold text-white mb-4">Known Limitations</h2>
            <p className="text-slate-300 mb-4 leading-relaxed">
              We believe in radical transparency. Here's what our model can't do:
            </p>
            <ul className="space-y-2 text-sm text-slate-300">
              <li>• <strong>Last-minute injuries:</strong> We can't predict surprise scratches announced 30 minutes before puck drop</li>
              <li>• <strong>Intangibles:</strong> Rivalry games, playoff implications, and "must-win" scenarios aren't fully captured</li>
              <li>• <strong>Lineup changes:</strong> Mid-game adjustments and line shuffles can't be predicted</li>
              <li>• <strong>Randomness:</strong> Hockey has high variance - a 60% prediction will still lose 40% of the time</li>
              <li>• <strong>Future uncertainty:</strong> Past performance doesn't guarantee future results</li>
            </ul>
          </div>
        </section>

        {/* FAQs */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Frequently Asked Questions</h2>
          <div className="space-y-4">
            <details className="card group">
              <summary className="cursor-pointer font-semibold text-white list-none flex items-center justify-between">
                <span>How often do you update predictions?</span>
                <svg className="w-5 h-5 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </summary>
              <p className="mt-4 text-sm text-slate-300 leading-relaxed">
                We generate fresh predictions daily at 11:00 AM UTC (6:00 AM ET) via automated GitHub Actions. The model
                pulls the latest stats from the NHL API and recalculates all 204 features before making predictions.
              </p>
            </details>

            <details className="card group">
              <summary className="cursor-pointer font-semibold text-white list-none flex items-center justify-between">
                <span>Do you sell picks or betting advice?</span>
                <svg className="w-5 h-5 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </summary>
              <p className="mt-4 text-sm text-slate-300 leading-relaxed">
                No. Puckcast is purely an analytics and educational platform. We don't sell picks, offer betting advice,
                or take a cut of any wagers. Everything is free and transparent.
              </p>
            </details>

            <details className="card group">
              <summary className="cursor-pointer font-semibold text-white list-none flex items-center justify-between">
                <span>Is the source code open source?</span>
                <svg className="w-5 h-5 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </summary>
              <p className="mt-4 text-sm text-slate-300 leading-relaxed">
                Yes! The entire codebase is available on{" "}
                <a
                  href="https://github.com/noahowsh/puckcast"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sky-400 hover:underline"
                >
                  GitHub
                </a>
                . You can inspect the model training code, feature engineering pipeline, and website frontend.
              </p>
            </details>

            <details className="card group">
              <summary className="cursor-pointer font-semibold text-white list-none flex items-center justify-between">
                <span>Why logistic regression instead of neural networks?</span>
                <svg className="w-5 h-5 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </summary>
              <p className="mt-4 text-sm text-slate-300 leading-relaxed">
                Interpretability. With logistic regression, we can see exactly which features drive each prediction
                (feature coefficients). Neural networks are black boxes. For sports prediction, understanding the "why"
                is as important as the "what." Plus, logistic regression is less prone to overfitting on limited data.
              </p>
            </details>
          </div>
        </section>

        {/* Contact */}
        <section className="mb-12">
          <div className="card-elevated bg-sky-500/5 border-sky-500/20 text-center max-w-2xl mx-auto">
            <h2 className="text-2xl font-bold text-white mb-4">Get In Touch</h2>
            <p className="text-slate-300 mb-6">
              Questions, feedback, or just want to chat about hockey analytics? We'd love to hear from you.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-4">
              <a
                href="https://x.com/puckcastai"
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-primary"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                </svg>
                Follow on X
              </a>
              <a
                href="https://github.com/noahowsh/puckcast"
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-secondary"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
                View on GitHub
              </a>
              <a
                href="mailto:team@puckcast.ai"
                className="btn btn-ghost"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                Email Us
              </a>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
