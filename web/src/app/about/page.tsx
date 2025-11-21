import Link from "next/link";

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
    description: "Expanded to 6 seasons of training data, launched this website, and began daily prediction updates with X/Twitter automation.",
  },
];

const principles = [
  {
    title: "Transparency First",
    description: "We openly share our methodology, performance metrics, and limitations. No black boxes, no hidden formulas, no misleading claims.",
    icon: "🔍",
  },
  {
    title: "Data-Driven",
    description: "Every prediction is grounded in historical data and statistical patterns. We let the numbers speak rather than gut feelings or narratives.",
    icon: "📊",
  },
  {
    title: "Continuous Improvement",
    description: "We track real-time performance, iterate on features, and refine our model as we learn. Accuracy metrics update daily with honest reporting.",
    icon: "🔄",
  },
  {
    title: "Accessible Insights",
    description: "Complex machine learning made simple. We explain predictions in plain language with context you can understand and use.",
    icon: "💡",
  },
];

const features = [
  {
    feature: "Daily Predictions",
    description: "Win probabilities for every NHL game, updated each morning with the latest rosters and goalie confirmations.",
  },
  {
    feature: "Performance Tracking",
    description: "Real-time accuracy metrics on current season games, with full transparency about what's working and what isn't.",
  },
  {
    feature: "X/Twitter Updates",
    description: "Automated daily posts with tonight's predictions, post-game results, and weekly performance summaries.",
  },
  {
    feature: "Analytics Dashboard",
    description: "Deep dive into feature importance, confidence calibration, and team-level breakdowns for hockey data enthusiasts.",
  },
];

const tech = [
  { label: "Backend", value: "Python, scikit-learn, pandas" },
  { label: "Model", value: "Logistic Regression (L2 regularization)" },
  { label: "Data", value: "NHL API, 3 seasons (2021-2024)" },
  { label: "Frontend", value: "Next.js 16, React 19, Tailwind CSS v4" },
  { label: "Deployment", value: "Vercel (auto-deploy on push)" },
  { label: "Automation", value: "GitHub Actions (daily updates)" },
];

const faqs = [
  {
    question: "Is this a betting tool?",
    answer: "No. We provide win probabilities based on historical data, but we're not a betting service. We don't offer betting advice, incorporate odds, or recommend wagers. Always bet responsibly if you choose to use our predictions as one input among many.",
  },
  {
    question: "How accurate are your predictions?",
    answer: "Our current season (2025-26) accuracy is tracked in real-time on the Performance page. Historically, we've achieved 55-60% accuracy on held-out test data, which represents a meaningful edge over the baseline (always picking home team). Performance varies by confidence level.",
  },
  {
    question: "What data sources do you use?",
    answer: "We combine NHL play-by-play statistics, internally calculated expected goals (xG), team performance metrics, and goalie tracking. Our training dataset includes 6 seasons (2018-2024) with 7,000+ games.",
  },
  {
    question: "Can I access historical predictions?",
    answer: "We're working on an archive feature. Currently, daily predictions are published each morning and results are tracked in aggregate. Follow @puckcastai on X for daily updates.",
  },
  {
    question: "How often do predictions update?",
    answer: "Once per day, typically around 10am ET after morning skates, goalie confirmations, and injury reports settle. We don't update intraday to avoid chasing last-minute noise.",
  },
  {
    question: "Is this open source?",
    answer: "Not yet, but we're considering it. We believe in transparency and may open-source the model in the future once it's more mature. Stay tuned for updates.",
  },
];

export default function AboutPage() {
  return (
    <div className="relative overflow-hidden">
      <div className="relative mx-auto flex max-w-6xl flex-col gap-16 px-6 pb-16 pt-8 lg:px-12">
        <header>
          <p className="text-sm uppercase tracking-[0.4em] text-lime-300">About Puckcast</p>
          <h1 className="mt-3 text-4xl font-semibold text-white sm:text-5xl">
            Machine learning for hockey fans who love the numbers.
          </h1>
          <p className="mt-4 max-w-3xl text-lg text-white/80">
            Puckcast is a passion project built by data enthusiasts who wanted to bring transparent,
            accessible NHL predictions to the hockey community. We combine machine learning with
            advanced statistics to predict game outcomes — and we share everything openly.
          </p>
        </header>

        <section className="rounded-[36px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30">
          <h2 className="text-2xl font-semibold text-white">Our Mission</h2>
          <p className="mt-4 max-w-3xl text-base leading-relaxed text-white/80">
            We believe hockey predictions should be transparent, data-driven, and accessible. Too many
            prediction models are black boxes that hide their methods and cherry-pick results. We're
            different. We show you how our model works, track real-time accuracy on current games,
            and openly discuss what we get right and wrong.
          </p>
          <p className="mt-4 max-w-3xl text-base leading-relaxed text-white/80">
            Our goal is simple: give hockey fans a better understanding of game probabilities using
            historical data and statistical patterns. Whether you're casually following your team,
            analyzing matchups, or just love the numbers, we want to make predictions you can trust
            and understand.
          </p>
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
            <h2 className="text-2xl font-semibold text-white">What We Offer</h2>
            <div className="mt-6 space-y-4">
              {features.map((item) => (
                <div key={item.feature} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                  <p className="text-sm font-semibold uppercase tracking-[0.4em] text-lime-300">{item.feature}</p>
                  <p className="mt-2 text-sm text-white/75">{item.description}</p>
                </div>
              ))}
            </div>
          </div>

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
              href="/methodology"
              className="rounded-full border border-white/20 px-8 py-3 text-sm font-semibold uppercase tracking-[0.4em] text-white/80 transition hover:text-white"
            >
              Learn how it works
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
