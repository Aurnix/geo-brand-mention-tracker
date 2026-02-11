from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import JSON, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    aliases: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="brands")
    competitors: Mapped[list["Competitor"]] = relationship(
        "Competitor", back_populates="brand", cascade="all, delete-orphan"
    )
    monitored_queries: Mapped[list["MonitoredQuery"]] = relationship(
        "MonitoredQuery", back_populates="brand", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Brand id={self.id} name={self.name}>"


class Competitor(Base):
    __tablename__ = "competitors"

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
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    aliases: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    brand: Mapped["Brand"] = relationship("Brand", back_populates="competitors")

    def __repr__(self) -> str:
        return f"<Competitor id={self.id} name={self.name}>"


# Resolve forward references at module level
from app.models.query import MonitoredQuery  # noqa: E402, F401
from app.models.user import User  # noqa: E402, F401
