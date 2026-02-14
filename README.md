# GeoTrack

Monitor how often your brand gets mentioned — and how favorably — when people ask ChatGPT, Claude, Perplexity, and Gemini the questions that matter to your business.

---

## The Problem

Search is fragmenting. Users increasingly ask AI assistants the questions they used to Google: *"What's the best CRM for small teams?"*, *"Best running shoes for flat feet?"*, *"What project management tool do you recommend?"*

Whether your brand shows up in those AI-generated answers is becoming as important as page-one SEO rankings. But until now, there's been no way to systematically track it.



## How It Works

1. **Set up your brand** — name, aliases, competitors
2. **Add the queries that matter** — the questions your customers are asking AI
3. **GeoTrack runs those queries daily** across ChatGPT, Claude, Perplexity, and Gemini
4. **See your AI visibility on a dashboard** — mention rates, sentiment, trends, competitor comparison

## Features

- **Multi-engine tracking** — Query ChatGPT (GPT-4o), Claude (Sonnet), Perplexity (Sonar), and Gemini (2.0 Flash) from a single dashboard
- **Brand mention detection** — Word-boundary matching (not substring) across brand names and aliases, preventing false positives
- **Sentiment analysis** — LLM-powered detection of positive, neutral, negative, and mixed sentiment
- **Position tracking** — First mention? Top recommendation? Early, middle, or late in the response?
- **Competitor monitoring** — Track how competitors show up in the same queries with per-competitor sentiment
- **Citation tracking** — See which URLs Perplexity cites when it mentions your brand
- **Historical trends** — Daily data collection builds a picture of your AI visibility over time
- **Manual triggers** — Run a scan on demand from the dashboard
- **Plan-based limits** — Free, Pro, and Agency tiers with enforced resource limits

## Dashboard

**Overview** — Brand mention rate across all AI engines, trending over time. Engine-by-engine breakdown. Sentiment donut chart. Top recommendation rate.

**Queries** — Table of monitored queries with per-engine status icons. Expandable rows showing historical results, full AI response text, and trend charts.

**Competitors** — Side-by-side bar chart comparison of mention rates. Sentiment breakdown table. Query-level winner tracking per engine.

## Detection Methodology

GeoTrack's analysis pipeline runs in two stages for each query+engine combination:

**Stage 1 — Text analysis (deterministic).** Word-boundary regex matching (`\b` boundaries, not substring search) checks whether your brand and each competitor appear in the AI-generated response. This prevents false positives — "Notion" won't match inside "notional" or "emotional". For each detected mention, GeoTrack records its position in the response (first, early, middle, late) based on the character offset relative to the full response length.

**Stage 2 — LLM-powered classification (gpt-4o-mini).** For mentioned brands, a lightweight LLM call determines: (1) whether the brand is the **top/primary recommendation**, and (2) the **sentiment** of the mention (positive, neutral, negative, or mixed). Competitors are analyzed in a single batched LLM call that extracts both sentiment and top-recommendation status for each mentioned competitor. Non-mentioned entities skip the LLM call entirely, reducing cost and latency.

