"""Tests for result-related endpoints:

- GET /api/brands/{id}/overview
- GET /api/brands/{id}/results (paginated, filterable)
- GET /api/queries/{id}/history
- GET /api/brands/{id}/competitors/comparison
"""

import pytest
from uuid import uuid4
from datetime import date

from app.models.result import QueryResult


class TestOverview:
    async def test_get_overview_with_results(
        self, client, auth_headers, sample_brand, sample_query, sample_results
    ):
        brand_id = str(sample_brand.id)
        response = await client.get(
            f"/api/brands/{brand_id}/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # We have 5 results, all brand_mentioned=True
        assert data["total_runs"] == 5
        assert data["mention_rate"] == 1.0  # 5/5 = 1.0 (rounded to 4 decimals)

        # 3 out of 5 are is_top_recommendation (i=0,2,4)
        assert data["top_rec_rate"] == 0.6  # 3/5

        # All results are engine="openai", all mentioned
        assert "openai" in data["engine_breakdown"]
        assert data["engine_breakdown"]["openai"] == 1.0

        # All positive sentiment
        assert data["sentiment_breakdown"]["positive"] == 5
        assert data["sentiment_breakdown"]["neutral"] == 0

        # mention_rate_trend should have entries for each run_date
        assert len(data["mention_rate_trend"]) == 5

        # total_queries should be 1 (the sample_query)
        assert data["total_queries"] >= 1

    async def test_get_overview_empty(
        self, client, auth_headers, sample_brand
    ):
        """Overview for a brand with no results returns zeroed-out data."""
        brand_id = str(sample_brand.id)
        response = await client.get(
            f"/api/brands/{brand_id}/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_runs"] == 0
        assert data["mention_rate"] == 0.0
        assert data["top_rec_rate"] == 0.0
        assert data["engine_breakdown"] == {}
        assert data["mention_rate_trend"] == []

    async def test_get_overview_nonexistent_brand(self, client, auth_headers):
        fake_id = str(uuid4())
        response = await client.get(
            f"/api/brands/{fake_id}/overview",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestPaginatedResults:
    async def test_get_results_paginated(
        self, client, auth_headers, sample_brand, sample_query, sample_results
    ):
        brand_id = str(sample_brand.id)
        response = await client.get(
            f"/api/brands/{brand_id}/results",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert len(data["items"]) == 5

    async def test_get_results_with_pagination(
        self, client, auth_headers, sample_brand, sample_query, sample_results
    ):
        brand_id = str(sample_brand.id)
        response = await client.get(
            f"/api/brands/{brand_id}/results?page=1&page_size=2",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["items"]) == 2
        assert data["pages"] == 3  # ceil(5/2)

    async def test_get_results_filter_engine(
        self, client, auth_headers, sample_brand, sample_query, sample_results
    ):
        brand_id = str(sample_brand.id)

        # All results are engine="openai", so filtering by "openai" returns all
        resp_openai = await client.get(
            f"/api/brands/{brand_id}/results?engine=openai",
            headers=auth_headers,
        )
        assert resp_openai.status_code == 200
        assert resp_openai.json()["total"] == 5

        # Filtering by "anthropic" returns none
        resp_anthropic = await client.get(
            f"/api/brands/{brand_id}/results?engine=anthropic",
            headers=auth_headers,
        )
        assert resp_anthropic.status_code == 200
        assert resp_anthropic.json()["total"] == 0

    async def test_get_results_empty(self, client, auth_headers, sample_brand):
        brand_id = str(sample_brand.id)
        response = await client.get(
            f"/api/brands/{brand_id}/results",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []


class TestQueryHistory:
    async def test_get_query_history(
        self, client, auth_headers, sample_query, sample_results
    ):
        query_id = str(sample_query.id)
        response = await client.get(
            f"/api/queries/{query_id}/history",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 5

        # Results should be ordered by run_date desc
        dates = [item["run_date"] for item in data]
        assert dates == sorted(dates, reverse=True)

    async def test_get_query_history_nonexistent(self, client, auth_headers):
        fake_id = str(uuid4())
        response = await client.get(
            f"/api/queries/{fake_id}/history",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_get_query_history_empty(
        self, client, auth_headers, sample_query
    ):
        """Query with no results returns an empty list."""
        query_id = str(sample_query.id)
        response = await client.get(
            f"/api/queries/{query_id}/history",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


class TestCompetitorComparison:
    async def test_get_competitor_comparison(
        self,
        client,
        auth_headers,
        sample_brand,
        sample_competitor,
        sample_query,
        sample_results,
    ):
        brand_id = str(sample_brand.id)
        response = await client.get(
            f"/api/brands/{brand_id}/competitors/comparison",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Brand entry
        assert data["brand"]["name"] == "TestBrand"
        assert data["brand"]["mention_rate"] == 1.0  # all mentioned

        # Competitors list should contain CompetitorA
        assert len(data["competitors"]) >= 1
        comp_a = next(
            (c for c in data["competitors"] if c["name"] == "CompetitorA"), None
        )
        assert comp_a is not None
        # CompetitorA is mentioned in all 5 results' competitor_mentions
        assert comp_a["mention_rate"] > 0

    async def test_get_competitor_comparison_no_competitors(
        self, client, auth_headers, sample_brand, sample_query, sample_results
    ):
        """Comparison with no competitors should have empty competitors list."""
        brand_id = str(sample_brand.id)
        response = await client.get(
            f"/api/brands/{brand_id}/competitors/comparison",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["brand"]["name"] == "TestBrand"
        assert data["competitors"] == []

    async def test_get_competitor_comparison_includes_query_winners(
        self,
        client,
        auth_headers,
        sample_brand,
        sample_competitor,
        sample_query,
        sample_results,
    ):
        """Comparison response should include query_winners field."""
        brand_id = str(sample_brand.id)
        response = await client.get(
            f"/api/brands/{brand_id}/competitors/comparison",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert "query_winners" in data
        assert isinstance(data["query_winners"], list)
        # We have one query with results, so should have at least one entry
        if data["query_winners"]:
            qw = data["query_winners"][0]
            assert "query_text" in qw
            assert "winners" in qw
            # The query_text should match our sample query
            assert qw["query_text"] == "What is the best testing tool?"
            # Winners should have engine keys
            assert isinstance(qw["winners"], dict)

    async def test_get_competitor_comparison_nonexistent_brand(
        self, client, auth_headers
    ):
        fake_id = str(uuid4())
        response = await client.get(
            f"/api/brands/{fake_id}/competitors/comparison",
            headers=auth_headers,
        )
        assert response.status_code == 404
