import Link from "next/link";
import {
  BarChart3,
  Search,
  TrendingUp,
  Shield,
  Users,
  Zap,
  ArrowRight,
  CheckCircle2,
  Sparkles,
  Eye,
  MessageSquare,
  Target,
} from "lucide-react";

const engines = [
  { name: "ChatGPT", color: "bg-green-500" },
  { name: "Claude", color: "bg-orange-500" },
  { name: "Perplexity", color: "bg-blue-500" },
  { name: "Gemini", color: "bg-purple-500" },
];

const steps = [
  {
    number: "01",
    title: "Set up your brand",
    description:
      "Enter your brand name and aliases. We'll use these to detect mentions across AI responses.",
    icon: Target,
  },
  {
    number: "02",
    title: "Add your queries",
    description:
      "Define the questions your customers ask. We'll monitor how AI engines respond to each one.",
    icon: Search,
  },
  {
    number: "03",
    title: "Daily tracking runs",
    description:
      "Every day, we query all major AI engines and analyze the responses for brand mentions and sentiment.",
    icon: Zap,
  },
  {
    number: "04",
    title: "Dashboard insights",
    description:
      "See mention rates, sentiment trends, competitor comparisons, and position tracking in one dashboard.",
    icon: BarChart3,
  },
];

const features = [
  {
    title: "Multi-engine tracking",
    description:
      "Monitor your brand across ChatGPT, Claude, Perplexity, and Gemini simultaneously.",
    icon: Eye,
  },
  {
    title: "Mention detection",
    description:
      "Know exactly when and where your brand appears in AI-generated responses.",
    icon: Search,
  },
  {
    title: "Sentiment analysis",
    description:
      "Understand whether AI engines talk about your brand positively, neutrally, or negatively.",
    icon: MessageSquare,
  },
  {
    title: "Position tracking",
    description:
      "Track whether your brand is mentioned first, early, or buried at the end of responses.",
    icon: TrendingUp,
  },
  {
    title: "Competitor monitoring",
    description:
      "Compare your brand's visibility against competitors across every engine and query.",
    icon: Users,
  },
  {
    title: "Trend analysis",
    description:
      "Spot changes in your AI visibility over time with daily tracking and historical charts.",
    icon: Sparkles,
  },
];

