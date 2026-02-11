import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import async_session_factory
from app.models.brand import Brand
from app.models.user import User
from app.services.plan_limits import get_allowed_engines, get_plan_limits
from app.services.query_runner import QueryRunner

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def daily_run() -> None:
    """Run all active queries for all brands.

    Creates a fresh database session, iterates over every brand whose
    owning user has an active plan, determines allowed engines based on
    plan tier, and delegates execution to QueryRunner.
    """
    logger.info("Scheduled daily run starting.")
    total_brands = 0
    total_success = 0
    total_failed = 0

    async with async_session_factory() as session:
        try:
            # Fetch all brands with their user eagerly loaded
            stmt = (
                select(Brand)
                .options(selectinload(Brand.user))
                .options(selectinload(Brand.monitored_queries))
            )
            result = await session.execute(stmt)
            brands = result.scalars().all()

            runner = QueryRunner(db=session)

            for brand in brands:
                user: User = brand.user
                plan_tier = user.plan_tier.value if hasattr(user.plan_tier, "value") else str(user.plan_tier)

                # Determine frequency: free-tier users only run weekly (Monday)
                plan = get_plan_limits(plan_tier)
                if plan["frequency"] == "weekly":
                    from datetime import date
                    if date.today().weekday() != 0:  # 0 = Monday
                        logger.info(
                            "Skipping brand '%s' (user=%s, plan=%s): "
                            "weekly plan, today is not Monday.",
                            brand.name,
                            user.email,
                            plan_tier,
                        )
                        continue

                # Check if brand has any active queries
                active_queries = [
                    q for q in brand.monitored_queries if q.is_active
                ]
                if not active_queries:
                    logger.info(
                        "Skipping brand '%s': no active queries.", brand.name
                    )
                    continue

                engines = get_allowed_engines(plan_tier)
                total_brands += 1

                logger.info(
                    "Running brand '%s' (user=%s, plan=%s) with engines: %s",
                    brand.name,
                    user.email,
                    plan_tier,
                    engines,
                )

                try:
                    stats = await runner.run_brand(brand, engines)
                    total_success += stats["success"]
                    total_failed += stats["failed"]
                except Exception:
                    logger.exception(
                        "Unhandled error running brand '%s'.", brand.name
                    )
                    total_failed += 1

            await session.commit()

        except Exception:
            logger.exception("Fatal error during daily run.")
            await session.rollback()

    logger.info(
        "Scheduled daily run complete. Brands processed: %d, "
        "Successful queries: %d, Failed queries: %d",
        total_brands,
        total_success,
        total_failed,
    )


def init_scheduler() -> None:
    """Initialize and start the APScheduler with the daily query run job."""
    settings = get_settings()
    scheduler.add_job(
        daily_run,
        "cron",
        hour=settings.RUN_SCHEDULE_HOUR,
        minute=settings.RUN_SCHEDULE_MINUTE,
        id="daily_query_run",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Scheduler started. Daily run scheduled at %02d:%02d UTC.",
        settings.RUN_SCHEDULE_HOUR,
        settings.RUN_SCHEDULE_MINUTE,
    )
