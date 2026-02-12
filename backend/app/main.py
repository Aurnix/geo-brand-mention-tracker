from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings
from app.services.scheduler import init_scheduler

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    init_scheduler()
    yield


limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(
    title="GeoTrack API",
    description="Monitor brand mentions in AI-generated responses",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from app.api.routes import auth, brands, queries, results  # noqa: E402

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(brands.router, prefix="/api/brands", tags=["brands"])
# queries/results routers have mixed paths (/brands/... and /queries/...)
app.include_router(queries.router, prefix="/api", tags=["queries"])
app.include_router(results.router, prefix="/api", tags=["results"])


@app.get("/api/health", tags=["health"])
async def health_check() -> dict:
    from sqlalchemy import text
    from app.database import async_session_factory

    db_ok = False
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        pass

    health_status = "healthy" if db_ok else "degraded"
    return {"status": health_status, "service": "geotrack-api", "database": db_ok}