const pricingTiers = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "Get started with basic AI brand tracking.",
    features: [
      "1 brand",
      "10 queries per brand",
      "2 engines (ChatGPT + Claude)",
      "Weekly run frequency",
      "2 competitors",
    ],
    cta: "Start free",
    href: "/signup",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "$49",
    period: "/month",
    description: "For growing brands that need comprehensive tracking.",
    features: [
      "3 brands",
      "100 queries per brand",
      "All 4 engines",
      "Daily run frequency",
      "10 competitors",
      "CSV/PDF export",
    ],
    cta: "Start free trial",
    href: "/signup",
    highlighted: true,
  },
  {
    name: "Agency",
    price: "$149",
    period: "/month",
    description: "For agencies managing multiple client brands.",
    features: [
      "Unlimited brands",
      "500 queries per brand",
      "All 4 engines",
      "Daily run frequency",
      "Unlimited competitors",
      "CSV/PDF export",
      "Priority support",
    ],
    cta: "Contact sales",
    href: "/signup",
    highlighted: false,
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* ── Navigation ───────────────────────────────────── */}
      <nav className="fixed top-0 z-50 w-full border-b border-gray-100 bg-white/80 backdrop-blur-lg">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600">
              <BarChart3 className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold text-gray-900">GeoTrack</span>
          </Link>
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="rounded-lg px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:text-gray-900"
            >
              Log in
            </Link>
            <Link
              href="/signup"
              className="btn-primary"
            >
              Sign up free
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ─────────────────────────────────────────── */}
      <section className="relative overflow-hidden pt-32 pb-20">
        {/* Gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-brand-50 via-white to-purple-50" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(59,130,246,0.15),transparent)]" />

        <div className="relative mx-auto max-w-7xl px-6">
          <div className="mx-auto max-w-4xl text-center">
            {/* Badge */}
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-4 py-1.5 text-sm font-medium text-brand-700">
              <Sparkles className="h-4 w-4" />
              The future of brand visibility tracking
            </div>

            <h1 className="text-5xl font-extrabold tracking-tight text-gray-900 sm:text-6xl lg:text-7xl">
              The Rank Tracker for{" "}
              <span className="bg-gradient-to-r from-brand-600 to-purple-600 bg-clip-text text-transparent">
                the AI Era
              </span>
            </h1>

            <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-gray-600 sm:text-xl">
              Monitor how often your brand gets mentioned — and how favorably —
              when people ask ChatGPT, Claude, Perplexity, and Gemini.
            </p>

            {/* CTAs */}
            <div className="mt-10 flex items-center justify-center gap-4">
              <Link
                href="/signup"
                className="btn-primary inline-flex items-center gap-2 px-6 py-3 text-base"
              >
                Start tracking free
                <ArrowRight className="h-4 w-4" />
              </Link>
              <a
                href="#how-it-works"
                className="btn-secondary inline-flex items-center gap-2 px-6 py-3 text-base"
              >
                See how it works
              </a>
            </div>

            {/* Engine badges */}
            <div className="mt-12 flex items-center justify-center gap-3">
              <span className="text-sm text-gray-500">Tracks across:</span>
              {engines.map((engine) => (
                <span
                  key={engine.name}
                  className="inline-flex items-center gap-1.5 rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-gray-700"
                >
                  <span
                    className={`h-2 w-2 rounded-full ${engine.color}`}
                  />
                  {engine.name}
                </span>
              ))}
            </div>
          </div>

          {/* Dashboard mockup */}
          <div className="mx-auto mt-16 max-w-5xl">
            <div className="overflow-hidden rounded-2xl border border-gray-200 bg-gray-900 shadow-2xl shadow-brand-500/10">
              {/* Browser chrome */}
              <div className="flex items-center gap-2 border-b border-gray-700 bg-gray-800 px-4 py-3">
                <div className="h-3 w-3 rounded-full bg-red-500" />
                <div className="h-3 w-3 rounded-full bg-yellow-500" />
                <div className="h-3 w-3 rounded-full bg-green-500" />
                <div className="ml-4 flex-1 rounded-md bg-gray-700 px-3 py-1 text-xs text-gray-400">
                  app.geotrack.io/dashboard
                </div>
              </div>
              {/* Mock dashboard */}
              <div className="p-6">
                <div className="grid grid-cols-4 gap-4">
                  <div className="rounded-lg bg-gray-800 p-4">
                    <div className="text-xs text-gray-400">Mention Rate</div>
                    <div className="mt-1 text-2xl font-bold text-white">
                      64.2%
                    </div>
                    <div className="mt-1 text-xs text-green-400">+3.1%</div>
                  </div>
                  <div className="rounded-lg bg-gray-800 p-4">
                    <div className="text-xs text-gray-400">Top Rec Rate</div>
                    <div className="mt-1 text-2xl font-bold text-white">
                      28.5%
                    </div>
                    <div className="mt-1 text-xs text-green-400">+1.8%</div>
                  </div>
                  <div className="rounded-lg bg-gray-800 p-4">
                    <div className="text-xs text-gray-400">Total Queries</div>
                    <div className="mt-1 text-2xl font-bold text-white">47</div>
                    <div className="mt-1 text-xs text-gray-500">active</div>
                  </div>
                  <div className="rounded-lg bg-gray-800 p-4">
                    <div className="text-xs text-gray-400">Total Runs</div>
                    <div className="mt-1 text-2xl font-bold text-white">
                      1,204
                    </div>
                    <div className="mt-1 text-xs text-gray-500">this month</div>
                  </div>
                </div>
                {/* Chart placeholder */}
                <div className="mt-4 flex gap-4">
                  <div className="flex-1 rounded-lg bg-gray-800 p-4">
                    <div className="mb-3 text-xs text-gray-400">
                      Mention Rate Trend
                    </div>
                    <div className="flex items-end gap-1" style={{ height: 80 }}>
                      {[40, 45, 42, 48, 52, 50, 55, 58, 56, 60, 62, 64].map(
                        (h, i) => (
                          <div
                            key={i}
                            className="flex-1 rounded-t bg-brand-500/70"
                            style={{ height: `${h}%` }}
                          />
                        )
                      )}
                    </div>
                  </div>
                  <div className="w-48 rounded-lg bg-gray-800 p-4">
                    <div className="mb-3 text-xs text-gray-400">
                      By Engine
                    </div>
                    <div className="space-y-2">
                      {[
                        { name: "ChatGPT", pct: 72 },
                        { name: "Claude", pct: 58 },
                        { name: "Perplexity", pct: 81 },
                        { name: "Gemini", pct: 45 },
                      ].map((e) => (
                        <div key={e.name}>
                          <div className="flex justify-between text-xs">
                            <span className="text-gray-400">{e.name}</span>
                            <span className="text-gray-300">{e.pct}%</span>
                          </div>
                          <div className="mt-1 h-1.5 rounded-full bg-gray-700">
                            <div
                              className="h-full rounded-full bg-brand-500"
                              style={{ width: `${e.pct}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Problem Section ──────────────────────────────── */}
      <section className="border-t border-gray-100 bg-white py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Search is fragmenting.{" "}
              <span className="text-gray-400">Your brand visibility is at risk.</span>
            </h2>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              More and more people are skipping Google and going straight to AI.
              They ask ChatGPT for product recommendations. They use Perplexity for
              research. They trust Claude for comparisons. If your brand isn't
              showing up in these AI-generated responses, you're invisible to a
              growing segment of your audience.
            </p>
          </div>

          <div className="mx-auto mt-16 grid max-w-5xl grid-cols-1 gap-8 sm:grid-cols-3">
            <div className="text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
                <TrendingUp className="h-6 w-6 text-red-600" />
              </div>
              <h3 className="mt-4 text-lg font-semibold text-gray-900">
                AI usage is exploding
              </h3>
              <p className="mt-2 text-sm text-gray-600">
                Hundreds of millions use AI assistants daily for product research
                and recommendations.
              </p>
            </div>
            <div className="text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-amber-100">
                <Eye className="h-6 w-6 text-amber-600" />
              </div>
              <h3 className="mt-4 text-lg font-semibold text-gray-900">
                No visibility into AI results
              </h3>
              <p className="mt-2 text-sm text-gray-600">
                Traditional SEO tools can't track what AI engines say about your
                brand. You're flying blind.
              </p>
            </div>
            <div className="text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
                <Shield className="h-6 w-6 text-green-600" />
              </div>
              <h3 className="mt-4 text-lg font-semibold text-gray-900">
                GEO is the new SEO
              </h3>
              <p className="mt-2 text-sm text-gray-600">
                Generative Engine Optimization is how brands will compete. Start
                measuring so you can improve.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── How It Works ─────────────────────────────────── */}
      <section
        id="how-it-works"
        className="border-t border-gray-100 bg-gray-50 py-24"
      >
        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              How it works
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              Get from zero to insights in under five minutes.
            </p>
          </div>

          <div className="mx-auto mt-16 grid max-w-5xl grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {steps.map((step) => (
              <div key={step.number} className="relative">
                <div className="card flex flex-col items-start p-6">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-600 text-sm font-bold text-white">
                    {step.number}
                  </div>
                  <h3 className="mt-4 text-lg font-semibold text-gray-900">
                    {step.title}
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-gray-600">
                    {step.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features Grid ────────────────────────────────── */}
      <section className="border-t border-gray-100 bg-white py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Everything you need to track AI visibility
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              Comprehensive monitoring across all major AI engines, with
              actionable insights.
            </p>
          </div>

          <div className="mx-auto mt-16 grid max-w-5xl grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="card group p-6 transition-shadow hover:shadow-md"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-100 text-brand-600 transition-colors group-hover:bg-brand-600 group-hover:text-white">
                  <feature.icon className="h-5 w-5" />
                </div>
                <h3 className="mt-4 text-base font-semibold text-gray-900">
                  {feature.title}
                </h3>
                <p className="mt-2 text-sm leading-6 text-gray-600">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Pricing ──────────────────────────────────────── */}
      <section className="border-t border-gray-100 bg-gray-50 py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Simple, transparent pricing
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              Start free and scale as your tracking needs grow.
            </p>
          </div>

          <div className="mx-auto mt-16 grid max-w-5xl grid-cols-1 gap-8 lg:grid-cols-3">
            {pricingTiers.map((tier) => (
              <div
                key={tier.name}
                className={`relative rounded-2xl p-8 ${
                  tier.highlighted
                    ? "bg-brand-600 text-white ring-2 ring-brand-600 shadow-xl shadow-brand-500/25"
                    : "bg-white ring-1 ring-gray-200"
                }`}
              >
                {tier.highlighted && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 rounded-full bg-brand-400 px-4 py-1 text-xs font-semibold text-white">
                    Most popular
                  </div>
                )}
                <h3
                  className={`text-lg font-semibold ${
                    tier.highlighted ? "text-white" : "text-gray-900"
                  }`}
                >
                  {tier.name}
                </h3>
                <p
                  className={`mt-2 text-sm ${
                    tier.highlighted ? "text-brand-100" : "text-gray-600"
                  }`}
                >
                  {tier.description}
                </p>
                <div className="mt-6 flex items-baseline gap-1">
                  <span
                    className={`text-4xl font-extrabold ${
                      tier.highlighted ? "text-white" : "text-gray-900"
                    }`}
                  >
                    {tier.price}
                  </span>
                  <span
                    className={`text-sm ${
                      tier.highlighted ? "text-brand-200" : "text-gray-500"
                    }`}
                  >
                    {tier.period}
                  </span>
                </div>
                <ul className="mt-8 space-y-3">
                  {tier.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2">
                      <CheckCircle2
                        className={`h-4 w-4 flex-shrink-0 ${
                          tier.highlighted ? "text-brand-200" : "text-brand-600"
                        }`}
                      />
                      <span
                        className={`text-sm ${
                          tier.highlighted ? "text-brand-100" : "text-gray-700"
                        }`}
                      >
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>
                <Link
                  href={tier.href}
                  className={`mt-8 block w-full rounded-lg py-2.5 text-center text-sm font-semibold transition-colors ${
                    tier.highlighted
                      ? "bg-white text-brand-600 hover:bg-brand-50"
                      : "bg-brand-600 text-white hover:bg-brand-700"
                  }`}
                >
                  {tier.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Final CTA ────────────────────────────────────── */}
      <section className="border-t border-gray-100 bg-white py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto max-w-3xl text-center">
            <div className="rounded-2xl bg-gradient-to-br from-brand-600 to-purple-700 px-8 py-16 shadow-xl shadow-brand-500/20 sm:px-16">
              <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
                Start tracking your brand's AI visibility
              </h2>
              <p className="mx-auto mt-4 max-w-xl text-lg text-brand-100">
                Set up in under 5 minutes. No credit card required. See exactly
                how AI engines talk about your brand.
              </p>
              <Link
                href="/signup"
                className="mt-8 inline-flex items-center gap-2 rounded-lg bg-white px-6 py-3 text-base font-semibold text-brand-600 shadow-sm transition-colors hover:bg-brand-50"
              >
                Get started for free
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────── */}
      <footer className="border-t border-gray-200 bg-gray-50 py-12">
        <div className="mx-auto max-w-7xl px-6">
          <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-brand-600">
                <BarChart3 className="h-4 w-4 text-white" />
              </div>
              <span className="text-base font-bold text-gray-900">
                GeoTrack
              </span>
            </div>
            <div className="flex items-center gap-6 text-sm text-gray-500">
              <a href="#how-it-works" className="hover:text-gray-700">
                How it works
              </a>
              <Link href="/login" className="hover:text-gray-700">
                Log in
              </Link>
              <Link href="/signup" className="hover:text-gray-700">
                Sign up
              </Link>
            </div>
            <p className="text-sm text-gray-400">
              &copy; 2026 GeoTrack. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
