"""Jobs API routes."""

from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from src.orchestrator.pipeline import ETLOrchestrator
from src.orchestrator.state_manager import StateManager
from src.utils.helpers import generate_job_id

router = APIRouter()
state_manager = StateManager()


class TriggerRequest(BaseModel):
    """Request model for triggering ETL jobs."""

    pipeline_type: str | None = Field(
        default=None,
        description="Type of pipeline to run (awards, classifications, pay_rates, etc.). If None, runs full ETL.",
    )
    award_codes: list[str] | None = Field(
        default=None,
        description="List of award codes to process. If None, processes all awards.",
    )


class TriggerResponse(BaseModel):
    """Response model for trigger requests."""

    job_id: str
    status: str
    message: str


class JobSummary(BaseModel):
    """Summary model for job listings."""

    job_id: str
    pipeline_name: str
    status: str
    started_at: str | None
    completed_at: str | None
    total_records: int
    error_message: str | None


class JobDetail(BaseModel):
    """Detailed job information."""

    job_id: str
    pipeline_name: str
    status: str
    started_at: str | None
    completed_at: str | None
    total_records: int
    error_message: str | None
    parameters: str | None
    details: list[dict[str, Any]]


@router.get("/jobs", response_model=list[JobSummary])
async def list_jobs(
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """List all ETL jobs with optional filtering.

    Args:
        status: Filter by job status (pending, running, success, failed)
        limit: Maximum number of results
        offset: Offset for pagination
    """
    jobs = await state_manager.get_jobs(status=status, limit=limit, offset=offset)
    return jobs


@router.get("/jobs/{job_id}", response_model=JobDetail)
async def get_job(job_id: str) -> dict[str, Any]:
    """Get details of a specific job.

    Args:
        job_id: Job identifier
    """
    job = await state_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    details = await state_manager.get_job_details(job_id)
    job["details"] = details

    return job


@router.get("/jobs/{job_id}/logs")
async def get_job_logs(job_id: str) -> dict[str, Any]:
    """Get logs for a specific job.

    Args:
        job_id: Job identifier
    """
    job = await state_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    details = await state_manager.get_job_details(job_id)

    return {
        "job_id": job_id,
        "status": job["status"],
        "logs": details,
    }


@router.post("/jobs/trigger", response_model=TriggerResponse)
async def trigger_job(
    request: TriggerRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """Manually trigger an ETL pipeline.

    Args:
        request: Trigger request parameters
        background_tasks: FastAPI background tasks
    """
    job_id = generate_job_id()

    async def run_pipeline() -> None:
        orchestrator = ETLOrchestrator()
        if request.pipeline_type:
            # Run specific pipeline
            award_code = request.award_codes[0] if request.award_codes else None
            await orchestrator.run_single_pipeline(
                pipeline_type=request.pipeline_type,
                award_code=award_code,
                job_id=job_id,
            )
        else:
            # Run full ETL
            await orchestrator.run_full_etl(
                award_codes=request.award_codes,
                job_id=job_id,
            )

    background_tasks.add_task(run_pipeline)

    return {
        "job_id": job_id,
        "status": "triggered",
        "message": f"ETL job {job_id} has been triggered",
    }


@router.get("/jobs/stats/summary")
async def get_job_stats() -> dict[str, Any]:
    """Get job statistics summary."""
    return await state_manager.get_job_stats()
