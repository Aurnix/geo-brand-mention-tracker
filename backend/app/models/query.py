from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MonitoredQuery(Base):
    __tablename__ = "monitored_queries"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    brand_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    query_text: Mapped[str] = mapped_column(String(1000), nullable=False)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    brand: Mapped["Brand"] = relationship("Brand", back_populates="monitored_queries")
    query_results: Mapped[list["QueryResult"]] = relationship(
        "QueryResult", back_populates="query", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MonitoredQuery id={self.id} text={self.query_text[:50]}>"


# Resolve forward references at module level
from app.models.brand import Brand  # noqa: E402, F401
from app.models.result import QueryResult  # noqa: E402, F401
