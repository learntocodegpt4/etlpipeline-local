"""Pipeline orchestration and execution"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from src.core.interfaces import (
    PipelineStep,
    PipelineContext,
    StepResult,
    StepStatus,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PipelineResult:
    """Result of a complete pipeline execution"""

    job_id: str
    status: StepStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    step_results: Dict[str, StepResult] = field(default_factory=dict)
    total_records_processed: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate total duration in seconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "total_records_processed": self.total_records_processed,
            "errors": self.errors,
            "warnings": self.warnings,
            "step_results": {
                name: {
                    "status": result.status.value,
                    "records_processed": result.records_processed,
                    "records_failed": result.records_failed,
                    "duration_seconds": result.duration_seconds,
                    "error_message": result.error_message,
                }
                for name, result in self.step_results.items()
            },
        }


class Pipeline:
    """ETL Pipeline orchestrator"""

    def __init__(
        self,
        name: str,
        steps: Optional[List[PipelineStep]] = None,
        stop_on_error: bool = True,
    ):
        self.name = name
        self.steps: List[PipelineStep] = steps or []
        self.stop_on_error = stop_on_error
        self._running = False
        self._current_job_id: Optional[str] = None

    def add_step(self, step: PipelineStep) -> "Pipeline":
        """Add a step to the pipeline"""
        self.steps.append(step)
        return self

    def add_steps(self, steps: List[PipelineStep]) -> "Pipeline":
        """Add multiple steps to the pipeline"""
        self.steps.extend(steps)
        return self

    async def execute(
        self,
        context: Optional[PipelineContext] = None,
        job_id: Optional[str] = None,
    ) -> PipelineResult:
        """Execute all pipeline steps"""
        if self._running:
            raise RuntimeError("Pipeline is already running")

        self._running = True
        job_id = job_id or str(uuid.uuid4())
        self._current_job_id = job_id

        if context is None:
            context = PipelineContext(job_id=job_id)
        else:
            context.job_id = job_id

        result = PipelineResult(
            job_id=job_id,
            status=StepStatus.RUNNING,
            start_time=datetime.utcnow(),
        )

        logger.info(
            "pipeline_started",
            pipeline=self.name,
            job_id=job_id,
            steps_count=len(self.steps),
        )

        try:
            for step in self.steps:
                step_name = step.name
                logger.info(
                    "step_started",
                    pipeline=self.name,
                    job_id=job_id,
                    step=step_name,
                )

                try:
                    step_result = await step.execute(context)
                    result.step_results[step_name] = step_result

                    if step_result.status == StepStatus.COMPLETED:
                        result.total_records_processed += step_result.records_processed
                        logger.info(
                            "step_completed",
                            pipeline=self.name,
                            job_id=job_id,
                            step=step_name,
                            records=step_result.records_processed,
                            duration=step_result.duration_seconds,
                        )
                    elif step_result.status == StepStatus.FAILED:
                        error_msg = f"Step '{step_name}' failed: {step_result.error_message}"
                        result.errors.append(error_msg)
                        logger.error(
                            "step_failed",
                            pipeline=self.name,
                            job_id=job_id,
                            step=step_name,
                            error=step_result.error_message,
                        )

                        if self.stop_on_error:
                            result.status = StepStatus.FAILED
                            break
                    elif step_result.status == StepStatus.SKIPPED:
                        logger.info(
                            "step_skipped",
                            pipeline=self.name,
                            job_id=job_id,
                            step=step_name,
                            reason=step_result.details.get("reason"),
                        )

                except Exception as e:
                    error_msg = f"Unexpected error in step '{step_name}': {str(e)}"
                    result.errors.append(error_msg)
                    result.step_results[step_name] = StepResult(
                        status=StepStatus.FAILED,
                        error_message=str(e),
                    )
                    logger.exception(
                        "step_exception",
                        pipeline=self.name,
                        job_id=job_id,
                        step=step_name,
                    )

                    if self.stop_on_error:
                        result.status = StepStatus.FAILED
                        break

            # Set final status if not already failed
            if result.status != StepStatus.FAILED:
                result.status = StepStatus.COMPLETED

            # Collect context errors and warnings
            result.errors.extend(context.errors)
            result.warnings.extend(context.warnings)

        finally:
            result.end_time = datetime.utcnow()
            self._running = False
            self._current_job_id = None

            logger.info(
                "pipeline_completed",
                pipeline=self.name,
                job_id=job_id,
                status=result.status.value,
                duration=result.duration_seconds,
                total_records=result.total_records_processed,
                errors_count=len(result.errors),
            )

        return result

    @property
    def is_running(self) -> bool:
        """Check if pipeline is currently running"""
        return self._running

    @property
    def current_job_id(self) -> Optional[str]:
        """Get the current job ID if running"""
        return self._current_job_id
