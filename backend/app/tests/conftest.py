"""
Shared test fixtures for the GeoTrack backend test suite.

Uses aiosqlite in-memory database for test isolation.
Handles UUID-to-string conversion for SQLite compatibility with
PostgreSQL-specific PG_UUID columns and gen_random_uuid() defaults.
"""

import os

# Set environment variables BEFORE any app imports so get_settings() picks them up.
# Use a fake postgresql URL for the module-level engine in database.py.
# We never actually connect to it because get_db is overridden per-test.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-unit-tests")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("PERPLEXITY_API_KEY", "test-key")
os.environ.setdefault("GOOGLE_AI_API_KEY", "test-key")

import uuid as _uuid_mod

import pytest
import sqlalchemy as sa
from uuid import uuid4
from datetime import datetime, date, timezone

from httpx import AsyncClient, ASGITransport
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from passlib.context import CryptContext
from jose import jwt

# ---------------------------------------------------------------------------
# SQLite compatibility: compile PG_UUID as VARCHAR(36)
# ---------------------------------------------------------------------------
from sqlalchemy.ext.compiler import compiles


@compiles(PG_UUID, "sqlite")
def compile_pg_uuid_for_sqlite(type_, compiler, **kw):
    return "VARCHAR(36)"


# ---------------------------------------------------------------------------
# App imports (after env vars are set)
# ---------------------------------------------------------------------------
from app.main import app
from app.database import get_db, Base
from app.models.user import User
from app.models.brand import Brand, Competitor
from app.models.query import MonitoredQuery
from app.models.result import QueryResult
from app.config import get_settings

TEST_DATABASE_URL = "sqlite+aiosqlite://"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _gen_random_uuid() -> str:
    """SQLite user-defined function to mimic PostgreSQL gen_random_uuid()."""
    return str(_uuid_mod.uuid4())


# ---------------------------------------------------------------------------
# Patch metadata: replace gen_random_uuid() server defaults with Python-side
# defaults so that INSERTs without explicit IDs work on SQLite.
# This needs to run exactly once before any create_all().
# ---------------------------------------------------------------------------
_metadata_patched = False


class _SQLiteUUID(sa.types.TypeDecorator):
    """A UUID type that works with both PostgreSQL and SQLite.

    Stores UUIDs as 36-character strings in SQLite while accepting
    and returning ``uuid.UUID`` objects in Python.
    """

    impl = sa.String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if isinstance(value, _uuid_mod.UUID):
                return str(value)
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if not isinstance(value, _uuid_mod.UUID):
                return _uuid_mod.UUID(str(value))
            return value
        return value


def _patch_metadata_for_sqlite():
    global _metadata_patched
    if _metadata_patched:
        return
    _metadata_patched = True

    for table in Base.metadata.tables.values():
        for column in table.columns:
            # Replace PG_UUID type with our SQLite-compatible UUID type
            if isinstance(column.type, PG_UUID):
                column.type = _SQLiteUUID()

            # Replace gen_random_uuid() server defaults with Python defaults
            sd = column.server_default
            if sd is not None and hasattr(sd, "arg"):
                text_val = str(sd.arg)
                if "gen_random_uuid" in text_val:
                    column.server_default = None
                    if column.default is None:
                        column.default = sa.ColumnDefault(_uuid_mod.uuid4)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
async def async_engine():
    _patch_metadata_for_sqlite()

    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Register gen_random_uuid() on each raw DBAPI connection in case any
    # raw SQL references it.
    @event.listens_for(engine.sync_engine, "connect")
    def _register_sqlite_functions(dbapi_conn, connection_record):
        dbapi_conn.create_function("gen_random_uuid", 0, _gen_random_uuid)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(async_engine):
    session_factory = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(async_engine):
    session_factory = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session):
    user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash=pwd_context.hash("testpassword123"),
        plan_tier="free",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user):
    settings = get_settings()
    token = jwt.encode(
        {"sub": str(test_user.id), "exp": datetime(2030, 1, 1, tzinfo=timezone.utc)},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
async def sample_brand(db_session, test_user):
    brand = Brand(
        id=uuid4(),
        user_id=test_user.id,
        name="TestBrand",
        aliases=["test-brand", "testbrand.com"],
    )
    db_session.add(brand)
    await db_session.commit()
    await db_session.refresh(brand)
    return brand


@pytest.fixture
async def sample_competitor(db_session, sample_brand):
    comp = Competitor(
        id=uuid4(),
        brand_id=sample_brand.id,
        name="CompetitorA",
        aliases=["competitor-a"],
    )
    db_session.add(comp)
    await db_session.commit()
    await db_session.refresh(comp)
    return comp


@pytest.fixture
async def sample_query(db_session, sample_brand):
    query = MonitoredQuery(
        id=uuid4(),
        brand_id=sample_brand.id,
        query_text="What is the best testing tool?",
        category="comparison",
        is_active=True,
    )
    db_session.add(query)
    await db_session.commit()
    await db_session.refresh(query)
    return query


@pytest.fixture
async def sample_results(db_session, sample_query):
    results = []
    for i in range(5):
        result = QueryResult(
            id=uuid4(),
            query_id=sample_query.id,
            engine="openai",
            model_version="gpt-5.2",
            raw_response=f"TestBrand is a great tool for testing. Day {i}.",
            brand_mentioned=True,
            mention_position="first",
            is_top_recommendation=(i % 2 == 0),
            sentiment="positive",
            competitor_mentions={
                "CompetitorA": {
                    "mentioned": True,
                    "sentiment": "neutral",
                    "position": "middle",
                    "is_top_recommendation": False,
                }
            },
            citations=None,
            run_date=date(2026, 1, i + 1),
        )
        results.append(result)
        db_session.add(result)
    await db_session.commit()
    return results
