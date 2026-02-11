from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.brand import Brand
from app.models.query import MonitoredQuery
from app.models.user import User
from app.schemas.query import QueryCreate, QueryResponse, QueryUpdate
from app.services.plan_limits import check_query_limit

router = APIRouter()


async def _verify_brand_ownership(
    brand_id: UUID, user: User, db: AsyncSession
) -> Brand:
    result = await db.execute(
        select(Brand).where(Brand.id == brand_id, Brand.user_id == user.id)
    )
    brand = result.scalar_one_or_none()
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found"
        )
    return brand


@router.post(
    "/brands/{brand_id}/queries",
    response_model=QueryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_query(
    brand_id: UUID,
    body: QueryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QueryResponse:
    await _verify_brand_ownership(brand_id, current_user, db)

    count_result = await db.execute(
        select(func.count())
        .select_from(MonitoredQuery)
        .where(MonitoredQuery.brand_id == brand_id)
    )
    current_count = count_result.scalar() or 0

    if not check_query_limit(current_count, current_user.plan_tier.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Query limit reached for {current_user.plan_tier.value} plan.",
        )

    query = MonitoredQuery(
        brand_id=brand_id,
        query_text=body.query_text,
        category=body.category,
    )
    db.add(query)
    await db.flush()
    await db.refresh(query)
    return QueryResponse.model_validate(query)


@router.get("/brands/{brand_id}/queries", response_model=list[QueryResponse])
async def list_queries(
    brand_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[QueryResponse]:
    await _verify_brand_ownership(brand_id, current_user, db)

    result = await db.execute(
        select(MonitoredQuery)
        .where(MonitoredQuery.brand_id == brand_id)
        .order_by(MonitoredQuery.created_at.desc())
    )
    queries = result.scalars().all()
    return [QueryResponse.model_validate(q) for q in queries]


@router.get("/queries/{query_id}", response_model=QueryResponse)
async def get_query(
    query_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QueryResponse:
    result = await db.execute(
        select(MonitoredQuery)
        .join(Brand, MonitoredQuery.brand_id == Brand.id)
        .where(MonitoredQuery.id == query_id, Brand.user_id == current_user.id)
    )
    query = result.scalar_one_or_none()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Query not found"
        )
    return QueryResponse.model_validate(query)


@router.patch("/queries/{query_id}", response_model=QueryResponse)
async def update_query(
    query_id: UUID,
    body: QueryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QueryResponse:
    result = await db.execute(
        select(MonitoredQuery)
        .join(Brand, MonitoredQuery.brand_id == Brand.id)
        .where(MonitoredQuery.id == query_id, Brand.user_id == current_user.id)
    )
    query = result.scalar_one_or_none()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Query not found"
        )

    if body.query_text is not None:
        query.query_text = body.query_text
    if body.category is not None:
        query.category = body.category
    if body.is_active is not None:
        query.is_active = body.is_active

    await db.flush()
    await db.refresh(query)
    return QueryResponse.model_validate(query)


@router.delete("/queries/{query_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_query(
    query_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    result = await db.execute(
        select(MonitoredQuery)
        .join(Brand, MonitoredQuery.brand_id == Brand.id)
        .where(MonitoredQuery.id == query_id, Brand.user_id == current_user.id)
    )
    query = result.scalar_one_or_none()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Query not found"
        )
    await db.delete(query)
    await db.flush()
