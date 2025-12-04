"""Status and health check routes."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from src.config.settings import get_settings
from src.load.sql_connector import SQLConnector
from src.orchestrator.state_manager import StateManager

router = APIRouter()


class HealthCheck(BaseModel):
    """Health check response model."""

    status: str
    timestamp: str
    version: str
    environment: str
    components: dict[str, Any]


@router.get("/status", response_model=HealthCheck)
async def health_check() -> dict[str, Any]:
    """System health check endpoint.

    Returns status of all system components.
    """
    settings = get_settings()
    components: dict[str, Any] = {}

    # Check database connection
    try:
        connector = SQLConnector()
        db_ok = connector.test_connection()
        components["database"] = {
            "status": "healthy" if db_ok else "unhealthy",
            "host": settings.mssql_host,
            "database": settings.mssql_database,
        }
    except Exception as e:
        components["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }

    # Check state manager
    try:
        state_manager = StateManager()
        stats = await state_manager.get_job_stats()
        components["state_manager"] = {
            "status": "healthy",
            "total_jobs": stats.get("total_jobs", 0),
        }
    except Exception as e:
        components["state_manager"] = {
            "status": "unhealthy",
            "error": str(e),
        }

    # Check API key configuration
    components["api_config"] = {
        "status": "healthy" if settings.fwc_api_key else "warning",
        "api_key_configured": bool(settings.fwc_api_key),
    }

    # Check scheduler
    components["scheduler"] = {
        "status": "healthy" if settings.scheduler_enabled else "disabled",
        "enabled": settings.scheduler_enabled,
        "cron": settings.scheduler_cron_expression,
    }

    # Overall status
    all_healthy = all(
        c.get("status") in ("healthy", "disabled", "warning")
        for c in components.values()
    )

    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": settings.environment,
        "components": components,
    }


@router.get("/status/config")
async def get_config() -> dict[str, Any]:
    """Get current configuration (non-sensitive values only)."""
    settings = get_settings()

    return {
        "fwc_api": {
            "base_url": settings.fwc_api_base_url,
            "timeout": settings.fwc_api_timeout,
            "max_retries": settings.fwc_api_max_retries,
            "page_size": settings.fwc_api_page_size,
        },
        "database": {
            "host": settings.mssql_host,
            "port": settings.mssql_port,
            "database": settings.mssql_database,
        },
        "scheduler": {
            "enabled": settings.scheduler_enabled,
            "cron": settings.scheduler_cron_expression,
            "timezone": settings.scheduler_timezone,
        },
        "logging": {
            "level": settings.log_level,
            "format": settings.log_format,
        },
        "environment": settings.environment,
    }
