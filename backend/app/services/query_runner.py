import asyncio
import logging
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.engines import ENGINE_MAP
from app.engines.base import BaseEngine, EngineResponse
from app.models.brand import Brand, Competitor
from app.models.query import MonitoredQuery
from app.models.result import QueryResult
from app.services.response_parser import ResponseParser

logger = logging.getLogger(__name__)


class QueryRunner:
    """Orchestrates running monitored queries against AI engines and
    persisting the parsed results."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.parser = ResponseParser()

    async def run_brand(self, brand: Brand, engines: list[str]) -> dict:
        """Run all active queries for a brand across specified engines.

        Args:
            brand: The Brand ORM instance (with relationships loaded).
            engines: List of engine names to run queries against.

        Returns:
            A stats dict with keys: total, success, failed, skipped.
        """
        stats = {"total": 0, "success": 0, "failed": 0, "skipped": 0}

        # Load active monitored queries for this brand
        stmt = (
            select(MonitoredQuery)
            .where(
                MonitoredQuery.brand_id == brand.id,
                MonitoredQuery.is_active.is_(True),
            )
        )
        result = await self.db.execute(stmt)
        queries = result.scalars().all()

        if not queries:
            logger.info("Brand '%s' has no active queries. Skipping.", brand.name)
            return stats

        # Load competitors for this brand
        comp_stmt = select(Competitor).where(Competitor.brand_id == brand.id)
        comp_result = await self.db.execute(comp_stmt)
        competitors = comp_result.scalars().all()

        today = date.today()

        for query in queries:
            for engine_name in engines:
                stats["total"] += 1

                # Check if this query+engine+date combination already exists
                existing_stmt = select(QueryResult).where(
                    QueryResult.query_id == query.id,
                    QueryResult.engine == engine_name,
                    QueryResult.run_date == today,
                )
                existing_result = await self.db.execute(existing_stmt)
                if existing_result.scalar_one_or_none() is not None:
                    logger.info(
                        "Result already exists for query=%s engine=%s date=%s. Skipping.",
                        query.id,
                        engine_name,
                        today,
                    )
                    stats["skipped"] += 1
                    continue

                query_result = await self.run_single_query(
                    query=query,
                    brand=brand,
                    competitors=competitors,
                    engine_name=engine_name,
                )
                if query_result is not None:
                    stats["success"] += 1
                else:
                    stats["failed"] += 1

                # Rate-limit between API calls
                await asyncio.sleep(1.5)

        logger.info(
            "Brand '%s' run complete. Stats: %s",
            brand.name,
            stats,
        )
        return stats

    async def run_single_query(
        self,
        query: MonitoredQuery,
        brand: Brand,
        competitors: list[Competitor],
        engine_name: str,
    ) -> QueryResult | None:
        """Run a single query against a single engine, parse, and store.

        Args:
            query: The MonitoredQuery to execute.
            brand: The parent Brand object.
            competitors: List of Competitor ORM objects for the brand.
            engine_name: Name of the AI engine to use.

        Returns:
            The persisted QueryResult, or None if an error occurred.
        """
        engine_cls = ENGINE_MAP.get(engine_name)
        if engine_cls is None:
            logger.error("Unknown engine '%s'. Skipping.", engine_name)
            return None

        try:
            engine: BaseEngine = engine_cls()
            logger.info(
                "Running query '%s' (id=%s) on engine '%s'",
                query.query_text[:60],
                query.id,
                engine_name,
            )
            engine_response: EngineResponse = await engine.run_query(
                query.query_text
            )
        except Exception:
            logger.exception(
                "Engine '%s' failed for query id=%s", engine_name, query.id
            )
            return None

        try:
            # Build competitor dicts for the parser
            comp_dicts = [
                {"name": c.name, "aliases": c.aliases or []}
                for c in competitors
            ]

            parsed = await self.parser.parse(
                raw_response=engine_response.raw_text,
                brand_name=brand.name,
                brand_aliases=brand.aliases or [],
                competitors=comp_dicts,
                citations=engine_response.citations,
            )
        except Exception:
            logger.exception(
                "Parser failed for query id=%s engine=%s",
                query.id,
                engine_name,
            )
            return None

        try:
            query_result = QueryResult(
                query_id=query.id,
                engine=engine_name,
                model_version=engine_response.model_version,
                raw_response=engine_response.raw_text,
                brand_mentioned=parsed.brand_mentioned,
                mention_position=parsed.mention_position,
                is_top_recommendation=parsed.is_top_recommendation,
                sentiment=parsed.sentiment,
                competitor_mentions=parsed.competitor_mentions,
                citations=parsed.citations,
                run_date=date.today(),
            )
            self.db.add(query_result)
            await self.db.flush()

            logger.info(
                "Stored result id=%s for query=%s engine=%s (brand_mentioned=%s)",
                query_result.id,
                query.id,
                engine_name,
                parsed.brand_mentioned,
            )
            return query_result
        except Exception:
            logger.exception(
                "Failed to persist result for query id=%s engine=%s",
                query.id,
                engine_name,
            )
            return None