**Aggregation.** The dashboard rolls up per-result data into actionable metrics:
- **Mention rate** — percentage of query runs where the brand appeared, overall and per-engine
- **Sentiment breakdown** — only counts sentiment for results where the brand was actually mentioned (non-mentions don't inflate neutral counts)
- **Top recommendation rate** — how often the brand is the primary recommendation
- **Competitor comparison** — side-by-side mention rates, sentiment, and per-query "winners" (which entity the AI recommended most strongly), with optional time-window scoping (`?days=30`)
- **Trend lines** — daily mention rate over time to track visibility changes

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | Python, FastAPI, SQLAlchemy (async) | 3.12, 0.115, 2.0 |
| Database | PostgreSQL | 16 |
| Frontend | Next.js (App Router), TypeScript | 14.2 |
| Styling | Tailwind CSS | 3.4 |
| Charts | Recharts | 2.15 |
| Auth | JWT (backend) + NextAuth.js (frontend) | — |
| Scheduling | APScheduler | 3.10 |
| AI Engines | OpenAI, Anthropic, Perplexity, Google Gemini | — |
| Containerization | Docker Compose | — |

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

# Seed demo data (optional — populates 30 days of realistic data for Notion + Airtable)
docker compose exec backend python -m app.seed

# Open
# Frontend: http://localhost:3000
# API docs: http://localhost:8000/docs
# Demo login: demo@geotrack.app / demo123456
```

## API Keys Required

GeoTrack queries AI engines on your behalf. You'll need API keys for the engines you want to track:

| Engine | Get a key | Required? |
|--------|----------|-----------|
| OpenAI | [platform.openai.com](https://platform.openai.com) | Yes (also used for response parsing) |
| Anthropic | [console.anthropic.com](https://console.anthropic.com) | Yes (free tier) |
| Perplexity | [docs.perplexity.ai](https://docs.perplexity.ai) | Optional (Pro tier) |
| Google Gemini | [aistudio.google.com](https://aistudio.google.com) | Optional (Pro tier) |

## Architecture

```
                                    ┌──────────────────┐
┌─────────────┐     ┌──────────────┤   PostgreSQL 16   │
│   Next.js   │────▶│   FastAPI    │   (Docker)        │
│   Frontend  │◀────│   Backend    ├──────────────────┘
│   :3000     │     │   :8000      │
└─────────────┘     └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │  APScheduler │
                    │  Daily Cron  │
                    └──────┬───────┘
                           │
          ┌────────┬───────┼────────┬─────────┐
          ▼        ▼       ▼        ▼         ▼
     ┌────────┐┌───────┐┌────────┐┌───────┐┌─────────┐
     │ OpenAI ││Claude ││Perplx. ││Gemini ││gpt-4o-  │
     │ gpt-4o ││Sonnet ││ Sonar  ││ Flash ││mini     │
     └────────┘└───────┘└────────┘└───────┘│(parser) │
                                           └─────────┘
```

## API Endpoints

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/signup` | Create account, returns JWT |
| POST | `/api/auth/login` | Login, returns JWT |
| GET | `/api/auth/me` | Current user info |

### Brands
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/brands` | List user's brands |
| POST | `/api/brands` | Create brand |
| GET | `/api/brands/{id}` | Get brand |
| PUT | `/api/brands/{id}` | Update brand |
| DELETE | `/api/brands/{id}` | Delete brand (cascades) |
| POST | `/api/brands/{id}/run` | Trigger manual scan |

### Competitors
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/brands/{id}/competitors` | List competitors |
| POST | `/api/brands/{id}/competitors` | Add competitor |
| DELETE | `/api/brands/{id}/competitors/{cid}` | Remove competitor |

### Queries
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/brands/{id}/queries` | List queries |
| POST | `/api/brands/{id}/queries` | Add query |
| PATCH | `/api/queries/{id}` | Update query |
| DELETE | `/api/queries/{id}` | Delete query |

### Dashboard Data
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/brands/{id}/overview` | Scorecard (mention rate, trends, sentiment) |
| GET | `/api/brands/{id}/results` | Paginated results with filters |
| GET | `/api/queries/{id}/history` | Time-series results for a query |
| GET | `/api/brands/{id}/competitors/comparison` | Competitor comparison data |

## Plan Tiers

| Feature | Free | Pro | Agency |
|---------|------|-----|--------|
| Brands | 1 | 3 | Unlimited |
| Queries / brand | 10 | 100 | 500 |
| Engines | 2 (OpenAI + Anthropic) | All 4 | All 4 |
| Frequency | Weekly | Daily | Daily |
| Competitors | 2 | 10 | Unlimited |

## Testing

The backend has comprehensive tests using pytest with aiosqlite for database isolation:

```bash
cd backend
pip install -r requirements.txt
pytest -v                    # Run all tests
pytest --cov=app --cov-report=term-missing  # With coverage
```

**Test coverage includes:**
- Auth (signup, login, JWT validation, edge cases) — 10 tests
- Brands (CRUD, ownership checks, plan limits) — 14 tests
- Competitors (add, list, delete, cross-brand protection) — 10 tests
- Queries (CRUD, brand ownership, plan limits) — 13 tests
- Results (overview aggregation, pagination, filtering, history, comparison, date scoping, sentiment filtering) — 16 tests
- Response parser (mention detection, word boundaries, position, sentiment, top-rec, competitor extraction) — 20 tests
- Plan limits (unit + integration, all three tiers) — 14 tests

**Total: 119 tests**

## Seed Data

The seed script creates realistic demo data for impressive dashboards:

- **1 demo user** — demo@geotrack.app / demo123456 (Pro plan)
- **2 brands** — Notion and Airtable with competitors
- **20 queries per brand** — Mix of purchase intent, comparison, and informational
- **30 days of results** — 4 engines x 20 queries x 30 days = 2,400 results per brand
- **Realistic patterns** — Notion at ~60% mention rate (trending up), engine-specific variation, natural daily variance

## Project Status

This is a working MVP. Core tracking and dashboard functionality is complete. The application demonstrates:
- Full-stack async Python + Next.js architecture
- Multi-provider AI API integration
- LLM-powered text analysis pipeline
- Real-time dashboard with data visualization
- Plan-based access control

## Roadmap

- [ ] Stripe integration for paid tiers
- [ ] White-label reports for agencies
- [ ] Semantic search across stored responses
- [ ] Slack/email alerts for visibility changes
- [ ] CSV/PDF export
- [ ] Query suggestions powered by AI
- [ ] "How to improve your GEO" recommendations

## License

MIT
