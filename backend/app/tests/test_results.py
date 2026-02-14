"""Tests for result-related endpoints:

- GET /api/brands/{id}/overview
- GET /api/brands/{id}/results (paginated, filterable)
- GET /api/queries/{id}/history
- GET /api/brands/{id}/competitors/comparison
"""

import pytest
from uuid import uuid4
from datetime import date, timedelta

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

    async def test_competitor_comparison_date_scoping(
        self,
        client,
        auth_headers,
        db_session,
        sample_brand,
        sample_competitor,
        sample_query,
    ):
        """The `days` parameter should limit results to the given window."""
        today = date.today()
        # Create a recent result (today) and an old result (60 days ago)
        recent = QueryResult(
            id=uuid4(),
            query_id=sample_query.id,
            engine="openai",
            model_version="gpt-5.2",
            raw_response="TestBrand is great.",
            brand_mentioned=True,
            mention_position="first",
            is_top_recommendation=True,
            sentiment="positive",
            competitor_mentions={
                "CompetitorA": {
                    "mentioned": True,
                    "sentiment": "positive",
                    "position": "early",
                    "is_top_recommendation": False,
                }
            },
            citations=None,
            run_date=today,
        )
        old = QueryResult(
            id=uuid4(),
            query_id=sample_query.id,
            engine="anthropic",
            model_version="claude-sonnet",
            raw_response="TestBrand is okay.",
            brand_mentioned=True,
            mention_position="middle",
            is_top_recommendation=False,
            sentiment="neutral",
            competitor_mentions={
                "CompetitorA": {
                    "mentioned": True,
                    "sentiment": "negative",
                    "position": "first",
                    "is_top_recommendation": True,
                }
            },
            citations=None,
            run_date=today - timedelta(days=60),
        )
        db_session.add_all([recent, old])
        await db_session.commit()

        brand_id = str(sample_brand.id)

        # Without days filter: both results included
        resp_all = await client.get(
            f"/api/brands/{brand_id}/competitors/comparison",
            headers=auth_headers,
        )
        assert resp_all.status_code == 200
        data_all = resp_all.json()
        assert data_all["brand"]["mention_rate"] > 0

        # With days=7: only the recent result
        resp_scoped = await client.get(
            f"/api/brands/{brand_id}/competitors/comparison?days=7",
            headers=auth_headers,
        )
        assert resp_scoped.status_code == 200
        data_scoped = resp_scoped.json()
        # The recent result has positive sentiment for brand
        assert data_scoped["brand"]["sentiment_breakdown"]["positive"] == 1
        assert data_scoped["brand"]["sentiment_breakdown"]["neutral"] == 0

    async def test_competitor_comparison_query_winners_with_top_rec(
        self,
        client,
        auth_headers,
        db_session,
        sample_brand,
        sample_competitor,
        sample_query,
    ):
        """When a competitor has is_top_recommendation=True and the brand
        does not, the competitor should be the winner for that engine."""
        today = date.today()
        result = QueryResult(
            id=uuid4(),
            query_id=sample_query.id,
            engine="anthropic",
            model_version="claude-sonnet",
            raw_response="CompetitorA is the best choice.",
            brand_mentioned=True,
            mention_position="late",
            is_top_recommendation=False,
            sentiment="neutral",
            competitor_mentions={
                "CompetitorA": {
                    "mentioned": True,
                    "sentiment": "positive",
                    "position": "first",
                    "is_top_recommendation": True,
                }
            },
            citations=None,
            run_date=today,
        )
        db_session.add(result)
        await db_session.commit()

        brand_id = str(sample_brand.id)
        response = await client.get(
            f"/api/brands/{brand_id}/competitors/comparison",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Find the query winner entry
        qw = next(
            (w for w in data["query_winners"]
             if w["query_text"] == "What is the best testing tool?"),
            None,
        )
        assert qw is not None
        # The anthropic engine winner should be CompetitorA
        assert qw["winners"].get("anthropic") == "CompetitorA"


class TestOverviewSentimentFilter:
    async def test_sentiment_excludes_unmentioned_results(
        self,
        client,
        auth_headers,
        db_session,
        sample_brand,
        sample_query,
    ):
        """Sentiment breakdown should only count results where the brand
        is actually mentioned, not inflate neutral counts from misses."""
        results = [
            QueryResult(
                id=uuid4(),
                query_id=sample_query.id,
                engine="openai",
                model_version="gpt-5.2",
                raw_response="TestBrand is great.",
                brand_mentioned=True,
                mention_position="first",
                is_top_recommendation=True,
                sentiment="positive",
                competitor_mentions={},
                citations=None,
                run_date=date(2026, 2, 1),
            ),
            QueryResult(
                id=uuid4(),
                query_id=sample_query.id,
                engine="anthropic",
                model_version="claude-sonnet",
                raw_response="There are many tools available.",
                brand_mentioned=False,
                mention_position="not_mentioned",
                is_top_recommendation=False,
                sentiment="neutral",
                competitor_mentions={},
                citations=None,
                run_date=date(2026, 2, 2),
            ),
        ]
        for r in results:
            db_session.add(r)
        await db_session.commit()

        brand_id = str(sample_brand.id)
        response = await client.get(
            f"/api/brands/{brand_id}/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # 2 total runs, 1 mentioned
        assert data["total_runs"] == 2
        assert data["mention_rate"] == 0.5

        # Sentiment should only reflect the 1 mentioned result (positive)
        # The unmentioned result's "neutral" should NOT be counted
        assert data["sentiment_breakdown"]["positive"] == 1
        assert data["sentiment_breakdown"]["neutral"] == 0
