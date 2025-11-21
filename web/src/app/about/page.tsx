import Link from "next/link";
import insightsData from "@/data/modelInsights.json";
import type { ModelInsights } from "@/types/insights";

const modelInsights = insightsData as ModelInsights;
const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

const timeline = [
  {
    date: "November 2024",
    title: "Project Launch",
    description: "Started building a machine learning model to predict NHL games using historical data and advanced statistics.",
  },
  {
    date: "December 2024",
    title: "V1.0 Model",
    description: "Deployed first logistic regression model trained on 3 seasons of data, achieving ~57% accuracy on held-out test data.",
  },
  {
    date: "January 2025",
    title: "V2.0 Site & Expansion",
    description: "Launched this website with daily prediction updates, real-time performance tracking, and automated X/Twitter posts.",
  },
];

const principles = [
  {
    title: "Transparency First",
    description: "We openly share our performance metrics and limitations. No black boxes, no hidden formulas, no misleading claims.",
    icon: "🔍",
  },
  {
    title: "Data-Driven",
    description: "Every prediction is grounded in historical data and statistical patterns. We let the numbers speak rather than gut feelings.",
    icon: "📊",
  },
  {
    title: "Continuous Improvement",
    description: "We track real-time performance and refine our model as we learn. Accuracy metrics update daily with honest reporting.",
    icon: "🔄",
  },
  {
    title: "Accessible Insights",
    description: "Complex machine learning made simple. We explain predictions in plain language with context you can understand.",
    icon: "💡",
  },
];

const howItWorks = [
  {
    title: "Data Collection",
    description: "We aggregate game-level statistics from the official NHL API including team performance, advanced metrics, and situational factors.",
    icon: "📊",
  },
  {
    title: "Pattern Recognition",
    description: "Our machine learning model identifies patterns in historical data that correlate with game outcomes — things like recent form, rest days, and head-to-head matchups.",
    icon: "🧠",
  },
  {
    title: "Win Probability",
    description: "Each morning, we generate win probabilities for today's games using the latest roster updates and goalie confirmations.",
    icon: "🎯",
  },
  {
    title: "Real-Time Tracking",
    description: "We validate performance on actual NHL results throughout the season, tracking accuracy in real-time with full transparency.",
    icon: "📈",
  },
];

const performanceHighlights = [
  {
    metric: "Test Accuracy",
    value: pct(modelInsights.overall.accuracy),
    description: "Current season performance"
  },
  {
    metric: "Edge over baseline",
    value: `+${((modelInsights.overall.accuracy - modelInsights.overall.baseline) * 100).toFixed(1)} pts`,
    description: "vs. always picking home team"
  },
  {
    metric: "Games Analyzed",
    value: modelInsights.overall.games.toLocaleString(),
    description: "Real NHL games tracked"
  },
];

const tech = [
  { label: "Backend", value: "Python, scikit-learn, pandas" },
  { label: "Data Source", value: "NHL API (play-by-play)" },
  { label: "Frontend", value: "Next.js 16, React 19, Tailwind CSS" },
  { label: "Deployment", value: "Vercel (auto-deploy)" },
  { label: "Automation", value: "GitHub Actions (daily updates)" },
];

const faqs = [
  {
    question: "Is this a betting tool?",
    answer: "No. We provide win probabilities based on historical data, but we're not a betting service. We don't offer betting advice, incorporate odds, or recommend wagers. Always bet responsibly if you choose to use our predictions as one input among many.",
  },
  {
    question: "How accurate are your predictions?",
    answer: "Our current accuracy is tracked in real-time on the Performance page. Historically, we've achieved 55-60% accuracy on held-out test data, which represents a meaningful edge over baseline. Performance varies by confidence level — stronger predictions (higher probability differences) tend to be more accurate.",
  },
  {
    question: "What data do you use?",
    answer: "We use official NHL API data including play-by-play statistics, team performance metrics, and situational factors like rest days and home/away splits. Our training dataset includes multiple seasons with thousands of games.",
  },
  {
    question: "How do you make predictions?",
    answer: "We use machine learning (logistic regression) trained on historical NHL data. The model learns patterns that correlate with wins/losses, then applies those patterns to predict upcoming games. We keep our exact feature set proprietary, but focus on team performance, recent form, and situational factors.",
  },
  {
    question: "How often do predictions update?",
    answer: "Once per day, typically around 10am ET after morning skates, goalie confirmations, and injury reports settle. We don't update intraday to avoid chasing last-minute noise.",
  },
  {
    question: "Can I access historical predictions?",
    answer: "We're working on an archive feature. Currently, daily predictions are published each morning and results are tracked in aggregate. Follow @puckcastai on X for daily updates.",
  },
];

