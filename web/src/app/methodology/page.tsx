import insightsData from "@/data/modelInsights.json";
import type { ModelInsights } from "@/types/insights";

const modelInsights = insightsData as ModelInsights;

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

const methodologySteps = [
  {
    title: "Data Collection",
    description: "We aggregate game-level statistics from multiple sources including MoneyPuck (expected goals), NHL play-by-play data, and team performance metrics. Our dataset covers 6+ seasons (2018-2024) with over 7,000+ games.",
    icon: "📊",
  },
  {
    title: "Feature Engineering",
    description: "We transform raw statistics into 200+ predictive features including rolling averages, head-to-head matchups, rest days, home/away splits, recent form, and advanced metrics like Corsi, Fenwick, and expected goals (xG).",
    icon: "⚙️",
  },
  {
    title: "Model Training",
    description: "We use Logistic Regression with L2 regularization, trained on historical data with sample weights to emphasize recent seasons. The model learns which features best predict game outcomes through iterative optimization.",
    icon: "🧠",
  },
  {
    title: "Validation & Testing",
    description: "We validate performance using walk-forward testing on held-out seasons. Current season accuracy is tracked in real-time to ensure the model generalizes to new data, not just historical patterns.",
    icon: "✅",
  },
  {
    title: "Daily Predictions",
    description: "Each morning, we fetch the latest roster updates, injury reports, and goalie confirmations, then generate win probabilities for upcoming games. Predictions update automatically and publish to the site and X/Twitter.",
    icon: "🔄",
  },
];

const featureCategories = [
  {
    category: "Team Performance",
    examples: ["Rolling win rate (5/10/20 games)", "Goals for/against per game", "Shot differential", "Power play %", "Penalty kill %"],
  },
  {
    category: "Advanced Metrics",
    examples: ["Expected goals (xG) for/against", "Corsi for % (shot attempts)", "Fenwick for %", "PDO (shooting % + save %)", "High-danger scoring chances"],
  },
  {
    category: "Situational Factors",
    examples: ["Home/away splits", "Rest days between games", "Back-to-back games", "Travel distance", "Time zone changes"],
  },
  {
    category: "Head-to-Head",
    examples: ["Historical matchup results", "Goals scored in previous meetings", "Recent trend vs opponent", "Division/conference matchups"],
  },
];

const modelSpecs = [
  { label: "Algorithm", value: "Logistic Regression (L2)" },
  { label: "Features", value: "200+ engineered" },
  { label: "Training data", value: "6 seasons (2018-2024)" },
  { label: "Training games", value: "7,000+" },
  { label: "Regularization (C)", value: "1.0" },
  { label: "Solver", value: "LBFGS" },
];

const performanceMetrics = [
  {
    metric: "Current Season Accuracy",
    value: pct(modelInsights.overall.accuracy),
    description: "Percentage of correct predictions on 2025-26 games"
  },
  {
    metric: "Baseline (Always pick home)",
    value: pct(modelInsights.overall.baseline),
    description: "Home team winning percentage this season"
  },
  {
    metric: "Edge over baseline",
    value: `+${((modelInsights.overall.accuracy - modelInsights.overall.baseline) * 100).toFixed(1)} pts`,
    description: "Improvement over naive home-team strategy"
  },
  {
    metric: "Games Analyzed",
    value: modelInsights.overall.games.toLocaleString(),
    description: "Total number of games in current season sample"
  },
  {
    metric: "Log Loss",
    value: modelInsights.overall.logLoss.toFixed(3),
    description: "Probability calibration metric (lower is better)"
  },
  {
    metric: "Brier Score",
    value: modelInsights.overall.brier.toFixed(3),
    description: "Mean squared error of probability predictions (lower is better)"
  },
];

const limitations = [
  {
    title: "Unpredictable Events",
    detail: "The model cannot account for unexpected injuries during games, referee decisions, or random bounces that change outcomes.",
  },
  {
    title: "Small Sample Bias",
    detail: "Early season predictions may be less reliable due to limited 2025-26 data. Accuracy improves as the season progresses.",
  },
  {
    title: "Lineup Changes",
    detail: "Last-minute scratches or goalie changes after our morning update can impact accuracy. We refresh daily but cannot track real-time changes.",
  },
  {
    title: "Not a Betting Tool",
    detail: "Win probabilities are predictions, not betting advice. We don't incorporate betting odds or recommend specific wagers. Always bet responsibly.",
  },
];

