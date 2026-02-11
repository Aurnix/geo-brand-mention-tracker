import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db, async_session_factory
from app.models.brand import Brand, Competitor
from app.models.query import MonitoredQuery
from app.models.user import User
from app.schemas.brand import (
    BrandCreate,
    BrandResponse,
    BrandUpdate,
    CompetitorCreate,
    CompetitorResponse,
)
from app.services.plan_limits import (
    check_brand_limit,
    check_competitor_limit,
    get_allowed_engines,
)

logger = logging.getLogger(__name__)
router = APIRouter()


async def _get_user_brand(
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


@router.post("/", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
async def create_brand(
    body: BrandCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BrandResponse:
    count_result = await db.execute(
        select(func.count()).select_from(Brand).where(Brand.user_id == current_user.id)
    )
    current_count = count_result.scalar() or 0

    if not check_brand_limit(current_count, current_user.plan_tier.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Brand limit reached for {current_user.plan_tier.value} plan. Upgrade to add more brands.",
        )

    brand = Brand(
        user_id=current_user.id,
        name=body.name,
        aliases=body.aliases,
    )
    db.add(brand)
    await db.flush()
    await db.refresh(brand)
    return BrandResponse.model_validate(brand)


@router.get("/", response_model=list[BrandResponse])
async def list_brands(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BrandResponse]:
    result = await db.execute(
        select(Brand)
        .where(Brand.user_id == current_user.id)
        .order_by(Brand.created_at.desc())
    )
    brands = result.scalars().all()
    return [BrandResponse.model_validate(b) for b in brands]


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand(
    brand_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BrandResponse:
    brand = await _get_user_brand(brand_id, current_user, db)
    return BrandResponse.model_validate(brand)


@router.put("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: UUID,
    body: BrandUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BrandResponse:
    brand = await _get_user_brand(brand_id, current_user, db)

    if body.name is not None:
        brand.name = body.name
    if body.aliases is not None:
        brand.aliases = body.aliases

    await db.flush()
    await db.refresh(brand)
    return BrandResponse.model_validate(brand)


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand(
    brand_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    brand = await _get_user_brand(brand_id, current_user, db)
    await db.delete(brand)
    await db.flush()


# ---------- Manual Run Trigger ----------


async def _run_brand_queries(brand_id: UUID, plan_tier: str) -> None:
    """Background task to run all queries for a brand."""
    from app.services.query_runner import QueryRunner

    async with async_session_factory() as db:
        try:
            result = await db.execute(select(Brand).where(Brand.id == brand_id))
            brand = result.scalar_one_or_none()
            if not brand:
                logger.error(f"Brand {brand_id} not found for manual run")
                return

            engines = get_allowed_engines(plan_tier)
            runner = QueryRunner(db)
            stats = await runner.run_brand(brand, engines)
            await db.commit()
            logger.info(f"Manual run completed for brand {brand_id}: {stats}")
        except Exception:
            logger.exception(f"Manual run failed for brand {brand_id}")
            await db.rollback()


@router.post("/{brand_id}/run")
async def trigger_run(
    brand_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    brand = await _get_user_brand(brand_id, current_user, db)
    background_tasks.add_task(
        _run_brand_queries, brand.id, current_user.plan_tier.value
    )
    return {"status": "started", "message": "Query run triggered for all active queries"}


# ---------- Competitors ----------


@router.post(
    "/{brand_id}/competitors",
    response_model=CompetitorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_competitor(
    brand_id: UUID,
    body: CompetitorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CompetitorResponse:
    brand = await _get_user_brand(brand_id, current_user, db)

    count_result = await db.execute(
        select(func.count())
        .select_from(Competitor)
        .where(Competitor.brand_id == brand_id)
    )
    current_count = count_result.scalar() or 0

    if not check_competitor_limit(current_count, current_user.plan_tier.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Competitor limit reached for {current_user.plan_tier.value} plan.",
        )

    competitor = Competitor(
        brand_id=brand.id,
        name=body.name,
        aliases=body.aliases,
    )
    db.add(competitor)
    await db.flush()
    await db.refresh(competitor)
    return CompetitorResponse.model_validate(competitor)


@router.get("/{brand_id}/competitors", response_model=list[CompetitorResponse])
async def list_competitors(
    brand_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CompetitorResponse]:
    await _get_user_brand(brand_id, current_user, db)

    result = await db.execute(
        select(Competitor)
        .where(Competitor.brand_id == brand_id)
        .order_by(Competitor.created_at.desc())
    )
    competitors = result.scalars().all()
    return [CompetitorResponse.model_validate(c) for c in competitors]


@router.delete(
    "/{brand_id}/competitors/{competitor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_competitor(
    brand_id: UUID,
    competitor_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await _get_user_brand(brand_id, current_user, db)

    result = await db.execute(
        select(Competitor).where(
            Competitor.id == competitor_id, Competitor.brand_id == brand_id
        )
    )
    competitor = result.scalar_one_or_none()
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found"
        )
    await db.delete(competitor)
    await db.flush()
