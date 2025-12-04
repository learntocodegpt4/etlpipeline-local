"""Scheduler for automated ETL runs using APScheduler."""

from collections.abc import Callable
from datetime import datetime
from typing import Any

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config.settings import get_settings

logger = structlog.get_logger(__name__)


class ETLScheduler:
    """Scheduler for automated ETL pipeline runs.

    Uses APScheduler with cron-based scheduling for periodic
    ETL execution.
    """

    def __init__(self):
        self.settings = get_settings()
        self._scheduler = AsyncIOScheduler(timezone=self.settings.scheduler_timezone)
        self._logger = logger.bind(component="etl_scheduler")
        self._jobs: dict[str, Any] = {}

    def add_job(
        self,
        job_id: str,
        func: Callable[..., Any],
        cron_expression: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Add a scheduled job.

        Args:
            job_id: Unique identifier for the job
            func: Async function to execute
            cron_expression: Cron expression (defaults to settings)
            **kwargs: Additional arguments passed to the job function
        """
        cron = cron_expression or self.settings.scheduler_cron_expression

        # Parse cron expression
        parts = cron.split()
        if len(parts) == 5:
            minute, hour, day, month, day_of_week = parts
        else:
            self._logger.warning(
                "invalid_cron_expression",
                expression=cron,
                default="0 2 * * *",
            )
            minute, hour, day, month, day_of_week = "0", "2", "*", "*", "*"

        trigger = CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            timezone=self.settings.scheduler_timezone,
        )

        job = self._scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            kwargs=kwargs,
            replace_existing=True,
        )

        self._jobs[job_id] = job

        self._logger.info(
            "job_added",
            job_id=job_id,
            cron=cron,
            timezone=self.settings.scheduler_timezone,
            next_run=job.next_run_time.isoformat() if job.next_run_time else None,
        )

    def add_immediate_job(
        self,
        job_id: str,
        func: Callable[..., Any],
        **kwargs: Any,
    ) -> None:
        """Add a job to run immediately.

        Args:
            job_id: Unique identifier for the job
            func: Async function to execute
            **kwargs: Arguments passed to the job function
        """
        job = self._scheduler.add_job(
            func,
            trigger="date",
            run_date=datetime.now(),
            id=job_id,
            kwargs=kwargs,
        )

        self._jobs[job_id] = job

        self._logger.info(
            "immediate_job_added",
            job_id=job_id,
        )

    def remove_job(self, job_id: str) -> None:
        """Remove a scheduled job.

        Args:
            job_id: Job identifier to remove
        """
        if job_id in self._jobs:
            self._scheduler.remove_job(job_id)
            del self._jobs[job_id]
            self._logger.info("job_removed", job_id=job_id)

    def get_jobs(self) -> list[dict[str, Any]]:
        """Get list of scheduled jobs.

        Returns:
            List of job information dictionaries
        """
        jobs = []
        for job in self._scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
            })
        return jobs

    def start(self) -> None:
        """Start the scheduler."""
        if not self.settings.scheduler_enabled:
            self._logger.info("scheduler_disabled")
            return

        self._scheduler.start()
        self._logger.info(
            "scheduler_started",
            timezone=self.settings.scheduler_timezone,
        )

    def stop(self) -> None:
        """Stop the scheduler."""
        self._scheduler.shutdown()
        self._logger.info("scheduler_stopped")

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._scheduler.running
