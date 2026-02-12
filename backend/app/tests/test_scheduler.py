"""Tests for the scheduler service.

Tests init_scheduler setup and daily_run logic including
plan-tier frequency gating and brand iteration.
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.scheduler import daily_run, init_scheduler


class TestInitScheduler:
    def test_init_scheduler_starts_without_error(self):
        """init_scheduler should configure and start the scheduler."""
        with patch("app.services.scheduler.scheduler") as mock_scheduler:
            init_scheduler()
            mock_scheduler.add_job.assert_called_once()
            mock_scheduler.start.assert_called_once()

            # Verify the job is configured as a cron trigger
            call_kwargs = mock_scheduler.add_job.call_args
            assert call_kwargs[1]["id"] == "daily_query_run"
            assert call_kwargs[0][1] == "cron"


class TestDailyRun:
    @patch("app.services.scheduler.async_session_factory")
    @patch("app.services.scheduler.QueryRunner")
    async def test_daily_run_processes_brands(
        self, mock_runner_cls, mock_session_factory
    ):
        """daily_run should iterate over brands and call run_brand."""
        mock_brand = MagicMock()
        mock_brand.name = "TestBrand"
        mock_brand.monitored_queries = [
            MagicMock(is_active=True),
        ]

        mock_user = MagicMock()
        mock_user.plan_tier = MagicMock(value="pro")
        mock_user.email = "test@example.com"
        mock_brand.user = mock_user

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_brand]
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        # Setup context manager
        mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_runner = AsyncMock()
        mock_runner.run_brand.return_value = {"total": 4, "success": 4, "failed": 0, "skipped": 0}
        mock_runner_cls.return_value = mock_runner

        await daily_run()

        mock_runner.run_brand.assert_called_once()

    @patch("app.services.scheduler.async_session_factory")
    async def test_daily_run_skips_brands_with_no_active_queries(
        self, mock_session_factory
    ):
        """daily_run should skip brands that have no active queries."""
        mock_brand = MagicMock()
        mock_brand.name = "EmptyBrand"
        mock_brand.monitored_queries = []

        mock_user = MagicMock()
        mock_user.plan_tier = MagicMock(value="pro")
        mock_user.email = "empty@example.com"
        mock_brand.user = mock_user

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_brand]
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        # Should not raise, should just skip
        await daily_run()

    @patch("app.services.scheduler.async_session_factory")
    @patch("app.services.scheduler.QueryRunner")
    async def test_daily_run_free_tier_weekly_skip(
        self, mock_runner_cls, mock_session_factory
    ):
        """Free-tier brands should only run on Mondays; runner not called on non-Monday."""
        from datetime import date as real_date

        mock_brand = MagicMock()
        mock_brand.name = "FreeBrand"
        mock_brand.monitored_queries = [MagicMock(is_active=True)]

        mock_user = MagicMock()
        mock_user.plan_tier = MagicMock(value="free")
        mock_user.email = "free@example.com"
        mock_brand.user = mock_user

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_brand]
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_runner = AsyncMock()
        mock_runner_cls.return_value = mock_runner

        # The free-tier check does `from datetime import date; date.today().weekday()`.
        # We patch `datetime.date` at the module level to control the weekday.
        class FakeDate(real_date):
            @classmethod
            def today(cls):
                # Return a Wednesday (weekday=2), not Monday (weekday=0)
                return real_date(2026, 2, 11)  # Feb 11, 2026 is a Wednesday

        with patch("datetime.date", FakeDate):
            await daily_run()

        # On a non-Monday, the free-tier brand should be skipped
        mock_runner.run_brand.assert_not_called()
