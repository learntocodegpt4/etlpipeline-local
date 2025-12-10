"""FastAPI application for ETL Pipeline"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import jobs, status, data, websocket
from src.config.settings import get_settings
from src.orchestrator.state_manager import StateManager
from src.orchestrator.scheduler import Scheduler
from src.orchestrator.pipeline import run_etl_pipeline
from src.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)

# Global instances
state_manager: StateManager | None = None
scheduler: Scheduler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan events"""
    global state_manager, scheduler

    settings = get_settings()

    # Setup logging
    setup_logging(
        log_level=settings.log_level,
        log_file=settings.log_file_path,
    )

    # Initialize state manager
    state_manager = StateManager()
    await state_manager.initialize()

    # Initialize scheduler
    scheduler = Scheduler()
    scheduler.set_job_function(run_etl_pipeline)

    if settings.etl_schedule_enabled:
        scheduler.add_cron_job()
        scheduler.start()
        logger.info("etl_scheduler_started")

    logger.info("api_server_started")

    yield

    # Cleanup
    if scheduler and scheduler.is_running:
        scheduler.stop()

    logger.info("api_server_stopped")


# Create FastAPI app
# app = FastAPI(
#     title="FWC ETL Pipeline API",
#     description="REST API for FWC Modern Awards ETL Pipeline",
#     version="1.0.0",
#     lifespan=lifespan,
# )
# Get root path from environment variable for reverse proxy support
root_path = os.getenv("ROOT_PATH", "")
app = FastAPI(
    title="ETL Pipeline API",
    description="REST API for FWC Modern Awards ETL Pipeline",
    version="1.0.0",
    lifespan = lifespan,
    root_path=root_path,  # This makes /docs work with prefix
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
settings = get_settings()
cors_origins = settings.cors_origins.split(",") if settings.cors_origins != "*" else ["*"]
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=cors_origins,  # Configure via CORS_ORIGINS env var in production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs.router, prefix="/api", tags=["Jobs"])
app.include_router(status.router, prefix="/api", tags=["Status"])
app.include_router(data.router, prefix="/api", tags=["Data"])
app.include_router(websocket.router, tags=["WebSocket"])


def get_state_manager() -> StateManager:
    """Get state manager instance"""
    if state_manager is None:
        raise RuntimeError("State manager not initialized")
    return state_manager


def get_scheduler() -> Scheduler:
    """Get scheduler instance"""
    if scheduler is None:
        raise RuntimeError("Scheduler not initialized")
    return scheduler


def run_server() -> None:
    """Run the API server"""
    settings = get_settings()
    uvicorn.run(
        "src.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )


if __name__ == "__main__":
    run_server()
