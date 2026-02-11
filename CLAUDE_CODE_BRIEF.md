# Claude Code Brief — GEO Brand Mention Tracker

## What You're Building

A full-stack SaaS web application called **GeoTrack** (working name) that monitors how often brands get mentioned in AI-generated responses across ChatGPT, Claude, Perplexity, and Gemini. Think "SEO rank tracker" but for the generative AI era.

This is a portfolio/demo build. It needs to be clean, well-structured, and impressive on GitHub. Write good code, write tests, and document your decisions.

## Tech Stack

- **Backend:** Python, FastAPI
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Job Scheduling:** APScheduler (for daily query runs)
- **Frontend:** Next.js with Tailwind CSS
- **Auth:** NextAuth.js (email + password for now)
- **Containerization:** Docker Compose for local dev (Postgres + API + Frontend)

## Project Structure

```
geotrack/
├── README.md
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entry
│   │   ├── config.py               # Settings, env vars
│   │   ├── models/                 # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── brand.py
│   │   │   ├── query.py
│   │   │   └── result.py
│   │   ├── schemas/                # Pydantic schemas
│   │   ├── api/                    # Route handlers
│   │   │   ├── auth.py
│   │   │   ├── brands.py
│   │   │   ├── queries.py
│   │   │   └── results.py
│   │   ├── services/               # Business logic
│   │   │   ├── query_runner.py     # Orchestrates running queries against engines
│   │   │   ├── response_parser.py  # Extracts mentions, sentiment, position
│   │   │   └── scheduler.py        # Daily job scheduling
│   │   ├── engines/                # One module per AI engine
│   │   │   ├── base.py             # Abstract base class
│   │   │   ├── openai_engine.py
│   │   │   ├── anthropic_engine.py
│   │   │   ├── perplexity_engine.py
│   │   │   └── gemini_engine.py
│   │   └── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── alembic/                    # DB migrations
├── frontend/
│   ├── src/
│   │   ├── app/                    # Next.js app router
│   │   │   ├── page.tsx            # Landing page
│   │   │   ├── login/
│   │   │   ├── signup/
│   │   │   ├── onboarding/         # Brand setup wizard
│   │   │   └── dashboard/
│   │   │       ├── page.tsx        # Overview scorecard
│   │   │       ├── queries/        # Query detail table + drilldown
│   │   │       └── competitors/    # Competitor comparison
│   │   ├── components/
│   │   └── lib/
│   ├── package.json
│   └── Dockerfile
└── .env.example
```

## Database Schema

### users
- id (uuid, PK)
- email (unique)
- password_hash
- plan_tier (enum: free, pro, agency) — default free
- created_at
- updated_at

### brands
- id (uuid, PK)
- user_id (FK → users)
- name (string, e.g. "HubSpot")
- aliases (json array, e.g. ["Hub Spot", "hubspot.com"])
- created_at

### competitors
- id (uuid, PK)
- brand_id (FK → brands)
- name (string)
- aliases (json array)

### monitored_queries
- id (uuid, PK)
- brand_id (FK → brands)
- query_text (string, e.g. "What's the best CRM for small businesses?")
- category (string, optional — e.g. "purchase_intent", "comparison", "informational")
- is_active (boolean, default true)
- created_at

### query_results
- id (uuid, PK)
- query_id (FK → monitored_queries)
- engine (enum: openai, anthropic, perplexity, gemini)
- model_version (string — e.g. "gpt-4o-2025-01-15")
- raw_response (text — store the full response)
- brand_mentioned (boolean)
- mention_position (enum: first, early, middle, late, not_mentioned)
- is_top_recommendation (boolean)
- sentiment (enum: positive, neutral, negative, mixed)
- competitor_mentions (json — e.g. {"Salesforce": {"mentioned": true, "sentiment": "positive", "position": "first"}, ...})
- citations (json, nullable — for Perplexity, list of cited URLs)
- run_date (date)
- created_at

Index on (query_id, engine, run_date) for fast dashboard queries.

## AI Engine Implementation

Each engine module should implement this interface:

```python
class BaseEngine(ABC):
    @abstractmethod
    async def run_query(self, query_text: str) -> EngineResponse:
        """Send a query and return the raw response."""
        pass
```

