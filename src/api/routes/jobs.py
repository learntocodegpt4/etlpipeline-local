"""Jobs API routes"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel

from src.orchestrator.state_manager import StateManager
from src.orchestrator.pipeline import run_etl_pipeline
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class TriggerRequest(BaseModel):
    """Request model for triggering ETL pipeline"""

    award_codes: Optional[List[str]] = None


class TriggerResponse(BaseModel):
    """Response model for trigger endpoint"""

    job_id: str
    message: str


class JobResponse(BaseModel):
    """Response model for job details"""

    job_id: str
    status: str
    start_time: str
    end_time: Optional[str]
    duration_seconds: Optional[float]
    total_records_processed: int
    error_count: int
    warning_count: int
    error_message: Optional[str]


class JobStepResponse(BaseModel):
    """Response model for job step"""

    step_name: str
    status: str
    start_time: Optional[str]
    end_time: Optional[str]
    duration_seconds: Optional[float]
    records_processed: int
    records_failed: int
    error_message: Optional[str]


class JobListResponse(BaseModel):
    """Response model for job list"""

    jobs: List[JobResponse]
    total: int
    page: int
    page_size: int


def get_state_manager() -> StateManager:
    """Get state manager - imported lazily to avoid circular imports"""
    from src.api.app import get_state_manager as get_sm
    return get_sm()


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
) -> JobListResponse:
    """List all ETL jobs with pagination"""
    sm = get_state_manager()
    offset = (page - 1) * page_size

    jobs = await sm.list_jobs(limit=page_size, offset=offset, status=status)
    total = await sm.get_job_count(status=status)

    return JobListResponse(
        jobs=[JobResponse(**job) for job in jobs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/jobs/{job_id}", response_model=Dict[str, Any])
async def get_job(job_id: str) -> Dict[str, Any]:
    """Get details of a specific job"""
    sm = get_state_manager()
    job = await sm.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get job steps
    steps = await sm.get_job_steps(job_id)

    return {
        **job,
        "steps": steps,
    }


@router.get("/jobs/{job_id}/logs", response_model=List[JobStepResponse])
async def get_job_logs(job_id: str) -> List[JobStepResponse]:
    """Get logs for a specific job"""
    sm = get_state_manager()
    job = await sm.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    steps = await sm.get_job_steps(job_id)
    return [JobStepResponse(**step) for step in steps]


async def _run_pipeline_task(award_codes: Optional[List[str]] = None) -> None:
    """Background task to run ETL pipeline"""
    try:
        await run_etl_pipeline(award_codes=award_codes)
    except Exception as e:
        logger.exception("background_pipeline_error")


@router.post("/jobs/trigger", response_model=TriggerResponse)
async def trigger_job(
    request: TriggerRequest,
    background_tasks: BackgroundTasks,
) -> TriggerResponse:
    """Manually trigger ETL pipeline"""
    import uuid

    job_id = str(uuid.uuid4())
    sm = get_state_manager()

    # Create job record first
    await sm.create_job(job_id)

    # Run pipeline in background
    background_tasks.add_task(_run_pipeline_task, request.award_codes)

    logger.info("job_triggered", job_id=job_id)

    return TriggerResponse(
        job_id=job_id,
        message="ETL pipeline triggered successfully",
    )


@router.get("/jobs/stats/summary")
async def get_job_stats(days: int = Query(7, ge=1, le=30)) -> Dict[str, Any]:
    """Get job statistics summary"""
    sm = get_state_manager()
    return await sm.get_recent_job_stats(days=days)
