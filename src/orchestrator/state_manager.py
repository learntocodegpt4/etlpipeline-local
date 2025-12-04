"""State management for ETL jobs using SQLite."""

import json
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from src.config.settings import get_settings

logger = structlog.get_logger(__name__)


class StateManager:
    """Manages ETL job state using SQLite.

    Provides local state persistence for:
    - Job tracking
    - Job details/logs
    - Execution history
    """

    def __init__(self, db_path: str | None = None):
        self.settings = get_settings()
        self.db_path = db_path or self.settings.sqlite_database_path
        self._logger = logger.bind(component="state_manager")
        self._init_database()

    def _init_database(self) -> None:
        """Initialize the SQLite database schema."""
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS etl_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT UNIQUE NOT NULL,
                    pipeline_name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    started_at TEXT,
                    completed_at TEXT,
                    total_records INTEGER DEFAULT 0,
                    error_message TEXT,
                    parameters TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS etl_job_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    step_name TEXT NOT NULL,
                    step_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    records_processed INTEGER DEFAULT 0,
                    error_message TEXT,
                    error_details TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES etl_jobs(job_id)
                );

                CREATE INDEX IF NOT EXISTS idx_jobs_job_id ON etl_jobs(job_id);
                CREATE INDEX IF NOT EXISTS idx_jobs_status ON etl_jobs(status);
                CREATE INDEX IF NOT EXISTS idx_job_details_job_id ON etl_job_details(job_id);
            """)

        self._logger.info("database_initialized", path=self.db_path)

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    async def create_job(
        self,
        job_id: str,
        pipeline_name: str,
        parameters: dict[str, Any] | None = None,
    ) -> None:
        """Create a new job record.

        Args:
            job_id: Unique job identifier
            pipeline_name: Name of the pipeline
            parameters: Optional job parameters
        """
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO etl_jobs (job_id, pipeline_name, status, started_at, parameters)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    pipeline_name,
                    "running",
                    datetime.now().isoformat(),
                    json.dumps(parameters) if parameters else None,
                ),
            )

        self._logger.info(
            "job_created",
            job_id=job_id,
            pipeline_name=pipeline_name,
        )

    async def update_job(
        self,
        job_id: str,
        status: str | None = None,
        completed_at: datetime | None = None,
        total_records: int | None = None,
        error_message: str | None = None,
    ) -> None:
        """Update a job record.

        Args:
            job_id: Job identifier
            status: New status
            completed_at: Completion time
            total_records: Total records processed
            error_message: Error message if failed
        """
        updates = []
        params: list[Any] = []

        if status is not None:
            updates.append("status = ?")
            params.append(status)

        if completed_at is not None:
            updates.append("completed_at = ?")
            params.append(completed_at.isoformat())

        if total_records is not None:
            updates.append("total_records = ?")
            params.append(total_records)

        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)

        if not updates:
            return

        params.append(job_id)

        with self._get_connection() as conn:
            conn.execute(
                f"UPDATE etl_jobs SET {', '.join(updates)} WHERE job_id = ?",
                params,
            )

        self._logger.info(
            "job_updated",
            job_id=job_id,
            status=status,
        )

    async def add_job_detail(
        self,
        job_id: str,
        step_name: str,
        step_type: str,
        status: str,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        records_processed: int = 0,
        error_message: str | None = None,
        error_details: dict[str, Any] | None = None,
    ) -> None:
        """Add a job detail record.

        Args:
            job_id: Job identifier
            step_name: Name of the step
            step_type: Type of step (extract, transform, load)
            status: Step status
            started_at: Step start time
            completed_at: Step completion time
            records_processed: Number of records processed
            error_message: Error message if failed
            error_details: Additional error details
        """
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO etl_job_details (
                    job_id, step_name, step_type, status, started_at,
                    completed_at, records_processed, error_message, error_details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    step_name,
                    step_type,
                    status,
                    started_at.isoformat() if started_at else None,
                    completed_at.isoformat() if completed_at else None,
                    records_processed,
                    error_message,
                    json.dumps(error_details) if error_details else None,
                ),
            )

    async def get_job(self, job_id: str) -> dict[str, Any] | None:
        """Get a job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job record or None
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM etl_jobs WHERE job_id = ?",
                (job_id,),
            )
            row = cursor.fetchone()

        if row:
            return dict(row)
        return None

    async def get_job_details(self, job_id: str) -> list[dict[str, Any]]:
        """Get job details/logs.

        Args:
            job_id: Job identifier

        Returns:
            List of job detail records
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM etl_job_details WHERE job_id = ? ORDER BY created_at",
                (job_id,),
            )
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    async def get_jobs(
        self,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get jobs with optional filtering.

        Args:
            status: Optional status filter
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of job records
        """
        query = "SELECT * FROM etl_jobs"
        params: list[Any] = []

        if status:
            query += " WHERE status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    async def get_job_stats(self) -> dict[str, Any]:
        """Get job statistics.

        Returns:
            Dictionary with job statistics
        """
        with self._get_connection() as conn:
            # Total counts by status
            cursor = conn.execute(
                """
                SELECT status, COUNT(*) as count
                FROM etl_jobs
                GROUP BY status
                """
            )
            status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}

            # Recent job count
            cursor = conn.execute(
                """
                SELECT COUNT(*) as count
                FROM etl_jobs
                WHERE created_at > datetime('now', '-24 hours')
                """
            )
            recent_count = cursor.fetchone()["count"]

            # Average duration for successful jobs
            cursor = conn.execute(
                """
                SELECT AVG(
                    (julianday(completed_at) - julianday(started_at)) * 24 * 60 * 60
                ) as avg_duration
                FROM etl_jobs
                WHERE status = 'success' AND completed_at IS NOT NULL
                """
            )
            avg_duration = cursor.fetchone()["avg_duration"]

        return {
            "total_jobs": sum(status_counts.values()),
            "by_status": status_counts,
            "jobs_last_24h": recent_count,
            "avg_duration_seconds": avg_duration,
            "success_rate": (
                status_counts.get("success", 0) / sum(status_counts.values()) * 100
                if status_counts
                else 0
            ),
        }
