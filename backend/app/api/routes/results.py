from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.brand import Brand, Competitor
from app.models.query import MonitoredQuery
from app.models.result import QueryResult
from app.models.user import User
from app.schemas.result import (
    CompetitorComparisonEntry,
    CompetitorComparisonResponse,
    OverviewResponse,
    MentionRateTrend,
    PaginatedResults,
    QueryWinner,
    ResultResponse,
    SentimentBreakdown,
)

router = APIRouter()


@router.get("/brands/{brand_id}/results", response_model=PaginatedResults)
async def list_results(
    brand_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    engine: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResults:
    brand_check = await db.execute(
        select(Brand).where(Brand.id == brand_id, Brand.user_id == current_user.id)
    )
    if not brand_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found"
        )

    base_query = (
        select(QueryResult)
        .join(MonitoredQuery, QueryResult.query_id == MonitoredQuery.id)
        .where(MonitoredQuery.brand_id == brand_id)
    )
    count_query = (
        select(func.count())
        .select_from(QueryResult)
        .join(MonitoredQuery, QueryResult.query_id == MonitoredQuery.id)
        .where(MonitoredQuery.brand_id == brand_id)
    )

    if engine:
        base_query = base_query.where(QueryResult.engine == engine)
        count_query = count_query.where(QueryResult.engine == engine)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    results = await db.execute(
        base_query.order_by(QueryResult.run_date.desc(), QueryResult.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = results.scalars().all()

    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return PaginatedResults(
        items=[ResultResponse.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/brands/{brand_id}/overview", response_model=OverviewResponse)
async def get_overview(
    brand_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OverviewResponse:
    brand_check = await db.execute(
        select(Brand).where(Brand.id == brand_id, Brand.user_id == current_user.id)
    )
    if not brand_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found"
        )

    base_filter = (
        select(QueryResult)
        .join(MonitoredQuery, QueryResult.query_id == MonitoredQuery.id)
        .where(MonitoredQuery.brand_id == brand_id)
    )

    all_results = await db.execute(base_filter)
    results_list = all_results.scalars().all()

    total_runs = len(results_list)
    if total_runs == 0:
        return OverviewResponse(
            mention_rate=0.0,
            mention_rate_trend=[],
            engine_breakdown={},
            sentiment_breakdown=SentimentBreakdown(),
            top_rec_rate=0.0,
            total_queries=0,
            total_runs=0,
        )

    mentioned_count = sum(1 for r in results_list if r.brand_mentioned)
    mention_rate = mentioned_count / total_runs if total_runs else 0.0

    top_rec_count = sum(1 for r in results_list if r.is_top_recommendation)
    top_rec_rate = top_rec_count / total_runs if total_runs else 0.0

    engine_counts: dict[str, dict[str, int]] = {}
    for r in results_list:
        if r.engine not in engine_counts:
            engine_counts[r.engine] = {"total": 0, "mentioned": 0}
        engine_counts[r.engine]["total"] += 1
        if r.brand_mentioned:
            engine_counts[r.engine]["mentioned"] += 1

    engine_breakdown = {
        eng: counts["mentioned"] / counts["total"] if counts["total"] else 0.0
        for eng, counts in engine_counts.items()
    }

    sentiment_counts = SentimentBreakdown()
    for r in results_list:
        if r.sentiment == "positive":
            sentiment_counts.positive += 1
        elif r.sentiment == "neutral":
            sentiment_counts.neutral += 1
        elif r.sentiment == "negative":
            sentiment_counts.negative += 1
        elif r.sentiment == "mixed":
            sentiment_counts.mixed += 1

    date_groups: dict[str, dict[str, int]] = {}
    for r in results_list:
        date_key = r.run_date.isoformat()
        if date_key not in date_groups:
            date_groups[date_key] = {"total": 0, "mentioned": 0}
        date_groups[date_key]["total"] += 1
        if r.brand_mentioned:
            date_groups[date_key]["mentioned"] += 1

    mention_rate_trend = sorted(
        [
            MentionRateTrend(
                date=d,
                rate=counts["mentioned"] / counts["total"] if counts["total"] else 0.0,
            )
            for d, counts in date_groups.items()
        ],
        key=lambda x: x.date,
    )

    query_count_result = await db.execute(
        select(func.count())
        .select_from(MonitoredQuery)
        .where(MonitoredQuery.brand_id == brand_id)
    )
    total_queries = query_count_result.scalar() or 0

    return OverviewResponse(
        mention_rate=round(mention_rate, 4),
        mention_rate_trend=mention_rate_trend,
        engine_breakdown=engine_breakdown,
        sentiment_breakdown=sentiment_counts,
        top_rec_rate=round(top_rec_rate, 4),
        total_queries=total_queries,
        total_runs=total_runs,
    )


@router.get("/queries/{query_id}/history", response_model=list[ResultResponse])
async def get_query_history(
    query_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ResultResponse]:
    query_check = await db.execute(
        select(MonitoredQuery)
        .join(Brand, MonitoredQuery.brand_id == Brand.id)
        .where(MonitoredQuery.id == query_id, Brand.user_id == current_user.id)
    )
    if not query_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Query not found"
        )

    results = await db.execute(
        select(QueryResult)
        .where(QueryResult.query_id == query_id)
        .order_by(QueryResult.run_date.desc(), QueryResult.engine)
    )
    items = results.scalars().all()
    return [ResultResponse.model_validate(r) for r in items]


@router.get(
    "/brands/{brand_id}/competitors/comparison",
    response_model=CompetitorComparisonResponse,
)
async def get_competitor_comparison(
    brand_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CompetitorComparisonResponse:
    brand_result = await db.execute(
        select(Brand).where(Brand.id == brand_id, Brand.user_id == current_user.id)
    )
    brand = brand_result.scalar_one_or_none()
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found"
        )

    all_results_query = (
        select(QueryResult)
        .join(MonitoredQuery, QueryResult.query_id == MonitoredQuery.id)
        .where(MonitoredQuery.brand_id == brand_id)
    )
    all_results = await db.execute(all_results_query)
    results_list = all_results.scalars().all()

    total_runs = len(results_list)
    brand_mentioned = sum(1 for r in results_list if r.brand_mentioned)
    brand_mention_rate = brand_mentioned / total_runs if total_runs else 0.0

    brand_sentiment = SentimentBreakdown()
    for r in results_list:
        if r.brand_mentioned:
            if r.sentiment == "positive":
                brand_sentiment.positive += 1
            elif r.sentiment == "neutral":
                brand_sentiment.neutral += 1
            elif r.sentiment == "negative":
                brand_sentiment.negative += 1
            elif r.sentiment == "mixed":
                brand_sentiment.mixed += 1

    brand_entry = CompetitorComparisonEntry(
        name=brand.name,
        mention_rate=round(brand_mention_rate, 4),
        sentiment_breakdown=brand_sentiment,
    )

    comp_result = await db.execute(
        select(Competitor).where(Competitor.brand_id == brand_id)
    )
    competitors = comp_result.scalars().all()

    competitor_entries: list[CompetitorComparisonEntry] = []
    for comp in competitors:
        comp_names = [comp.name.lower()] + [a.lower() for a in (comp.aliases or [])]
        comp_mention_count = 0
        comp_sentiment = SentimentBreakdown()

        for r in results_list:
            if r.competitor_mentions:
                for comp_name_key, comp_data in r.competitor_mentions.items():
                    if comp_name_key.lower() in comp_names:
                        is_mentioned = comp_data if isinstance(comp_data, bool) else comp_data.get("mentioned", False)
                        if is_mentioned:
                            comp_mention_count += 1
                            sent = comp_data.get("sentiment", "neutral") if isinstance(comp_data, dict) else "neutral"
                            if sent == "positive":
                                comp_sentiment.positive += 1
                            elif sent == "neutral":
                                comp_sentiment.neutral += 1
                            elif sent == "negative":
                                comp_sentiment.negative += 1
                            elif sent == "mixed":
                                comp_sentiment.mixed += 1
                        break

        comp_rate = comp_mention_count / total_runs if total_runs else 0.0
        competitor_entries.append(
            CompetitorComparisonEntry(
                name=comp.name,
                mention_rate=round(comp_rate, 4),
                sentiment_breakdown=comp_sentiment,
            )
        )

    # Build query_winners: per-query, per-engine top recommendation winner
    query_map: dict[UUID, str] = {}
    queries_result = await db.execute(
        select(MonitoredQuery).where(MonitoredQuery.brand_id == brand_id)
    )
    for q in queries_result.scalars().all():
        query_map[q.id] = q.query_text

    # Group results by (query_id, engine) and find the latest result per group
    latest_results: dict[tuple[UUID, str], QueryResult] = {}
    for r in results_list:
        key = (r.query_id, r.engine)
        if key not in latest_results or r.run_date > latest_results[key].run_date:
            latest_results[key] = r

    # For each query, determine the winner per engine
    query_winners_map: dict[UUID, dict[str, str | None]] = {}
    comp_names_lookup = {
        comp.name.lower(): comp.name for comp in competitors
    }
    for comp in competitors:
        for alias in (comp.aliases or []):
            comp_names_lookup[alias.lower()] = comp.name

    for (qid, eng), r in latest_results.items():
        if qid not in query_winners_map:
            query_winners_map[qid] = {}
        winner: str | None = None
        if r.is_top_recommendation:
            winner = brand.name
        elif r.competitor_mentions:
            for comp_key, comp_data in r.competitor_mentions.items():
                is_top = False
                if isinstance(comp_data, dict):
                    is_top = comp_data.get("is_top_recommendation", False)
                if is_top:
                    winner = comp_names_lookup.get(comp_key.lower(), comp_key)
                    break
        query_winners_map[qid][eng] = winner

    query_winners = [
        QueryWinner(query_text=query_map[qid], winners=winners)
        for qid, winners in query_winners_map.items()
        if qid in query_map
    ]

    return CompetitorComparisonResponse(
        brand=brand_entry,
        competitors=competitor_entries,
        query_winners=query_winners,
    )
