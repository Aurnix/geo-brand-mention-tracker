"""Tests for brand CRUD endpoints: /api/brands."""

import pytest
from uuid import uuid4


class TestCreateBrand:
    async def test_create_brand(self, client, auth_headers):
        response = await client.post(
            "/api/brands/",
            json={"name": "NewBrand", "aliases": ["nb", "new-brand.com"]},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "NewBrand"
        assert data["aliases"] == ["nb", "new-brand.com"]
        assert "id" in data
        assert "created_at" in data

    async def test_create_brand_unauthorized(self, client):
        response = await client.post(
            "/api/brands/",
            json={"name": "NoBrand", "aliases": []},
        )
        # HTTPBearer returns 403 when no credentials are provided
        assert response.status_code in (401, 403)

    async def test_create_brand_no_aliases(self, client, auth_headers):
        response = await client.post(
            "/api/brands/",
            json={"name": "MinimalBrand"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "MinimalBrand"
        assert data["aliases"] == []

    async def test_create_brand_empty_name(self, client, auth_headers):
        response = await client.post(
            "/api/brands/",
            json={"name": "", "aliases": []},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestListBrands:
    async def test_list_brands(self, client, auth_headers, sample_brand):
        response = await client.get("/api/brands/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(b["name"] == "TestBrand" for b in data)

    async def test_list_brands_empty(self, client, auth_headers):
        response = await client.get("/api/brands/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


class TestGetBrand:
    async def test_get_brand(self, client, auth_headers, sample_brand):
        brand_id = str(sample_brand.id)
        response = await client.get(
            f"/api/brands/{brand_id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TestBrand"
        assert data["aliases"] == ["test-brand", "testbrand.com"]

    async def test_get_nonexistent_brand(self, client, auth_headers):
        fake_id = str(uuid4())
        response = await client.get(
            f"/api/brands/{fake_id}", headers=auth_headers
        )
        assert response.status_code == 404

    async def test_get_other_users_brand(self, client, async_engine, sample_brand):
        """A different user should not be able to access another user's brand."""
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
        from passlib.context import CryptContext
        from jose import jwt as jose_jwt
        from app.config import get_settings
        from app.models.user import User
        from datetime import datetime, timezone

        settings = get_settings()
        pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

        session_factory = async_sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            other_user = User(
                id=uuid4(),
                email="other@example.com",
                password_hash=pwd_ctx.hash("otherpass123"),
                plan_tier="free",
            )
            session.add(other_user)
            await session.commit()
            await session.refresh(other_user)

        other_token = jose_jwt.encode(
            {
                "sub": str(other_user.id),
                "exp": datetime(2030, 1, 1, tzinfo=timezone.utc),
            },
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
        other_headers = {"Authorization": f"Bearer {other_token}"}

        response = await client.get(
            f"/api/brands/{sample_brand.id}", headers=other_headers
        )
        assert response.status_code == 404


class TestUpdateBrand:
    async def test_update_brand(self, client, auth_headers, sample_brand):
        brand_id = str(sample_brand.id)
        response = await client.put(
            f"/api/brands/{brand_id}",
            json={"name": "UpdatedBrand", "aliases": ["updated"]},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "UpdatedBrand"
        assert data["aliases"] == ["updated"]

    async def test_update_brand_partial(self, client, auth_headers, sample_brand):
        """PUT with only name should update name, keep aliases unchanged."""
        brand_id = str(sample_brand.id)
        response = await client.put(
            f"/api/brands/{brand_id}",
            json={"name": "OnlyNameUpdated"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "OnlyNameUpdated"
        # aliases should remain unchanged since BrandUpdate allows None
        assert data["aliases"] == ["test-brand", "testbrand.com"]

    async def test_update_nonexistent_brand(self, client, auth_headers):
        fake_id = str(uuid4())
        response = await client.put(
            f"/api/brands/{fake_id}",
            json={"name": "Nope"},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestDeleteBrand:
    async def test_delete_brand(self, client, auth_headers, sample_brand):
        brand_id = str(sample_brand.id)
        response = await client.delete(
            f"/api/brands/{brand_id}", headers=auth_headers
        )
        assert response.status_code == 204

        # Verify it's gone
        get_resp = await client.get(
            f"/api/brands/{brand_id}", headers=auth_headers
        )
        assert get_resp.status_code == 404

    async def test_delete_nonexistent_brand(self, client, auth_headers):
        fake_id = str(uuid4())
        response = await client.delete(
            f"/api/brands/{fake_id}", headers=auth_headers
        )
        assert response.status_code == 404
