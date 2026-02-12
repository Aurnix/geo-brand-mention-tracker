# CLAUDE.md — GeoTrack

## Project Overview

GeoTrack is a full-stack SaaS application that monitors brand mentions in AI-generated responses across ChatGPT, Claude, Perplexity, and Gemini. Think "SEO rank tracker" for the generative AI era.

## Tech Stack

- **Backend:** Python 3.12, FastAPI 0.115, SQLAlchemy 2.0 (async), PostgreSQL 16
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, Recharts
- **Auth:** JWT (backend) + NextAuth.js (frontend)
- **Scheduling:** APScheduler (daily cron)
- **Infrastructure:** Docker Compose (3 services: db, backend, frontend)

## Project Structure

```
backend/
  app/
    main.py              # FastAPI app, CORS, router registration, lifespan/scheduler
    config.py            # pydantic-settings, all env var loading
    database.py          # Async engine, sync engine, session factory, Base, get_db
    seed.py              # Demo data seeder (python -m app.seed)
    api/
      deps.py            # get_current_user (JWT), verify_brand_ownership
      routes/
        auth.py          # /api/auth — signup, login, me
        brands.py        # /api/brands — CRUD + competitors + manual run trigger
        queries.py       # /api — brand queries CRUD
        results.py       # /api — overview, paginated results, history, comparison
    models/              # SQLAlchemy 2.0 Mapped[] models, PG_UUID PKs
      user.py            # User + PlanTier enum
      brand.py           # Brand + Competitor
      query.py           # MonitoredQuery
      result.py          # QueryResult (composite index on query_id, engine, run_date)
    schemas/             # Pydantic v2 schemas (from_attributes=True)
    engines/             # AI engine adapters (BaseEngine → EngineResponse)
      openai_engine.py   # gpt-4o
      anthropic_engine.py # claude-sonnet-4-20250514
      perplexity_engine.py # sonar-large (httpx, extracts citations)
      gemini_engine.py   # gemini-2.0-flash
    services/
      response_parser.py # LLM-powered mention detection, sentiment, position
      query_runner.py    # Orchestrates engine calls + parsing + storage
      scheduler.py       # APScheduler daily cron, init_scheduler()
      plan_limits.py     # PLAN_LIMITS dict, check_* functions
    tests/               # pytest-asyncio, aiosqlite, SQLite UUID compat
frontend/
  src/
    app/
      page.tsx           # Landing page (server component)
      login/page.tsx     # Login form
      signup/page.tsx    # Signup form
      onboarding/page.tsx # 4-step wizard
      dashboard/
        layout.tsx       # Dark sidebar, brand selector, BrandContext
        page.tsx         # Overview scorecard, charts
        queries/page.tsx # Query table with expandable rows
        competitors/page.tsx # Comparison bar chart, sentiment table
      api/auth/[...nextauth]/route.ts  # NextAuth CredentialsProvider
    lib/
      api.ts             # ApiClient class, all backend calls
      auth.ts            # useAuth() hook, auto-sets API token
    components/
      providers.tsx      # SessionProvider wrapper
    middleware.ts        # Protects /dashboard, /onboarding
```

## Key Patterns

- **Database sessions**: `get_db()` yields async sessions with auto-commit/rollback
- **Auth flow**: Backend issues JWT → NextAuth stores in session → `useAuth()` hook sets token on `api` client
- **Brand context**: Dashboard layout provides `useBrand()` context (brandId, brands, setBrandId)
- **Plan enforcement**: Checked in route handlers before create operations (brands, queries, competitors)
- **Response parsing**: Cheap LLM calls (gpt-4o-mini) for sentiment + top-rec detection; text analysis for position
- **Background tasks**: Manual run uses FastAPI `BackgroundTasks` with a fresh session

## Running

```bash
cp .env.example .env       # Add API keys
docker compose up --build   # Start all services
# Backend: http://localhost:8000/docs
# Frontend: http://localhost:3000
docker compose exec backend python -m app.seed  # Load demo data
```

## Testing

```bash
cd backend && pip install -r requirements.txt
pytest app/tests/           # Run all tests (tests dir is inside app/)
pytest app/tests/ --cov=app # With coverage
```

Tests use aiosqlite in-memory DB. The conftest patches PG_UUID → VARCHAR(36) and replaces gen_random_uuid() server defaults with Python-side uuid4 defaults for SQLite compatibility.

## Demo Data

```bash
docker compose exec backend python -m app.seed
```

- Seed is idempotent — checks for existing demo user (`demo@geotrack.ai` / `demo1234`) before inserting
- Creates 2 brands (Notion, Airtable) with competitors, 40 queries, and ~30 days of results across all 4 engines
- To re-seed: wipe the DB first (`docker compose down -v && docker compose up --build`)

## Known Gotchas

- **Backend OverviewResponse vs frontend**: The backend returns `mention_rate_trend` (array), `top_rec_rate`, `engine_breakdown` (dict), and `sentiment_breakdown` (object). The frontend dashboard must transform these shapes for Recharts (arrays, percentages). If adding new overview fields, update both `backend/app/schemas/result.py` and `frontend/src/app/dashboard/page.tsx`.
- **NextAuth NEXTAUTH_URL**: Must be set to `http://localhost:3000` (the browser-facing URL), not the Docker-internal service name. `NEXT_PUBLIC_API_URL` is what the browser uses to reach the backend.
- **competitor_mentions JSON shape**: Each competitor entry in `QueryResult.competitor_mentions` should include `{mentioned, sentiment, position, is_top_recommendation}`. The competitor comparison endpoint reads `is_top_recommendation` to determine query winners.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/auth/signup | Create account, returns JWT |
| POST | /api/auth/login | Login, returns JWT |
| GET | /api/auth/me | Current user info |
| GET | /api/brands | List user's brands |
| POST | /api/brands | Create brand (plan-limited) |
| GET | /api/brands/{id} | Get brand |
| PUT | /api/brands/{id} | Update brand |
| DELETE | /api/brands/{id} | Delete brand (cascades) |
| POST | /api/brands/{id}/run | Trigger manual scan (background) |
| GET | /api/brands/{id}/competitors | List competitors |
| POST | /api/brands/{id}/competitors | Add competitor (plan-limited) |
| DELETE | /api/brands/{id}/competitors/{cid} | Remove competitor |
| GET | /api/brands/{id}/queries | List queries |
| POST | /api/brands/{id}/queries | Add query (plan-limited) |
| PATCH | /api/queries/{id} | Update query |
| DELETE | /api/queries/{id} | Delete query |
| GET | /api/brands/{id}/overview | Dashboard scorecard |
| GET | /api/brands/{id}/results | Paginated results (filter by engine) |
| GET | /api/queries/{id}/history | Query result time series |
| GET | /api/brands/{id}/competitors/comparison | Competitor comparison |
| GET | /api/health | Health check |

## Plan Limits

| Feature | Free | Pro | Agency |
|---------|------|-----|--------|
| Brands | 1 | 3 | Unlimited |
| Queries/brand | 10 | 100 | 500 |
| Engines | 2 (OpenAI, Anthropic) | All 4 | All 4 |
| Frequency | Weekly | Daily | Daily |
| Competitors | 2 | 10 | Unlimited |
