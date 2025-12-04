"""State management using SQLite for job tracking"""

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

    async def initialize(self) -> None:
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration_seconds REAL,
                    total_records_processed INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    warning_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    result_json TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS job_steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    step_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    start_time TEXT,
                    end_time TEXT,
                    duration_seconds REAL,
                    records_processed INTEGER DEFAULT 0,
                    records_failed INTEGER DEFAULT 0,
                    error_message TEXT,
                    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_job_steps_job_id ON job_steps(job_id)
            """)
            await db.commit()
            logger.info("state_manager_initialized")

    async def create_job(self, job_id: str) -> None:
        """Create a new job record"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO jobs (job_id, status, start_time)
                VALUES (?, ?, ?)
                """,
                (job_id, "pending", datetime.utcnow().isoformat()),
            )
            await db.commit()
            logger.info("job_created", job_id=job_id)

    async def update_job_status(
        self,
        job_id: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        """Update job status"""
        async with aiosqlite.connect(self.db_path) as db:
            if error_message:
                await db.execute(
                    """
                    UPDATE jobs SET status = ?, error_message = ?
                    WHERE job_id = ?
                    """,
                    (status, error_message, job_id),
                )
            else:
                await db.execute(
                    """
                    UPDATE jobs SET status = ?
                    WHERE job_id = ?
                    """,
                    (status, job_id),
                )
            await db.commit()
            logger.info("job_status_updated", job_id=job_id, status=status)

    async def save_job_result(self, job_id: str, result: PipelineResult) -> None:
        """Save complete job result"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE jobs SET
                    status = ?,
                    end_time = ?,
                    duration_seconds = ?,
                    total_records_processed = ?,
                    error_count = ?,
                    warning_count = ?,
                    error_message = ?,
                    result_json = ?
                WHERE job_id = ?
                """,
                (
                    result.status.value,
                    result.end_time.isoformat() if result.end_time else None,
                    result.duration_seconds,
                    result.total_records_processed,
                    len(result.errors),
                    len(result.warnings),
                    "; ".join(result.errors) if result.errors else None,
                    json.dumps(result.to_dict()),
                    job_id,
                ),
            )

            # Save step results
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
                        step_result.status.value,
                        step_result.start_time.isoformat() if step_result.start_time else None,
                        step_result.end_time.isoformat() if step_result.end_time else None,
                        step_result.duration_seconds,
                        step_result.records_processed,
                        step_result.records_failed,
                        step_result.error_message,
                    ),
                )

            await db.commit()
            logger.info("job_result_saved", job_id=job_id)

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM jobs WHERE job_id = ?",
                (job_id,),
            )
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

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

    async def list_jobs(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List jobs with pagination"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            if status:
                cursor = await db.execute(
                    """
                    SELECT * FROM jobs WHERE status = ?
                    ORDER BY start_time DESC LIMIT ? OFFSET ?
                    """,
                    (status, limit, offset),
                )
            else:
                cursor = await db.execute(
                    """
                    SELECT * FROM jobs
                    ORDER BY start_time DESC LIMIT ? OFFSET ?
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

    async def get_recent_job_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get job statistics for recent period"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT
                    status,
                    COUNT(*) as count,
                    AVG(duration_seconds) as avg_duration,
                    SUM(total_records_processed) as total_records
                FROM jobs
                WHERE start_time >= datetime('now', ?)
                GROUP BY status
                """,
                (f"-{days} days",),
            )
            rows = await cursor.fetchall()

            stats = {
                "total": 0,
                "by_status": {},
                "avg_duration": 0,
                "total_records": 0,
            }

            for row in rows:
                status, count, avg_dur, records = row
                stats["by_status"][status] = count
                stats["total"] += count
                if avg_dur:
                    stats["avg_duration"] = avg_dur
                if records:
                    stats["total_records"] += records

            return stats
