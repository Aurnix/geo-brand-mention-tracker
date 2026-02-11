from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSON, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class QueryResult(Base):
    __tablename__ = "query_results"

    __table_args__ = (
        Index("ix_query_results_query_engine_date", "query_id", "engine", "run_date"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    query_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("monitored_queries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    engine: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_response: Mapped[str] = mapped_column(Text, nullable=False)
    brand_mentioned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mention_position: Mapped[str] = mapped_column(
        String(20), nullable=False, default="not_mentioned"
    )
    is_top_recommendation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    sentiment: Mapped[str] = mapped_column(
        String(20), nullable=False, default="neutral"
    )
    competitor_mentions: Mapped[dict | None] = mapped_column(JSON, default=dict)
    citations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    run_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    query: Mapped["MonitoredQuery"] = relationship(
        "MonitoredQuery", back_populates="query_results"
    )

    def __repr__(self) -> str:
        return f"<QueryResult id={self.id} engine={self.engine} date={self.run_date}>"


# Resolve forward references at module level
from app.models.query import MonitoredQuery  # noqa: E402, F401