**System prompt for all engines:**
```
You are a helpful assistant. Answer the user's question thoroughly and naturally.
```

Do NOT add anything that biases the response toward or against any brand. The goal is to simulate what a normal user would see.

**EngineResponse:**
```python
@dataclass
class EngineResponse:
    raw_text: str
    model_version: str
    citations: list[str] | None  # Only populated for Perplexity
```

**Engine-specific notes:**
- OpenAI: Use the chat completions API. Model: gpt-4o (or latest available).
- Anthropic: Use the messages API. Model: claude-sonnet-4-20250514 (cost-efficient for bulk runs).
- Perplexity: Use their chat completions API (OpenAI-compatible). Extract citations from the response.
- Gemini: Use the Google Generative AI API. Model: gemini-2.0-flash or latest.

**IMPORTANT:** All API keys should come from environment variables. The .env.example file should list every required key with placeholder values. Never hardcode keys.

## Response Parser

The response parser is the core intelligence. Given a raw AI response, a brand name (+ aliases), and a list of competitors (+ their aliases), it should extract:

1. **brand_mentioned** — Was the brand name or any alias found in the response?
2. **mention_position** — Where in the response did the first mention appear? Split the response into quartiles. If the brand is the first product/service mentioned, position is "first".
3. **is_top_recommendation** — Is the brand presented as the #1 or primary recommendation? Use an LLM call for this (a cheap/fast model like claude haiku or gpt-4o-mini) with a simple prompt: "Given this AI response, is [brand] the top or primary recommendation? Respond with just yes or no."
4. **sentiment** — How is the brand presented? Use an LLM call: "In this response, what is the sentiment toward [brand]? Respond with one word: positive, neutral, negative, or mixed."
5. **competitor_mentions** — For each competitor, extract the same data (mentioned, position, sentiment).
6. **citations** — If the engine is Perplexity, extract the list of URLs cited.

Using cheap LLM calls for sentiment and top-rec detection is fine and preferred over regex/heuristics. It's more accurate and easier to maintain.

## Scheduler