export default function MethodologyPage() {
  return (
    <div className="relative overflow-hidden">
      <div className="relative mx-auto flex max-w-6xl flex-col gap-16 px-6 pb-16 pt-8 lg:px-12">
        <header>
          <p className="text-sm uppercase tracking-[0.4em] text-lime-300">How it works</p>
          <h1 className="mt-3 text-4xl font-semibold text-white sm:text-5xl">
            Transparent, data-driven NHL predictions.
          </h1>
          <p className="mt-4 max-w-3xl text-lg text-white/80">
            Puckcast uses machine learning to predict NHL game outcomes. This page explains our methodology,
            data sources, model architecture, and performance metrics — with full transparency about what works
            and what doesn't.
          </p>
        </header>

        <section className="rounded-[36px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30">
          <h2 className="text-2xl font-semibold text-white">Our Process</h2>
          <p className="mt-2 text-sm text-white/70">From raw data to daily predictions in 5 steps</p>
          <div className="mt-8 space-y-6">
            {methodologySteps.map((step, idx) => (
              <div key={step.title} className="rounded-3xl border border-white/10 bg-black/20 p-6">
                <div className="flex items-start gap-4">
                  <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-lime-300/20 to-emerald-400/20 text-2xl">
                    {step.icon}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-baseline gap-3">
                      <span className="text-sm uppercase tracking-[0.4em] text-white/50">Step {idx + 1}</span>
                      <h3 className="text-xl font-semibold text-white">{step.title}</h3>
                    </div>
                    <p className="mt-3 text-base leading-relaxed text-white/80">{step.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="grid gap-8 lg:grid-cols-2">
          <div className="rounded-[36px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30">
            <h2 className="text-2xl font-semibold text-white">Feature Engineering</h2>
            <p className="mt-2 text-sm text-white/70">Categories of predictive signals we extract from raw data</p>
            <div className="mt-6 space-y-5">
              {featureCategories.map((cat) => (
                <div key={cat.category} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                  <p className="text-sm font-semibold uppercase tracking-[0.4em] text-lime-300">{cat.category}</p>
                  <ul className="mt-3 space-y-1.5 text-sm text-white/75">
                    {cat.examples.map((example) => (
                      <li key={example} className="flex items-start gap-2">
                        <span className="text-lime-300">•</span>
                        <span>{example}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[36px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30">
            <h2 className="text-2xl font-semibold text-white">Model Specifications</h2>
            <p className="mt-2 text-sm text-white/70">Technical details of the prediction engine</p>
            <div className="mt-6 space-y-3">
              {modelSpecs.map((spec) => (
                <div key={spec.label} className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
                  <span className="text-sm uppercase tracking-[0.3em] text-white/60">{spec.label}</span>
                  <span className="text-base font-semibold text-white">{spec.value}</span>
                </div>
              ))}
            </div>
            <div className="mt-6 rounded-2xl bg-gradient-to-r from-lime-300/20 to-emerald-400/20 p-4">
              <p className="text-xs uppercase tracking-[0.4em] text-lime-200">Why Logistic Regression?</p>
              <p className="mt-2 text-sm text-white/85">
                We chose logistic regression for its interpretability, fast training, and excellent probability calibration.
                Unlike black-box models, we can inspect which features drive predictions and explain our reasoning transparently.
              </p>
            </div>
          </div>
        </section>

        <section className="rounded-[36px] border border-white/10 bg-gradient-to-br from-white/5 via-slate-900/40 to-slate-950 p-8 shadow-2xl shadow-black/30">
          <h2 className="text-2xl font-semibold text-white">Current Performance Metrics</h2>
          <p className="mt-2 text-sm text-white/70">Real-time tracking on 2025-26 season games</p>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {performanceMetrics.map((item) => (
              <div key={item.metric} className="rounded-3xl border border-white/10 bg-black/30 p-5">
                <p className="text-xs uppercase tracking-[0.5em] text-white/50">{item.metric}</p>
                <p className="mt-3 text-3xl font-semibold text-white">{item.value}</p>
                <p className="mt-2 text-xs leading-relaxed text-white/60">{item.description}</p>
              </div>
            ))}
          </div>
          <div className="mt-6 rounded-2xl border border-lime-200/30 bg-gradient-to-r from-lime-200/10 to-emerald-200/10 p-5">
            <p className="text-sm font-semibold text-white">
              ✅ Tested on {modelInsights.overall.games} real games from the 2025-26 season
            </p>
            <p className="mt-2 text-sm text-white/75">
              We track accuracy on actual NHL results throughout the season. Performance updates daily as new games complete.
            </p>
          </div>
        </section>

        <section className="rounded-[36px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30">
          <h2 className="text-2xl font-semibold text-white">Limitations & Transparency</h2>
          <p className="mt-2 text-sm text-white/70">What our model can't predict (and why honesty matters)</p>
          <div className="mt-6 grid gap-5 md:grid-cols-2">
            {limitations.map((item) => (
              <div key={item.title} className="rounded-2xl border border-white/10 bg-black/20 p-5">
                <p className="text-sm font-semibold uppercase tracking-[0.4em] text-amber-200">{item.title}</p>
                <p className="mt-3 text-sm leading-relaxed text-white/80">{item.detail}</p>
              </div>
            ))}
          </div>
          <div className="mt-6 rounded-2xl border border-white/10 bg-black/20 p-5">
            <p className="text-sm font-semibold text-white">Why we share this</p>
            <p className="mt-2 text-sm leading-relaxed text-white/75">
              Prediction models are tools, not crystal balls. We believe in transparent communication about what
              our model does well (identifying high-probability outcomes based on historical patterns) and what it
              cannot do (predict injuries, referee calls, or random variance). Use our predictions as one input
              among many when forming your own opinions about games.
            </p>
          </div>
        </section>

        <section className="rounded-[36px] border border-lime-200/30 bg-gradient-to-br from-lime-200/20 via-emerald-200/20 to-transparent p-10 text-center shadow-lg shadow-emerald-500/20">
          <h2 className="text-3xl font-semibold text-white">Questions about our methodology?</h2>
          <p className="mt-3 text-base text-white/80">
            We're committed to transparency and continuous improvement. Follow us on X for model updates,
            performance breakdowns, and behind-the-scenes insights into how we refine our predictions.
          </p>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-4">
            <a
              href="https://x.com/puckcastai"
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-full bg-white px-8 py-3 text-sm font-semibold uppercase tracking-[0.4em] text-slate-900 shadow-lg transition hover:bg-white/90"
            >
              Follow @puckcastai
            </a>
          </div>
        </section>
      </div>
    </div>
  );
}
