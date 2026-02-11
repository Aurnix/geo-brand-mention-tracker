"""Tests for competitor CRUD endpoints: /api/brands/{brand_id}/competitors."""

import pytest
from uuid import uuid4


class TestAddCompetitor:
    async def test_add_competitor(self, client, auth_headers, sample_brand):
        brand_id = str(sample_brand.id)
        response = await client.post(
            f"/api/brands/{brand_id}/competitors",
            json={"name": "RivalCo", "aliases": ["rival", "rivalco.io"]},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "RivalCo"
        assert data["aliases"] == ["rival", "rivalco.io"]
        assert data["brand_id"] == brand_id
        assert "id" in data
        assert "created_at" in data

    async def test_add_competitor_no_aliases(self, client, auth_headers, sample_brand):
        brand_id = str(sample_brand.id)
        response = await client.post(
            f"/api/brands/{brand_id}/competitors",
            json={"name": "SimpleComp"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "SimpleComp"
        assert data["aliases"] == []

    async def test_add_competitor_nonexistent_brand(self, client, auth_headers):
        fake_id = str(uuid4())
        response = await client.post(
            f"/api/brands/{fake_id}/competitors",
            json={"name": "GhostComp"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_add_competitor_empty_name(self, client, auth_headers, sample_brand):
        brand_id = str(sample_brand.id)
        response = await client.post(
            f"/api/brands/{brand_id}/competitors",
            json={"name": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestListCompetitors:
    async def test_list_competitors(
        self, client, auth_headers, sample_brand, sample_competitor
    ):
        brand_id = str(sample_brand.id)
        response = await client.get(
            f"/api/brands/{brand_id}/competitors",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(c["name"] == "CompetitorA" for c in data)

    async def test_list_competitors_empty(self, client, auth_headers, sample_brand):
        brand_id = str(sample_brand.id)
        response = await client.get(
            f"/api/brands/{brand_id}/competitors",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_list_competitors_nonexistent_brand(self, client, auth_headers):
        fake_id = str(uuid4())
        response = await client.get(
            f"/api/brands/{fake_id}/competitors",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestDeleteCompetitor:
    async def test_delete_competitor(
        self, client, auth_headers, sample_brand, sample_competitor
    ):
        brand_id = str(sample_brand.id)
        comp_id = str(sample_competitor.id)
        response = await client.delete(
            f"/api/brands/{brand_id}/competitors/{comp_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify it's gone
        list_resp = await client.get(
            f"/api/brands/{brand_id}/competitors",
            headers=auth_headers,
        )
        assert list_resp.status_code == 200
        names = [c["name"] for c in list_resp.json()]
        assert "CompetitorA" not in names

    async def test_delete_nonexistent_competitor(
        self, client, auth_headers, sample_brand
    ):
        brand_id = str(sample_brand.id)
        fake_comp_id = str(uuid4())
        response = await client.delete(
            f"/api/brands/{brand_id}/competitors/{fake_comp_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_delete_competitor_wrong_brand(
        self, client, auth_headers, sample_brand, sample_competitor
    ):
        """Deleting a competitor using a different (nonexistent) brand_id should fail."""
        fake_brand_id = str(uuid4())
        comp_id = str(sample_competitor.id)
        response = await client.delete(
            f"/api/brands/{fake_brand_id}/competitors/{comp_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404
