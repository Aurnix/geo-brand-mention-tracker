"""Tests for authentication endpoints: /api/auth/signup, /api/auth/login, /api/auth/me."""

import pytest


class TestSignup:
    async def test_signup_success(self, client):
        response = await client.post(
            "/api/auth/signup",
            json={"email": "new@example.com", "password": "strongpass123"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # The TokenResponse also includes a nested user object
        assert "user" in data
        assert data["user"]["email"] == "new@example.com"
        assert data["user"]["plan_tier"] == "free"

    async def test_signup_duplicate_email(self, client):
        payload = {"email": "dupe@example.com", "password": "strongpass123"}
        first = await client.post("/api/auth/signup", json=payload)
        assert first.status_code == 201

        second = await client.post("/api/auth/signup", json=payload)
        assert second.status_code == 409
        assert "already exists" in second.json()["detail"].lower()

    async def test_signup_invalid_email(self, client):
        response = await client.post(
            "/api/auth/signup",
            json={"email": "not-an-email", "password": "strongpass123"},
        )
        assert response.status_code == 422

    async def test_signup_short_password(self, client):
        response = await client.post(
            "/api/auth/signup",
            json={"email": "short@example.com", "password": "short"},
        )
        assert response.status_code == 422


class TestLogin:
    async def test_login_success(self, client):
        # First register
        await client.post(
            "/api/auth/signup",
            json={"email": "login@example.com", "password": "strongpass123"},
        )
        # Then login
        response = await client.post(
            "/api/auth/login",
            json={"email": "login@example.com", "password": "strongpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == "login@example.com"

    async def test_login_wrong_password(self, client):
        await client.post(
            "/api/auth/signup",
            json={"email": "wrongpw@example.com", "password": "strongpass123"},
        )
        response = await client.post(
            "/api/auth/login",
            json={"email": "wrongpw@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    async def test_login_nonexistent_user(self, client):
        response = await client.post(
            "/api/auth/login",
            json={"email": "noone@example.com", "password": "irrelevant123"},
        )
        assert response.status_code == 401


class TestGetMe:
    async def test_get_me(self, client, auth_headers):
        response = await client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "id" in data
        assert "plan_tier" in data
        assert "created_at" in data

    async def test_get_me_unauthorized(self, client):
        response = await client.get("/api/auth/me")
        # HTTPBearer returns 403 when no credentials are provided
        assert response.status_code in (401, 403)

    async def test_get_me_invalid_token(self, client):
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid-token-here"},
        )
        assert response.status_code == 401
