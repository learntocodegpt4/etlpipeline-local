"""Status API routes"""

from typing import Any, Dict
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from src.config.settings import get_settings
from src.load.sql_connector import get_connector
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    timestamp: str
    database_connected: bool
    scheduler_running: bool
    version: str


class SystemStatus(BaseModel):
    """System status response"""

    api_status: str
    database_status: str
    scheduler_status: str
    last_job_time: str | None
    config: Dict[str, Any]


@router.get("/status", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """System health check endpoint"""
    settings = get_settings()

    # Test database connection
    db_connected = False
    try:
        connector = get_connector()
        db_connected = connector.test_connection()
    except Exception as e:
        logger.warning("health_check_db_error", error=str(e))

    # Check scheduler
    scheduler_running = False
    try:
        from src.api.app import get_scheduler
        scheduler = get_scheduler()
        scheduler_running = scheduler.is_running
    except Exception:
        pass

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        database_connected=db_connected,
        scheduler_running=scheduler_running,
        version="1.0.0",
    )


@router.get("/status/detailed")
async def detailed_status() -> Dict[str, Any]:
    """Get detailed system status"""
    settings = get_settings()

    # Test database
    db_status = "disconnected"
    try:
        connector = get_connector()
        if connector.test_connection():
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # Scheduler status
    scheduler_status = "not_initialized"
    scheduled_jobs = []
    try:
        from src.api.app import get_scheduler
        scheduler = get_scheduler()
        scheduler_status = "running" if scheduler.is_running else "stopped"
        scheduled_jobs = [
            {
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
            }
            for job in scheduler.get_jobs()
        ]
    except Exception:
        pass

    # Get last job info
    last_job = None
    try:
        from src.api.app import get_state_manager
        sm = get_state_manager()
        jobs = await sm.list_jobs(limit=1)
        if jobs:
            last_job = {
                "job_id": jobs[0]["job_id"],
                "status": jobs[0]["status"],
                "start_time": jobs[0]["start_time"],
            }
    except Exception:
        pass

    return {
        "api": {
            "status": "running",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
        },
        "database": {
            "status": db_status,
            "host": settings.mssql_host,
            "database": settings.mssql_database,
        },
        "scheduler": {
            "status": scheduler_status,
            "enabled": settings.etl_schedule_enabled,
            "cron_expression": settings.etl_cron_expression,
            "scheduled_jobs": scheduled_jobs,
        },
        "last_job": last_job,
        "config": {
            "fwc_api_url": settings.fwc_api_base_url,
            "page_size": settings.default_page_size,
            "log_level": settings.log_level,
        },
    }
