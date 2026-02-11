# GeoTrack

**The rank tracker for the AI era.** Monitor how often your brand gets mentioned — and how favorably — when people ask ChatGPT, Claude, Perplexity, and Gemini the questions that matter to your business.

---

## The Problem

Search is fragmenting. Users increasingly ask AI assistants the questions they used to Google: *"What's the best CRM for small teams?"*, *"Best running shoes for flat feet?"*, *"What project management tool do you recommend?"*

Whether your brand shows up in those AI-generated answers is becoming as important as page-one SEO rankings. But until now, there's been no way to systematically track it.

**GeoTrack fixes that.**

## How It Works

1. **Set up your brand** — name, aliases, competitors
2. **Add the queries that matter** — the questions your customers are asking AI
3. **GeoTrack runs those queries daily** across ChatGPT, Claude, Perplexity, and Gemini
4. **See your AI visibility on a dashboard** — mention rates, sentiment, trends, competitor comparison

## Dashboard

<!-- TODO: Add screenshots after build -->

**Overview** — Your brand mention rate across all AI engines, trending over time.

**Query Detail** — Drill into any query to see exactly what each AI engine said about your brand.

**Competitor Comparison** — Side-by-side visibility: who's getting recommended and where.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, SQLAlchemy |
| Database | PostgreSQL |
| Frontend | Next.js, Tailwind CSS, Recharts |
| Auth | NextAuth.js |
| Scheduling | APScheduler |
| Containerization | Docker Compose |

## Quick Start

```bash
# Clone
git clone https://github.com/yourusername/geotrack.git
cd geotrack

# Set up environment
cp .env.example .env
# Add your API keys to .env

# Run
docker compose up --build

# Seed demo data (optional — populates dashboard with sample data)
docker compose exec backend python -m app.seed

# Open
# Frontend: http://localhost:3000
# API docs: http://localhost:8000/docs
```

## API Keys Required

GeoTrack queries AI engines on your behalf. You'll need API keys for the engines you want to track:

| Engine | Get a key | Required? |
|--------|----------|-----------|
| OpenAI | [platform.openai.com](https://platform.openai.com) | Yes (free tier) |
| Anthropic | [console.anthropic.com](https://console.anthropic.com) | Yes (free tier) |
| Perplexity | [docs.perplexity.ai](https://docs.perplexity.ai) | Optional (Pro tier) |
| Google Gemini | [aistudio.google.com](https://aistudio.google.com) | Optional (Pro tier) |

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐
│   Next.js    │────▶│   FastAPI     │────▶│   PostgreSQL     │
│   Frontend   │◀────│   Backend     │◀────│   Database       │
└─────────────┘     └──────┬───────┘     └──────────────────┘
                           │
                    ┌──────┴───────┐
                    │  Scheduler   │
                    │  (APScheduler)│
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌────────┐  ┌────────┐  ┌────────┐
         │ OpenAI │  │ Claude │  │Perplx. │  ...
         └────────┘  └────────┘  └────────┘
```

## Features

- **Multi-engine tracking** — Query ChatGPT, Claude, Perplexity, and Gemini from a single dashboard
- **Brand mention detection** — Fuzzy matching across brand names and aliases
- **Sentiment analysis** — Is the AI recommending you enthusiastically or mentioning you as an afterthought?
- **Position tracking** — Are you the first brand mentioned? The top recommendation?
- **Competitor monitoring** — Track how competitors show up in the same queries
- **Citation tracking** — See which URLs Perplexity cites when it mentions your brand
- **Historical trends** — Daily data collection builds a picture of your AI visibility over time
- **Manual triggers** — Run a scan on demand, don't wait for the daily schedule

## Plan Tiers

| Feature | Free | Pro | Agency |
|---------|------|-----|--------|
| Brands | 1 | 3 | Unlimited |
| Queries / brand | 10 | 100 | 500 |
| Engines | 2 | 4 | 4 |
| Frequency | Weekly | Daily | Daily |
| Competitors | 2 | 10 | Unlimited |
| Export | — | CSV/PDF | CSV/PDF |

## Project Status

🚧 **Early development** — This is a working MVP. Core tracking and dashboard functionality is in place. Payment processing and some advanced features are on the roadmap.

## Roadmap

- [ ] Stripe integration for paid tiers
- [ ] White-label reports for agencies
- [ ] Semantic search across stored responses
- [ ] Slack/email alerts for visibility changes
- [ ] Public API
- [ ] Query suggestions powered by AI
- [ ] "How to improve your GEO" recommendations

## Contributing

This is currently a solo project, but feedback and ideas are welcome. Open an issue or reach out.

## License

MIT
