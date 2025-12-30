"""Jobs API routes"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
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
    name: Optional[str] = None
    status: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    total_records_processed: Optional[int] = 0
    error_count: Optional[int] = 0
    warning_count: Optional[int] = 0
    error_message: Optional[str] = None


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
    sm: StateManager = Depends(get_state_manager),
) -> JobListResponse:
    """List all ETL jobs with pagination"""
    # sm = Depends(get_state_manager)
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
async def get_job(job_id: str,  sm: StateManager = Depends(get_state_manager)) -> Dict[str, Any]:
    """Get details of a specific job"""
    # sm = Depends(get_state_manager)
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
async def get_job_logs(job_id: str, sm: StateManager = Depends(get_state_manager)) -> List[JobStepResponse]:
    """Get logs for a specific job"""
    # sm = Depends(get_state_manager)
    job = await sm.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    steps = await sm.get_job_steps(job_id)
    return [JobStepResponse(**step) for step in steps]


async def _run_pipeline_task(
    award_codes: Optional[List[str]] = None, job_id: Optional[str] = None
) -> None:
    """Background task to run ETL pipeline with a provided job_id."""
    try:
        await run_etl_pipeline(award_codes=award_codes, job_id=job_id)
    except Exception:
        logger.exception("background_pipeline_error")


@router.post("/jobs/trigger", response_model=TriggerResponse)
async def trigger_job(
    request: TriggerRequest,
    background_tasks: BackgroundTasks,
     sm: StateManager = Depends(get_state_manager)
) -> TriggerResponse:
    """Manually trigger ETL pipeline"""
    import uuid

    job_id = str(uuid.uuid4())
    # sm = Depends(get_state_manager)

    # Create job record first
    # await sm.create_job(job_id)

    # Run pipeline in background; pass job_id so the pipeline uses the same job record
    background_tasks.add_task(_run_pipeline_task, request.award_codes, job_id)

    logger.info("job_triggered", job_id=job_id)

    return TriggerResponse(
        job_id=job_id,
        message="ETL pipeline triggered successfully",
    )


@router.post("/jobs/trigger_sync")
async def trigger_job_sync(request: TriggerRequest,  sm: StateManager = Depends(get_state_manager)) -> Dict[str, Any]:
    """Synchronously run the ETL pipeline and return the result.

    This endpoint is intended for manual testing via Swagger/UI. It will run
    the pipeline inline and return the pipeline result (may take time).
    """
    import uuid

    job_id = str(uuid.uuid4())
    #sm = Depends(get_state_manager)

    logger.info("job_triggered_sync", job_id=job_id)

    # Run pipeline inline and return the result. ETLPipeline.run will create the
    # job record itself using the provided job_id, so we must not pre-create it
    # here (that caused UNIQUE constraint failures).
    result = await run_etl_pipeline(award_codes=request.award_codes, job_id=job_id)

    # Save result to state (run_etl_pipeline already calls save_job_result,
    # but saving again is idempotent for the state DB)
    # try:
    #     await sm.save_job_result(job_id, result)
    # except Exception:
    #     # If save fails because the pipeline already saved it, ignore.
    #     pass

    return result.to_dict()


@router.get("/jobs/stats/summary")
async def get_job_stats(days: int = Query(7, ge=1, le=30), sm: StateManager = Depends(get_state_manager)) -> Dict[str, Any]:
    """Get job statistics summary"""
    # sm = Depends(get_state_manager)
    return await sm.get_recent_job_stats(days=days)


@router.post("/jobs/cleanup_pending")
async def cleanup_pending_jobs(age_seconds: Optional[int] = None, sm: StateManager = Depends(get_state_manager)) -> Dict[str, Any]:
    """Mark pending jobs as failed. Optionally only those older than `age_seconds`."""
    # sm = Depends(get_state_manager)
    count = await sm.cleanup_pending_jobs(older_than_seconds=age_seconds)
    return {"marked_failed": count}


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, sm: StateManager = Depends(get_state_manager)) -> Dict[str, Any]:
    """Delete a job and its steps from the state DB."""
    # sm = Depends(get_state_manager)
    await sm.delete_job(job_id)
    return {"deleted": job_id}


@router.get("/jobs/{job_id}/diagnostics")
async def get_job_diagnostics(job_id: str, sm: StateManager = Depends(get_state_manager)) -> Dict[str, Any]:
    """Get detailed diagnostics for a job including step-by-step breakdown"""
    from src.load.sql_connector import get_connector
    
    job = await sm.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    steps = await sm.get_job_steps(job_id)
    
    # Build step summary
    step_summary = {}
    for step in steps:
        step_name = step.get('step_name', 'unknown')
        step_summary[step_name] = {
            'status': step.get('status'),
            'records_processed': step.get('records_processed', 0),
            'records_failed': step.get('records_failed', 0),
            'error': step.get('error_message'),
            'duration_seconds': step.get('duration_seconds'),
        }
    
    # Check database tables for actual row counts
    table_counts = {}
    try:
        connector = get_connector()
        tables = ['Stg_TblAwards', 'Stg_TblClassifications', 'Stg_TblPayRates', 
                  'Stg_TblExpenseAllowances', 'Stg_TblWageAllowances', 'Stg_TblPenalties']
        for table in tables:
            try:
                result = connector.execute_query(f"SELECT COUNT(*) as cnt FROM {table}")
                table_counts[table] = result[0]['cnt'] if result else 0
            except Exception as e:
                table_counts[table] = f"error: {str(e)}"
    except Exception as e:
        logger.error("diagnostics_db_error", error=str(e))
    
    return {
        'job': job,
        'step_summary': step_summary,
        'table_row_counts': table_counts,
        'warnings': job.get('warnings', []),
        'errors': job.get('error_message'),
    }
