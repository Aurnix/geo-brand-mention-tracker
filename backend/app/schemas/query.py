from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class QueryCreate(BaseModel):
    query_text: str = Field(..., min_length=1, max_length=1000)
    category: str | None = None
    is_active: bool = True


class QueryUpdate(BaseModel):
    query_text: str | None = Field(None, min_length=1, max_length=1000)
    category: str | None = None
    is_active: bool | None = None


class QueryResponse(BaseModel):
    id: UUID
    brand_id: UUID
    query_text: str
    category: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
