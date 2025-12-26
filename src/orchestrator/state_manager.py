"""State management using SQLite for job tracking"""

import sqlite3
import aiosqlite
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config.settings import get_settings
from src.core.pipeline import PipelineResult
from src.core.interfaces import StepStatus
from src.utils.logging import get_logger

logger = get_logger(__name__)


class StateManager:
    """Manage ETL pipeline state using SQLite"""

    def __init__(self, db_path: Optional[str] = None):
        settings = get_settings()
        self.db_path = db_path or settings.sqlite_database_path
        self._ensure_db_dir()

    def _ensure_db_dir(self) -> None:
        """Ensure database directory exists"""
        path = Path(self.db_path)
        path.parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """Initialize SQLite database with required tables"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT UNIQUE NOT NULL,
                    name TEXT,
                    status TEXT DEFAULT 'pending',
                    progress INTEGER DEFAULT 0,
                    total_records INTEGER DEFAULT 0,
                    processed_records INTEGER DEFAULT 0,
                    failed_records INTEGER DEFAULT 0,
                    error_message TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS job_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    level TEXT,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
                );

                CREATE TABLE IF NOT EXISTS job_steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    step_name TEXT,
                    status TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration_seconds REAL,
                    records_processed INTEGER DEFAULT 0,
                    records_failed INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
                );

                CREATE INDEX IF NOT EXISTS idx_jobs_job_id ON jobs(job_id);
                CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
                CREATE INDEX IF NOT EXISTS idx_job_logs_job_id ON job_logs(job_id);
                CREATE INDEX IF NOT EXISTS idx_job_steps_job_id ON job_steps(job_id);
                """
            )
            await db.commit()
            logger.info("database_initialized", db_path=self.db_path)

            # Backward-compatible migration: ensure required columns exist on existing DBs
            try:
                # Fetch existing columns for 'jobs'
                cur = await db.execute("PRAGMA table_info(jobs)")
                cols = [row[1] for row in await cur.fetchall()]

                # Add 'progress' column if missing (older DBs)
                if "progress" not in cols:
                    await db.execute("ALTER TABLE jobs ADD COLUMN progress INTEGER DEFAULT 0")
                    logger.info("sqlite_migration_applied", table="jobs", column="progress")

                await db.commit()
            except Exception as e:
                # Log and proceed; initialization shouldn't fatally fail due to migrations
                logger.warning("sqlite_migration_warning", error=str(e))

    async def create_job(self, job_id: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Insert a job; if it already exists, reset it."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # First check if job exists
            cursor = await db.execute(
                "SELECT * FROM jobs WHERE job_id = ?",
                (job_id,),
            )
            existing = await cursor.fetchone()
            
            if existing:
                # Job exists - reset it
                logger.warning("job_already_exists_resetting", job_id=job_id)
                await db.execute(
                    """
                    UPDATE jobs
                    SET name = ?, status = ?, progress = 0, 
                        error_message = NULL, updated_at = CURRENT_TIMESTAMP
                    WHERE job_id = ?
                    """,
                    (name or job_id, "pending", job_id),
                )
            else:
                # Job doesn't exist - create it
                await db.execute(
                    """
                    INSERT INTO jobs (job_id, name, status, progress, created_at, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    (job_id, name or job_id, "pending", 0),
                )
                logger.info("job_created", job_id=job_id, name=name)

            await db.commit()

            # Fetch and return the job
            cursor = await db.execute(
                "SELECT * FROM jobs WHERE job_id = ?",
                (job_id,),
            )
            row = await cursor.fetchone()
            return dict(row) if row else {}

    async def update_job_status(
        self,
        job_id: str,
        status: str,
        progress: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Update job status and progress"""
        async with aiosqlite.connect(self.db_path) as db:
            if error_message:
                await db.execute(
                    """
                    UPDATE jobs
                    SET status = ?, progress = COALESCE(?, progress), 
                        error_message = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE job_id = ?
                    """,
                    (status, progress, error_message, job_id),
                )
            else:
                await db.execute(
                    """
                    UPDATE jobs
                    SET status = ?, progress = COALESCE(?, progress), 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE job_id = ?
                    """,
                    (status, progress, job_id),
                )
            await db.commit()
            logger.info("job_status_updated", job_id=job_id, status=status, progress=progress)

    async def update_job_completion(
        self,
        job_id: str,
        status: str,
        total_records: int = 0,
        processed_records: int = 0,
        failed_records: int = 0,
        error_message: Optional[str] = None,
    ) -> None:
        """Update job completion details"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE jobs
                SET status = ?, total_records = ?, processed_records = ?,
                    failed_records = ?, error_message = ?, 
                    completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE job_id = ?
                """,
                (
                    status,
                    total_records,
                    processed_records,
                    failed_records,
                    error_message,
                    job_id,
                ),
            )
            await db.commit()
            logger.info(
                "job_completed",
                job_id=job_id,
                status=status,
                total=total_records,
                processed=processed_records,
                failed=failed_records,
            )

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM jobs WHERE job_id = ?",
                (job_id,),
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def list_jobs(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List all jobs with pagination"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            if status:
                cursor = await db.execute(
                    """
                    SELECT * FROM jobs WHERE status = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (status, limit, offset),
                )
            else:
                cursor = await db.execute(
                    """
                    SELECT * FROM jobs
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (limit, offset),
                )
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_job_count(self, status: Optional[str] = None) -> int:
        """Get total job count"""
        async with aiosqlite.connect(self.db_path) as db:
            if status:
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM jobs WHERE status = ?",
                    (status,),
                )
            else:
                cursor = await db.execute("SELECT COUNT(*) FROM jobs")
            
            result = await cursor.fetchone()
            return result[0] if result else 0

    async def add_job_log(self, job_id: str, level: str, message: str) -> None:
        """Add a log entry for a job"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO job_logs (job_id, level, message)
                VALUES (?, ?, ?)
                """,
                (job_id, level, message),
            )
            await db.commit()

    async def get_job_logs(self, job_id: str) -> List[Dict[str, Any]]:
        """Get all logs for a job"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM job_logs
                WHERE job_id = ?
                ORDER BY created_at ASC
                """,
                (job_id,),
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def delete_job(self, job_id: str) -> None:
        """Delete a job and its steps from the state DB (irreversible)."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM job_logs WHERE job_id = ?", (job_id,))
            await db.execute("DELETE FROM job_steps WHERE job_id = ?", (job_id,))
            await db.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
            await db.commit()
            logger.info("job_deleted", job_id=job_id)

    async def cleanup_pending_jobs(self, older_than_seconds: Optional[int] = None) -> int:
        """Mark pending jobs as failed (optionally only those older than given seconds).
        
        Returns number of jobs marked failed.
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Build selection
            if older_than_seconds is None:
                cursor = await db.execute("SELECT job_id FROM jobs WHERE status = 'pending'")
            else:
                # Convert to datetime comparison using SQLite datetime functions
                cursor = await db.execute(
                    "SELECT job_id FROM jobs WHERE status = 'pending' AND created_at <= datetime('now', ?)",
                    (f'-{older_than_seconds} seconds',),
                )
            rows = await cursor.fetchall()
            job_ids = [r[0] for r in rows]
            
            for jid in job_ids:
                await db.execute(
                    "UPDATE jobs SET status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP WHERE job_id = ?",
                    ("failed", "Marked failed by cleanup", jid),
                )
            await db.commit()
            logger.info("cleanup_pending_jobs", count=len(job_ids))
            return len(job_ids)

    async def save_job_result(self, job_id: str, result: PipelineResult) -> None:
        """Save complete job result"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE jobs SET
                    status = ?,
                    completed_at = ?,
                    total_records = ?,
                    processed_records = ?,
                    failed_records = ?,
                    error_message = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE job_id = ?
                """,
                (
                    result.status.value if hasattr(result.status, 'value') else str(result.status),
                    result.end_time.isoformat() if result.end_time else None,
                    result.total_records_processed,
                    result.total_records_processed - len(result.errors) if hasattr(result, 'errors') else 0,
                    len(result.errors) if hasattr(result, 'errors') else 0,
                    "; ".join(result.errors) if hasattr(result, 'errors') and result.errors else None,
                    job_id,
                ),
            )

            # Save step results if available
            if hasattr(result, 'step_results'):
                for step_name, step_result in result.step_results.items():
                    await db.execute(
                        """
                        INSERT INTO job_steps
                        (job_id, step_name, status, start_time, end_time,
                         duration_seconds, records_processed, records_failed, error_message)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            job_id,
                            step_name,
                            step_result.status.value if hasattr(step_result.status, 'value') else str(step_result.status),
                            step_result.start_time.isoformat() if hasattr(step_result, 'start_time') and step_result.start_time else None,
                            step_result.end_time.isoformat() if hasattr(step_result, 'end_time') and step_result.end_time else None,
                            step_result.duration_seconds if hasattr(step_result, 'duration_seconds') else None,
                            step_result.records_processed if hasattr(step_result, 'records_processed') else 0,
                            step_result.records_failed if hasattr(step_result, 'records_failed') else 0,
                            step_result.error_message if hasattr(step_result, 'error_message') else None,
                        ),
                    )

            await db.commit()
            logger.info("job_result_saved", job_id=job_id)

    async def get_job_steps(self, job_id: str) -> List[Dict[str, Any]]:
        """Get job steps"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM job_steps WHERE job_id = ? ORDER BY id",
                (job_id,),
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_recent_job_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get job statistics for recent period"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT
                    status,
                    COUNT(*) as count,
                    SUM(total_records) as total_records
                FROM jobs
                WHERE created_at >= datetime('now', ?)
                GROUP BY status
                """,
                (f"-{days} days",),
            )
            rows = await cursor.fetchall()

            stats = {
                "total": 0,
                "by_status": {},
                "total_records": 0,
            }

            for row in rows:
                status, count, records = row
                stats["by_status"][status] = count
                stats["total"] += count
                if records:
                    stats["total_records"] += records

            return stats