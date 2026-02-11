from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BrandCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    aliases: list[str] = Field(default_factory=list)


class BrandUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    aliases: list[str] | None = None


class BrandResponse(BaseModel):
    id: UUID
    name: str
    aliases: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class CompetitorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    aliases: list[str] = Field(default_factory=list)


class CompetitorResponse(BaseModel):
    id: UUID
    brand_id: UUID
    name: str
    aliases: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}
