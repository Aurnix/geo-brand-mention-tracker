"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-02-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID

# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create plan_tier_enum type
    plan_tier_enum = sa.Enum("free", "pro", "agency", name="plan_tier_enum")
    plan_tier_enum.create(op.get_bind(), checkfirst=True)

    # Users table
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column("plan_tier", plan_tier_enum, server_default="free", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # Brands table
    op.create_table(
        "brands",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("aliases", JSON, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_brands_user_id", "brands", ["user_id"])

    # Competitors table
    op.create_table(
        "competitors",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("aliases", JSON, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_competitors_brand_id", "competitors", ["brand_id"])

    # Monitored queries table
    op.create_table(
        "monitored_queries",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), nullable=False),
        sa.Column("query_text", sa.String(1000), nullable=False),
        sa.Column("category", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_monitored_queries_brand_id", "monitored_queries", ["brand_id"])

    # Query results table
    op.create_table(
        "query_results",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("query_id", UUID(as_uuid=True), nullable=False),
        sa.Column("engine", sa.String(50), nullable=False),
        sa.Column("model_version", sa.String(100), nullable=False),
        sa.Column("raw_response", sa.Text, nullable=False),
        sa.Column("brand_mentioned", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("mention_position", sa.String(20), nullable=False, server_default="not_mentioned"),
        sa.Column("is_top_recommendation", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("sentiment", sa.String(20), nullable=False, server_default="neutral"),
        sa.Column("competitor_mentions", JSON, nullable=True),
        sa.Column("citations", JSON, nullable=True),
        sa.Column("run_date", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["query_id"], ["monitored_queries.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_query_results_query_id", "query_results", ["query_id"])
    op.create_index("ix_query_results_query_engine_date", "query_results", ["query_id", "engine", "run_date"])


def downgrade() -> None:
    op.drop_table("query_results")
    op.drop_table("monitored_queries")
    op.drop_table("competitors")
    op.drop_table("brands")
    op.drop_table("users")
    sa.Enum(name="plan_tier_enum").drop(op.get_bind(), checkfirst=True)
