"""Tests for monitored query CRUD endpoints under /api/brands/{id}/queries and /api/queries/{id}."""

import pytest
from uuid import uuid4


class TestCreateQuery:
    async def test_create_query(self, client, auth_headers, sample_brand):
        brand_id = str(sample_brand.id)
        response = await client.post(
            f"/api/brands/{brand_id}/queries",
            json={
                "query_text": "What is the best CI/CD tool?",
                "category": "comparison",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["query_text"] == "What is the best CI/CD tool?"
        assert data["category"] == "comparison"
        assert data["is_active"] is True
        assert "id" in data
        assert data["brand_id"] == brand_id

    async def test_create_query_no_category(self, client, auth_headers, sample_brand):
        brand_id = str(sample_brand.id)
        response = await client.post(
            f"/api/brands/{brand_id}/queries",
            json={"query_text": "Tell me about testing frameworks"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["category"] is None

    async def test_create_query_for_nonexistent_brand(self, client, auth_headers):
        fake_id = str(uuid4())
        response = await client.post(
            f"/api/brands/{fake_id}/queries",
            json={"query_text": "Some query", "category": "general"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_create_query_for_other_users_brand(
        self, client, async_engine, sample_brand
    ):
        """Another user cannot create queries for a brand they do not own."""
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
        from passlib.context import CryptContext
        from jose import jwt as jose_jwt
        from app.config import get_settings
        from app.models.user import User
        from datetime import datetime, timezone

        settings = get_settings()
        pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

        factory = async_sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with factory() as session:
            other = User(
                id=uuid4(),
                email="other_query@example.com",
                password_hash=pwd_ctx.hash("otherpass123"),
                plan_tier="free",
            )
            session.add(other)
            await session.commit()
            await session.refresh(other)

        token = jose_jwt.encode(
            {"sub": str(other.id), "exp": datetime(2030, 1, 1, tzinfo=timezone.utc)},
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            f"/api/brands/{sample_brand.id}/queries",
            json={"query_text": "Sneaky query"},
            headers=headers,
        )
        assert response.status_code in (403, 404)


class TestListQueries:
    async def test_list_queries(self, client, auth_headers, sample_brand, sample_query):
        brand_id = str(sample_brand.id)
        response = await client.get(
            f"/api/brands/{brand_id}/queries",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(q["query_text"] == "What is the best testing tool?" for q in data)

    async def test_list_queries_empty(self, client, auth_headers, sample_brand):
        """Brand with no queries should return an empty list."""
        brand_id = str(sample_brand.id)
        response = await client.get(
            f"/api/brands/{brand_id}/queries",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


class TestGetQuery:
    async def test_get_query(self, client, auth_headers, sample_query):
        query_id = str(sample_query.id)
        response = await client.get(
            f"/api/queries/{query_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["query_text"] == "What is the best testing tool?"

    async def test_get_nonexistent_query(self, client, auth_headers):
        fake_id = str(uuid4())
        response = await client.get(
            f"/api/queries/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestUpdateQuery:
    async def test_update_query(self, client, auth_headers, sample_query):
        query_id = str(sample_query.id)
        response = await client.patch(
            f"/api/queries/{query_id}",
            json={
                "query_text": "Updated query text?",
                "category": "updated-category",
                "is_active": False,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["query_text"] == "Updated query text?"
        assert data["category"] == "updated-category"
        assert data["is_active"] is False

    async def test_update_query_partial(self, client, auth_headers, sample_query):
        query_id = str(sample_query.id)
        response = await client.patch(
            f"/api/queries/{query_id}",
            json={"is_active": False},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        # Original text should be unchanged
        assert data["query_text"] == "What is the best testing tool?"

    async def test_update_nonexistent_query(self, client, auth_headers):
        fake_id = str(uuid4())
        response = await client.patch(
            f"/api/queries/{fake_id}",
            json={"query_text": "Nope"},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestDeleteQuery:
    async def test_delete_query(self, client, auth_headers, sample_query):
        query_id = str(sample_query.id)
        response = await client.delete(
            f"/api/queries/{query_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify it's gone
        get_resp = await client.get(
            f"/api/queries/{query_id}",
            headers=auth_headers,
        )
        assert get_resp.status_code == 404

    async def test_delete_nonexistent_query(self, client, auth_headers):
        fake_id = str(uuid4())
        response = await client.delete(
            f"/api/queries/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404
