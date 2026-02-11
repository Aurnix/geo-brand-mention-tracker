"""Tests for plan-level enforcement of brand, query, and competitor limits.

Free plan: 1 brand, 10 queries/brand, 2 competitors/brand, engines: [openai, anthropic]
Pro plan: 3 brands, 100 queries/brand, 10 competitors/brand, engines: all 4
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from passlib.context import CryptContext
from jose import jwt as jose_jwt

from app.config import get_settings
from app.models.user import User
from app.services.plan_limits import (
    get_plan_limits,
    check_brand_limit,
    check_query_limit,
    check_competitor_limit,
    get_allowed_engines,
)


# ---------------------------------------------------------------------------
# Helper to create a user with a specific plan tier and return auth headers
# ---------------------------------------------------------------------------

async def _make_user_headers(async_engine, email, plan_tier):
    """Create a user with the given plan and return (user, auth_headers)."""
    settings = get_settings()
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    factory = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with factory() as session:
        user = User(
            id=uuid4(),
            email=email,
            password_hash=pwd_ctx.hash("testpass1234"),
            plan_tier=plan_tier,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    token = jose_jwt.encode(
        {"sub": str(user.id), "exp": datetime(2030, 1, 1, tzinfo=timezone.utc)},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return user, {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Unit tests for plan_limits service functions
# ---------------------------------------------------------------------------

class TestPlanLimitsService:
    def test_free_plan_limits(self):
        limits = get_plan_limits("free")
        assert limits["brands"] == 1
        assert limits["queries_per_brand"] == 10
        assert limits["competitors"] == 2
        assert limits["engines"] == ["openai", "anthropic"]

    def test_pro_plan_limits(self):
        limits = get_plan_limits("pro")
        assert limits["brands"] == 3
        assert limits["queries_per_brand"] == 100
        assert limits["competitors"] == 10
        assert set(limits["engines"]) == {"openai", "anthropic", "perplexity", "gemini"}

    def test_agency_plan_limits(self):
        limits = get_plan_limits("agency")
        assert limits["brands"] == 999999
        assert limits["queries_per_brand"] == 500

    def test_unknown_plan_falls_back_to_free(self):
        limits = get_plan_limits("nonexistent")
        assert limits == get_plan_limits("free")

    def test_check_brand_limit_under(self):
        assert check_brand_limit(0, "free") is True

    def test_check_brand_limit_at(self):
        assert check_brand_limit(1, "free") is False

    def test_check_query_limit(self):
        assert check_query_limit(9, "free") is True
        assert check_query_limit(10, "free") is False

    def test_check_competitor_limit(self):
        assert check_competitor_limit(1, "free") is True
        assert check_competitor_limit(2, "free") is False

    def test_get_allowed_engines_free(self):
        engines = get_allowed_engines("free")
        assert engines == ["openai", "anthropic"]

    def test_get_allowed_engines_pro(self):
        engines = get_allowed_engines("pro")
        assert set(engines) == {"openai", "anthropic", "perplexity", "gemini"}


# ---------------------------------------------------------------------------
# Integration tests: plan enforcement via API endpoints
# ---------------------------------------------------------------------------

class TestFreePlanBrandLimit:
    async def test_free_plan_brand_limit(self, client, async_engine):
        """Free user can create 1 brand; the 2nd should fail with 403."""
        _, headers = await _make_user_headers(
            async_engine, "free_limit@example.com", "free"
        )

        # Create first brand -- should succeed
        resp1 = await client.post(
            "/api/brands/",
            json={"name": "Brand1"},
            headers=headers,
        )
        assert resp1.status_code == 201

        # Create second brand -- should be rejected
        resp2 = await client.post(
            "/api/brands/",
            json={"name": "Brand2"},
            headers=headers,
        )
        assert resp2.status_code == 403
        assert "limit" in resp2.json()["detail"].lower()


class TestFreePlanQueryLimit:
    async def test_free_plan_query_limit(self, client, async_engine):
        """Free user can create 10 queries per brand; the 11th should fail."""
        _, headers = await _make_user_headers(
            async_engine, "free_query_limit@example.com", "free"
        )

        # Create a brand first
        brand_resp = await client.post(
            "/api/brands/",
            json={"name": "QueryLimitBrand"},
            headers=headers,
        )
        assert brand_resp.status_code == 201
        brand_id = brand_resp.json()["id"]

        # Create 10 queries -- all should succeed
        for i in range(10):
            r = await client.post(
                f"/api/brands/{brand_id}/queries",
                json={"query_text": f"Query number {i + 1}"},
                headers=headers,
            )
            assert r.status_code == 201, f"Query {i + 1} failed: {r.text}"

        # 11th query should fail
        resp = await client.post(
            f"/api/brands/{brand_id}/queries",
            json={"query_text": "Query number 11"},
            headers=headers,
        )
        assert resp.status_code == 403
        assert "limit" in resp.json()["detail"].lower()


class TestFreePlanCompetitorLimit:
    async def test_free_plan_competitor_limit(self, client, async_engine):
        """Free user can create 2 competitors per brand; the 3rd should fail."""
        _, headers = await _make_user_headers(
            async_engine, "free_comp_limit@example.com", "free"
        )

        brand_resp = await client.post(
            "/api/brands/",
            json={"name": "CompLimitBrand"},
            headers=headers,
        )
        assert brand_resp.status_code == 201
        brand_id = brand_resp.json()["id"]

        # Create 2 competitors
        for i in range(2):
            r = await client.post(
                f"/api/brands/{brand_id}/competitors",
                json={"name": f"Comp{i + 1}"},
                headers=headers,
            )
            assert r.status_code == 201, f"Competitor {i + 1} failed: {r.text}"

        # 3rd should fail
        resp = await client.post(
            f"/api/brands/{brand_id}/competitors",
            json={"name": "Comp3"},
            headers=headers,
        )
        assert resp.status_code == 403
        assert "limit" in resp.json()["detail"].lower()


class TestProPlanHigherLimits:
    async def test_pro_plan_higher_brand_limit(self, client, async_engine):
        """Pro user can create up to 3 brands."""
        _, headers = await _make_user_headers(
            async_engine, "pro_brands@example.com", "pro"
        )

        for i in range(3):
            r = await client.post(
                "/api/brands/",
                json={"name": f"ProBrand{i + 1}"},
                headers=headers,
            )
            assert r.status_code == 201, f"Brand {i + 1} failed: {r.text}"

        # 4th should be rejected
        resp = await client.post(
            "/api/brands/",
            json={"name": "ProBrand4"},
            headers=headers,
        )
        assert resp.status_code == 403
