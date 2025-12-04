"""FastAPI application for the ETL Pipeline."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import data, jobs, status, websocket
from src.config.settings import get_settings
from src.orchestrator.pipeline import ETLOrchestrator
from src.orchestrator.scheduler import ETLScheduler
from src.utils.logging import setup_logging

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown."""
    setup_logging()
    logger.info("application_starting")

    # Initialize scheduler
    settings = get_settings()
    scheduler = ETLScheduler()

    if settings.scheduler_enabled:
        orchestrator = ETLOrchestrator()
        scheduler.add_job(
            "scheduled_etl",
            orchestrator.run_full_etl,
            cron_expression=settings.scheduler_cron_expression,
        )
        scheduler.start()
        logger.info("scheduler_initialized")

    app.state.scheduler = scheduler

    yield

    # Shutdown
    scheduler.stop()
    logger.info("application_shutdown")


# Create FastAPI application
app = FastAPI(
    title="FWC ETL Pipeline API",
    description="REST API for managing FWC Modern Awards ETL pipeline",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs.router, prefix="/api", tags=["Jobs"])
app.include_router(status.router, prefix="/api", tags=["Status"])
app.include_router(data.router, prefix="/api", tags=["Data"])
app.include_router(websocket.router, tags=["WebSocket"])


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "name": "FWC ETL Pipeline API",
        "version": "1.0.0",
        "docs": "/api/docs",
    }


def run_server() -> None:
    """Run the FastAPI server."""
    settings = get_settings()
    uvicorn.run(
        "src.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        workers=settings.api_workers,
    )


if __name__ == "__main__":
    run_server()