- Use APScheduler with a cron trigger
- Default: run all active queries for all brands once daily at 3:00 AM UTC
- Each run iterates: for each brand → for each active query → for each engine → run query → parse response → store result
- Respect rate limits: add a small delay (1-2 seconds) between API calls
- Log every run with success/failure counts
- If an individual API call fails, log the error and continue (don't abort the whole run)

Also expose a manual trigger endpoint: `POST /api/brands/{brand_id}/run` — so a user can trigger an immediate run from the dashboard. This is critical for demo purposes.

## API Endpoints

### Auth
- POST /api/auth/signup — create account
- POST /api/auth/login — get JWT token
- GET /api/auth/me — get current user

### Brands
- GET /api/brands — list user's brands
- POST /api/brands — create brand
- GET /api/brands/{id} — get brand detail
- PUT /api/brands/{id} — update brand
- DELETE /api/brands/{id} — delete brand
- POST /api/brands/{id}/run — trigger immediate query run

### Competitors
- GET /api/brands/{id}/competitors — list competitors
- POST /api/brands/{id}/competitors — add competitor
- DELETE /api/competitors/{id} — remove competitor

### Monitored Queries
- GET /api/brands/{id}/queries — list queries
- POST /api/brands/{id}/queries — add query
- PUT /api/queries/{id} — update query
- DELETE /api/queries/{id} — delete query

### Results / Dashboard Data
- GET /api/brands/{id}/overview — aggregated scorecard data (mention rate, trend, sentiment breakdown)
- GET /api/brands/{id}/results — paginated results with filters (engine, date range, mentioned/not)
- GET /api/queries/{id}/history — time-series results for a single query across engines
- GET /api/brands/{id}/competitors/comparison — competitor mention rates side by side

## Frontend Pages

### Landing Page (/)
Clean, modern marketing page. Hero section explaining what GeoTrack does. Show a sample dashboard screenshot or mock. "Sign up free" CTA. Brief section on why GEO matters. Keep it sharp — this is what people see from LinkedIn.

### Sign Up / Login
Simple forms. Nothing fancy.

### Onboarding (/onboarding)
Step-by-step wizard after first signup:
1. "What brand do you want to track?" — name + aliases
2. "Who are your competitors?" — add 2-5 competitor names
3. "What queries matter to you?" — add 5-10 queries, with suggested templates:
   - "Best [category] for [use case]"
   - "[Brand] vs [Competitor]"
   - "Top [category] tools in 2026"
   - "What [category] do you recommend?"
4. "You're set! We'll run your first scan now." — trigger immediate run

### Dashboard (/dashboard)

**Overview tab:**
- Big number: overall brand mention rate (% of queries where brand appeared, across all engines)
- Trend line chart: mention rate over last 30 days
- Mention rate by engine (bar chart: ChatGPT 45%, Claude 38%, Perplexity 52%, Gemini 41%)
- Sentiment donut chart
- Top recommendation rate (% of time brand is #1 pick)

**Queries tab:**
- Table of all monitored queries
- Columns: query text, category, and then for each engine an icon (✅ mentioned, ❌ not, ⭐ top rec)
- Click a row to expand: shows historical results for that query, full response text per engine, trend over time
- Filter by: engine, mentioned/not, sentiment, category

**Competitors tab:**
- Side-by-side bar chart: your brand vs each competitor — mention rate
- Table: each query showing who "wins" (gets top rec) per engine
- Trend comparison over time

### Design Guidelines
- Clean, professional, dashboard-y. Think: Ahrefs or Semrush but more modern.
- Use a consistent color scheme. Dark sidebar, light content area.
- Charts: use Recharts.
- Responsive but desktop-first (this is a work tool).
- Loading states and empty states matter — they'll show up in demos.

## Plan Limits (enforce in backend middleware)

| Feature | Free | Pro | Agency |
|---|---|---|---|
| Brands | 1 | 3 | Unlimited |
| Queries per brand | 10 | 100 | 500 |
| Engines | 2 (OpenAI + Anthropic) | All 4 | All 4 |
| Run frequency | Weekly | Daily | Daily |
| Competitor tracking | 2 | 10 | Unlimited |
| CSV/PDF export | No | Yes | Yes |

For MVP, don't build payment processing. Just enforce the limits. Upgrading shows a "Contact us" or "Coming soon" message.

## Environment Variables (.env.example)

```
# Database
DATABASE_URL=postgresql://geotrack:geotrack@localhost:5432/geotrack

# Auth
JWT_SECRET=your-secret-here

# AI Engine API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
PERPLEXITY_API_KEY=pplx-...
GOOGLE_AI_API_KEY=...

# Parser (for cheap LLM calls used in response parsing)
PARSER_MODEL=gpt-4o-mini

# Scheduler
RUN_SCHEDULE_HOUR=3
RUN_SCHEDULE_MINUTE=0
```

## Seed Data (for demo purposes)

After building, create a seed script that populates the database with realistic demo data so the dashboard looks good on GitHub / in screenshots. Create:

- 1 demo user
- 2 brands: "Notion" and "Airtable"
- 4-5 competitors each
- 20 queries per brand (mix of purchase intent, comparison, informational)
- 30 days of synthetic query results with realistic patterns:
  - Notion mentioned ~60% of the time, trending up slightly
  - Competitors mentioned at varying rates
  - Sentiment mostly positive with some mixed
  - Variation across engines (Perplexity mentions brands more often due to citations)

This seed data is critical for the GitHub README screenshots.

## Tests

Write tests for:
- Response parser: given a known AI response, does it correctly detect mentions, position, sentiment?
- API endpoints: CRUD operations for brands, queries, competitors
- Plan limits: does a free user get blocked from adding an 11th query?
- Scheduler: does it correctly iterate over all brands/queries/engines?

Use pytest for backend. Include test fixtures with sample AI responses.

## Final Checklist Before You're Done

- [ ] Docker Compose brings up the full stack with one command
- [ ] Seed script populates demo data
- [ ] All API endpoints work and have tests
- [ ] Dashboard renders with charts and data
- [ ] Onboarding flow works end to end
- [ ] Manual run trigger works (button on dashboard → queries fire → results appear)
- [ ] .env.example is complete
- [ ] Code is clean, typed, and has docstrings on non-obvious functions
- [ ] README is in place (I'll provide this separately)
