from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.services.scheduler import init_scheduler

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    init_scheduler()
    yield


app = FastAPI(
    title="GeoTrack API",
    description="Monitor brand mentions in AI-generated responses",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
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
    return {"status": "healthy", "service": "geotrack-api"}
