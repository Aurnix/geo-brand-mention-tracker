from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class ResultResponse(BaseModel):
    id: UUID
    query_id: UUID
    engine: str
    model_version: str
    raw_response: str
    brand_mentioned: bool
    mention_position: str
    is_top_recommendation: bool
    sentiment: str
    competitor_mentions: dict | None
    citations: list | None
    run_date: date
    created_at: datetime

    model_config = {"from_attributes": True}


class MentionRateTrend(BaseModel):
    date: date
    rate: float


class SentimentBreakdown(BaseModel):
    positive: int = 0
    neutral: int = 0
    negative: int = 0
    mixed: int = 0


class OverviewResponse(BaseModel):
    mention_rate: float
    mention_rate_trend: list[MentionRateTrend]
    engine_breakdown: dict[str, float]
    sentiment_breakdown: SentimentBreakdown
    top_rec_rate: float
    total_queries: int
    total_runs: int


class CompetitorComparisonEntry(BaseModel):
    name: str
    mention_rate: float
    sentiment_breakdown: SentimentBreakdown


class QueryWinner(BaseModel):
    query_text: str
    winners: dict[str, str | None]


class CompetitorComparisonResponse(BaseModel):
    brand: CompetitorComparisonEntry
    competitors: list[CompetitorComparisonEntry]
    query_winners: list[QueryWinner] = []


class PaginatedResults(BaseModel):
    items: list[ResultResponse]
    total: int
    page: int
    page_size: int
    pages: int
