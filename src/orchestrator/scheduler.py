"""Job scheduler using APScheduler"""

from datetime import datetime
from typing import Callable, Optional
import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from src.config.settings import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class Scheduler:
    """Job scheduler for ETL pipeline"""

    def __init__(self, run_job_func: Optional[Callable] = None):
        self.settings = get_settings()
        self._scheduler = AsyncIOScheduler()
        self._run_job_func = run_job_func
        self._is_running = False

    def set_job_function(self, func: Callable) -> None:
        """Set the function to run for scheduled jobs"""
        self._run_job_func = func

    def add_cron_job(
        self,
        cron_expression: Optional[str] = None,
        job_id: str = "etl_scheduled_job",
    ) -> None:
        """Add a cron-scheduled job"""
        if not self._run_job_func:
            raise ValueError("Job function not set. Call set_job_function first.")

        cron_expr = cron_expression or self.settings.etl_cron_expression
        parts = cron_expr.split()

        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_expr}")

        trigger = CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
        )

        self._scheduler.add_job(
            self._run_job_func,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            name="ETL Pipeline Scheduled Job",
        )

        logger.info(
            "cron_job_added",
            job_id=job_id,
            cron_expression=cron_expr,
        )

    def add_one_time_job(
        self,
        run_at: datetime,
        job_id: str = "etl_one_time_job",
    ) -> None:
        """Add a one-time scheduled job"""
        if not self._run_job_func:
            raise ValueError("Job function not set. Call set_job_function first.")

        trigger = DateTrigger(run_date=run_at)

        self._scheduler.add_job(
            self._run_job_func,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            name="ETL Pipeline One-Time Job",
        )

        logger.info(
            "one_time_job_added",
            job_id=job_id,
            run_at=run_at.isoformat(),
        )

    def remove_job(self, job_id: str) -> None:
        """Remove a scheduled job"""
        try:
            self._scheduler.remove_job(job_id)
            logger.info("job_removed", job_id=job_id)
        except Exception as e:
            logger.warning("job_remove_failed", job_id=job_id, error=str(e))

    def get_jobs(self) -> list:
        """Get all scheduled jobs"""
        return self._scheduler.get_jobs()

    def start(self) -> None:
        """Start the scheduler"""
        if self._is_running:
            logger.warning("scheduler_already_running")
            return

        self._scheduler.start()
        self._is_running = True
        logger.info("scheduler_started")

    def stop(self) -> None:
        """Stop the scheduler"""
        if not self._is_running:
            return

        self._scheduler.shutdown(wait=False)
        self._is_running = False
        logger.info("scheduler_stopped")

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self._is_running

    async def trigger_job_now(self) -> None:
        """Trigger the job immediately"""
        if not self._run_job_func:
            raise ValueError("Job function not set")

        logger.info("triggering_job_manually")
        await self._run_job_func()