export default function AboutPage() {
  return (
    <div className="relative min-h-screen bg-slate-950">
      {/* Subtle background gradient */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-b from-sky-950/20 via-slate-950 to-slate-950" />
      </div>

      <div className="relative mx-auto max-w-7xl px-6 py-16 lg:px-8">
        {/* Header */}
        <section className="mb-20">
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-sky-500/20 bg-sky-500/5 px-3 py-1">
            <span className="text-xs font-medium text-sky-400">About Puckcast</span>
          </div>
          <h1 className="mb-4 text-4xl font-bold text-white lg:text-5xl">
            Machine learning for hockey fans who love the numbers
          </h1>
          <p className="max-w-3xl text-lg text-slate-300">
            Puckcast is a passion project built by data enthusiasts who wanted to bring transparent,
            accessible NHL predictions to the hockey community. We combine machine learning with
            advanced statistics to predict game outcomes — and we share everything openly.
          </p>
        </section>

        {/* Mission */}
        <section className="mb-20">
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
            <h2 className="mb-4 text-2xl font-bold text-white">Our Mission</h2>
            <p className="mb-4 max-w-3xl text-sm leading-relaxed text-slate-300">
              We believe hockey predictions should be transparent, data-driven, and accessible. Too many
              prediction models are black boxes that hide their methods and cherry-pick results. We're
              different. We track real-time accuracy on current games and openly discuss what we get right and wrong.
            </p>
            <p className="max-w-3xl text-sm leading-relaxed text-slate-300">
              Our goal is simple: give hockey fans a better understanding of game probabilities using
              historical data and statistical patterns. Whether you're casually following your team,
              analyzing matchups, or just love the numbers, we want to make predictions you can trust
              and understand.
            </p>
          </div>
        </section>

        <section className="rounded-[36px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30">
          <h2 className="text-2xl font-semibold text-white">Our Principles</h2>
          <div className="mt-8 grid gap-6 md:grid-cols-2">
            {principles.map((principle) => (
              <div key={principle.title} className="rounded-3xl border border-white/10 bg-black/20 p-6">
                <div className="flex items-start gap-4">
                  <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-lime-300/20 to-emerald-400/20 text-2xl">
                    {principle.icon}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">{principle.title}</h3>
                    <p className="mt-2 text-sm leading-relaxed text-white/75">{principle.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-[36px] border border-white/10 bg-gradient-to-br from-white/5 via-slate-900/40 to-slate-950 p-8 shadow-2xl shadow-black/30">
          <h2 className="text-2xl font-semibold text-white">How It Works</h2>
          <p className="mt-2 text-sm text-white/70">Our prediction process in 4 steps</p>
          <div className="mt-8 grid gap-6 md:grid-cols-2">
            {howItWorks.map((step, idx) => (
              <div key={step.title} className="rounded-3xl border border-white/10 bg-black/20 p-6">
                <div className="flex items-start gap-4">
                  <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-lime-300/20 to-emerald-400/20 text-2xl">
                    {step.icon}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-white">{step.title}</h3>
                    <p className="mt-2 text-sm leading-relaxed text-white/75">{step.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            {performanceHighlights.map((item) => (
              <div key={item.metric} className="rounded-3xl border border-white/10 bg-black/30 p-5 text-center">
                <p className="text-xs uppercase tracking-[0.5em] text-white/50">{item.metric}</p>
                <p className="mt-3 text-3xl font-semibold text-lime-300">{item.value}</p>
                <p className="mt-2 text-xs leading-relaxed text-white/60">{item.description}</p>
              </div>
            ))}
          </div>

          <div className="mt-6 rounded-2xl bg-gradient-to-r from-lime-300/20 to-emerald-400/20 p-4">
            <p className="text-xs uppercase tracking-[0.4em] text-lime-200">Transparent Performance</p>
            <p className="mt-2 text-sm text-white/85">
              We track accuracy on real NHL games throughout the season. No cherry-picking, no hiding losses —
              just honest performance metrics that update daily. See detailed breakdowns on our Performance page.
            </p>
          </div>
        </section>

        <section className="rounded-[36px] border border-white/10 bg-gradient-to-br from-white/5 via-slate-900/40 to-slate-950 p-8 shadow-2xl shadow-black/30">
          <h2 className="text-2xl font-semibold text-white">Project Timeline</h2>
          <p className="mt-2 text-sm text-white/70">How we got here</p>
          <div className="mt-8 space-y-6">
            {timeline.map((milestone, idx) => (
              <div key={milestone.date} className="flex gap-6">
                <div className="flex flex-col items-center">
                  <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full border-2 border-lime-300 bg-black text-sm font-semibold text-lime-300">
                    {idx + 1}
                  </div>
                  {idx < timeline.length - 1 && <div className="mt-2 h-full w-0.5 bg-white/10" />}
                </div>
                <div className="flex-1 pb-6">
                  <p className="text-xs uppercase tracking-[0.4em] text-white/50">{milestone.date}</p>
                  <h3 className="mt-1 text-lg font-semibold text-white">{milestone.title}</h3>
                  <p className="mt-2 text-sm text-white/75">{milestone.description}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="grid gap-8 lg:grid-cols-2">
          <div className="rounded-[36px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30">
            <h2 className="text-2xl font-semibold text-white">Technology Stack</h2>
            <div className="mt-6 space-y-3">
              {tech.map((item) => (
                <div key={item.label} className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
                  <span className="text-sm uppercase tracking-[0.3em] text-white/60">{item.label}</span>
                  <span className="text-sm font-medium text-white">{item.value}</span>
                </div>
              ))}
            </div>
            <div className="mt-6 rounded-2xl bg-gradient-to-r from-lime-300/20 to-emerald-400/20 p-4">
              <p className="text-xs uppercase tracking-[0.4em] text-lime-200">Built for Speed & Reliability</p>
              <p className="mt-2 text-sm text-white/85">
                Modern tech stack optimized for fast load times, daily automation, and seamless deployment.
                Every push to main auto-deploys to production via Vercel.
              </p>
            </div>
          </div>

          <div className="rounded-[36px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30">
            <h2 className="text-2xl font-semibold text-white">Limitations</h2>
            <p className="mt-2 text-sm text-white/70">What we can't predict</p>
            <div className="mt-6 space-y-4">
              <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                <p className="text-sm font-semibold text-amber-200">Unpredictable Events</p>
                <p className="mt-2 text-xs text-white/75">Injuries, referee decisions, and random bounces can change outcomes in ways no model can predict.</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                <p className="text-sm font-semibold text-amber-200">Last-Minute Changes</p>
                <p className="mt-2 text-xs text-white/75">Scratches or goalie changes after our morning update can impact accuracy. We refresh daily but can't track real-time changes.</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                <p className="text-sm font-semibold text-amber-200">Not a Betting Tool</p>
                <p className="mt-2 text-xs text-white/75">Win probabilities are predictions, not betting advice. We don't incorporate odds or recommend wagers. Bet responsibly.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="rounded-[36px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30">
          <h2 className="text-2xl font-semibold text-white">Frequently Asked Questions</h2>
          <div className="mt-6 space-y-5">
            {faqs.map((faq) => (
              <details key={faq.question} className="group rounded-2xl border border-white/10 bg-black/20 p-5">
                <summary className="cursor-pointer text-base font-semibold text-white group-open:text-lime-300">
                  {faq.question}
                </summary>
                <p className="mt-3 text-sm leading-relaxed text-white/75">{faq.answer}</p>
              </details>
            ))}
          </div>
        </section>

        <section className="rounded-[36px] border border-lime-200/30 bg-gradient-to-br from-lime-200/20 via-emerald-200/20 to-transparent p-10 text-center shadow-lg shadow-emerald-500/20">
          <h2 className="text-3xl font-semibold text-white">Stay Connected</h2>
          <p className="mt-3 text-base text-white/80">
            Follow @puckcastai on X for daily predictions, post-game results, performance updates,
            and behind-the-scenes insights into how we refine the model.
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
            <Link
              href="/performance"
              className="rounded-full border border-white/20 px-8 py-3 text-sm font-semibold uppercase tracking-[0.4em] text-white/80 transition hover:text-white"
            >
              View Performance
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
