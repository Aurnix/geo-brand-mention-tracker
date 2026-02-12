"""Tests for the QueryRunner service.

Mocks AI engine calls and response parsing to test orchestration logic:
dedup checking, error handling, result storage, and stats tracking.
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.engines.base import EngineResponse
from app.models.brand import Brand, Competitor
from app.models.query import MonitoredQuery
from app.models.result import QueryResult
from app.services.query_runner import QueryRunner


@pytest.fixture
async def runner(db_session):
    return QueryRunner(db=db_session)


@pytest.fixture
def mock_engine_response():
    return EngineResponse(
        raw_text="TestBrand is a great tool for managing projects.",
        model_version="gpt-4o-test",
        citations=["https://example.com"],
    )


@pytest.fixture
def mock_parsed_result():
    m = MagicMock()
    m.brand_mentioned = True
    m.mention_position = "first"
    m.is_top_recommendation = True
    m.sentiment = "positive"
    m.competitor_mentions = {"CompetitorA": {"mentioned": True, "sentiment": "neutral"}}
    m.citations = ["https://example.com"]
    return m


class TestRunSingleQuery:
    @patch("app.services.query_runner.ENGINE_MAP")
    async def test_run_single_query_success(
        self,
        mock_engine_map,
        runner,
        db_session,
        sample_brand,
        sample_query,
        sample_competitor,
        mock_engine_response,
        mock_parsed_result,
    ):
        """Successfully runs a query, parses, and stores a result."""
        mock_engine_instance = AsyncMock()
        mock_engine_instance.run_query.return_value = mock_engine_response
        mock_engine_cls = MagicMock(return_value=mock_engine_instance)
        mock_engine_map.get.return_value = mock_engine_cls

        with patch.object(runner.parser, "parse", new_callable=AsyncMock) as mock_parse:
            mock_parse.return_value = mock_parsed_result

            result = await runner.run_single_query(
                query=sample_query,
                brand=sample_brand,
                competitors=[sample_competitor],
                engine_name="openai",
            )

        assert result is not None
        assert isinstance(result, QueryResult)
        assert result.engine == "openai"
        assert result.brand_mentioned is True
        assert result.is_top_recommendation is True
        assert result.sentiment == "positive"

    @patch("app.services.query_runner.ENGINE_MAP")
    async def test_run_single_query_unknown_engine(
        self, mock_engine_map, runner, sample_brand, sample_query
    ):
        """Returns None for an unknown engine name."""
        mock_engine_map.get.return_value = None

        result = await runner.run_single_query(
            query=sample_query,
            brand=sample_brand,
            competitors=[],
            engine_name="nonexistent",
        )
        assert result is None

    @patch("app.services.query_runner.ENGINE_MAP")
    async def test_run_single_query_engine_error(
        self, mock_engine_map, runner, sample_brand, sample_query
    ):
        """Returns None when the engine raises an exception."""
        mock_engine_instance = AsyncMock()
        mock_engine_instance.run_query.side_effect = Exception("API timeout")
        mock_engine_cls = MagicMock(return_value=mock_engine_instance)
        mock_engine_map.get.return_value = mock_engine_cls

        result = await runner.run_single_query(
            query=sample_query,
            brand=sample_brand,
            competitors=[],
            engine_name="openai",
        )
        assert result is None

    @patch("app.services.query_runner.ENGINE_MAP")
    async def test_run_single_query_parser_error(
        self,
        mock_engine_map,
        runner,
        sample_brand,
        sample_query,
        mock_engine_response,
    ):
        """Returns None when the parser raises an exception."""
        mock_engine_instance = AsyncMock()
        mock_engine_instance.run_query.return_value = mock_engine_response
        mock_engine_cls = MagicMock(return_value=mock_engine_instance)
        mock_engine_map.get.return_value = mock_engine_cls

        with patch.object(runner.parser, "parse", new_callable=AsyncMock) as mock_parse:
            mock_parse.side_effect = Exception("Parse failed")

            result = await runner.run_single_query(
                query=sample_query,
                brand=sample_brand,
                competitors=[],
                engine_name="openai",
            )
        assert result is None


class TestRunBrand:
    @patch("app.services.query_runner.asyncio.sleep", new_callable=AsyncMock)
    @patch("app.services.query_runner.ENGINE_MAP")
    async def test_run_brand_success(
        self,
        mock_engine_map,
        mock_sleep,
        runner,
        db_session,
        sample_brand,
        sample_query,
        mock_engine_response,
        mock_parsed_result,
    ):
        """Run brand processes all queries and engines."""
        mock_engine_instance = AsyncMock()
        mock_engine_instance.run_query.return_value = mock_engine_response
        mock_engine_cls = MagicMock(return_value=mock_engine_instance)
        mock_engine_map.get.return_value = mock_engine_cls

        with patch.object(runner.parser, "parse", new_callable=AsyncMock) as mock_parse:
            mock_parse.return_value = mock_parsed_result

            stats = await runner.run_brand(sample_brand, ["openai"])

        assert stats["total"] == 1
        assert stats["success"] == 1
        assert stats["failed"] == 0
        assert stats["skipped"] == 0

    async def test_run_brand_no_active_queries(
        self, runner, db_session, sample_brand
    ):
        """Returns empty stats when brand has no active queries."""
        # sample_brand has no queries by default (sample_query not used)
        stats = await runner.run_brand(sample_brand, ["openai"])
        assert stats["total"] == 0
        assert stats["success"] == 0

    @patch("app.services.query_runner.asyncio.sleep", new_callable=AsyncMock)
    @patch("app.services.query_runner.ENGINE_MAP")
    async def test_run_brand_dedup_skips_existing(
        self,
        mock_engine_map,
        mock_sleep,
        runner,
        db_session,
        sample_brand,
        sample_query,
        mock_engine_response,
        mock_parsed_result,
    ):
        """Skips query+engine+date combinations that already have results."""
        # Create an existing result for today
        existing = QueryResult(
            id=uuid4(),
            query_id=sample_query.id,
            engine="openai",
            model_version="gpt-4o",
            raw_response="existing",
            brand_mentioned=False,
            mention_position="not_mentioned",
            is_top_recommendation=False,
            sentiment="neutral",
            run_date=date.today(),
        )
        db_session.add(existing)
        await db_session.commit()

        stats = await runner.run_brand(sample_brand, ["openai"])
        assert stats["total"] == 1
        assert stats["skipped"] == 1
        assert stats["success"] == 0
