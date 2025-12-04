"""Core interfaces for the ETL pipeline.

These interfaces define the contract for ETL components, enabling
portability across different deployment targets (standalone, Docker,
Azure Functions, Azure VMs).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

T = TypeVar("T")
InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class StepStatus(str, Enum):
    """Status of a pipeline step."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult(Generic[T]):
    """Result of a pipeline step execution."""

    status: StepStatus
    data: T | None = None
    error: str | None = None
    error_details: dict[str, Any] | None = None
    records_processed: int = 0
    start_time: datetime | None = None
    end_time: datetime | None = None

    @property
    def duration_seconds(self) -> float | None:
        """Calculate duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


@dataclass
class PipelineContext:
    """Context passed through the pipeline for state management."""

    job_id: str
    started_at: datetime
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    step_results: dict[str, StepResult[Any]] = field(default_factory=dict)

    def add_error(self, error: str) -> None:
        """Add an error to the context."""
        self.errors.append(error)

    def set_step_result(self, step_name: str, result: StepResult[Any]) -> None:
        """Store the result of a step."""
        self.step_results[step_name] = result

    def get_step_result(self, step_name: str) -> StepResult[Any] | None:
        """Get the result of a previous step."""
        return self.step_results.get(step_name)

    @property
    def has_errors(self) -> bool:
        """Check if the context has any errors."""
        return len(self.errors) > 0 or any(
            r.status == StepStatus.FAILED for r in self.step_results.values()
        )


class PipelineStep(ABC, Generic[InputT, OutputT]):
    """Base class for all pipeline steps."""

    def __init__(self, name: str | None = None):
        self.name = name or self.__class__.__name__

    @abstractmethod
    async def execute(
        self, data: InputT, context: PipelineContext
    ) -> StepResult[OutputT]:
        """Execute the pipeline step.

        Args:
            data: Input data for the step
            context: Pipeline context for state management

        Returns:
            StepResult containing the output or error information
        """
        pass

    async def __call__(
        self, data: InputT, context: PipelineContext
    ) -> StepResult[OutputT]:
        """Allow step to be called as a function."""
        return await self.execute(data, context)


class Extractor(PipelineStep[dict[str, Any], list[dict[str, Any]]], ABC):
    """Base class for data extractors.

    Extractors are responsible for fetching data from external sources
    (APIs, databases, files, etc.) and returning it in a standardized format.
    """

    @abstractmethod
    async def extract(
        self, params: dict[str, Any], context: PipelineContext
    ) -> list[dict[str, Any]]:
        """Extract data from the source.

        Args:
            params: Parameters for the extraction (filters, pagination, etc.)
            context: Pipeline context

        Returns:
            List of extracted records
        """
        pass

    async def execute(
        self, data: dict[str, Any], context: PipelineContext
    ) -> StepResult[list[dict[str, Any]]]:
        """Execute the extraction step."""
        start_time = datetime.now()
        try:
            records = await self.extract(data, context)
            return StepResult(
                status=StepStatus.SUCCESS,
                data=records,
                records_processed=len(records),
                start_time=start_time,
                end_time=datetime.now(),
            )
        except Exception as e:
            return StepResult(
                status=StepStatus.FAILED,
                error=str(e),
                error_details={"exception_type": type(e).__name__},
                start_time=start_time,
                end_time=datetime.now(),
            )


class Transformer(PipelineStep[list[dict[str, Any]], list[dict[str, Any]]], ABC):
    """Base class for data transformers.

    Transformers are responsible for cleaning, validating, and transforming
    data from the extraction format to the loading format.
    """

    @abstractmethod
    async def transform(
        self, records: list[dict[str, Any]], context: PipelineContext
    ) -> list[dict[str, Any]]:
        """Transform the extracted data.

        Args:
            records: List of raw records from extraction
            context: Pipeline context

        Returns:
            List of transformed records
        """
        pass

    async def execute(
        self, data: list[dict[str, Any]], context: PipelineContext
    ) -> StepResult[list[dict[str, Any]]]:
        """Execute the transformation step."""
        start_time = datetime.now()
        try:
            records = await self.transform(data, context)
            return StepResult(
                status=StepStatus.SUCCESS,
                data=records,
                records_processed=len(records),
                start_time=start_time,
                end_time=datetime.now(),
            )
        except Exception as e:
            return StepResult(
                status=StepStatus.FAILED,
                error=str(e),
                error_details={"exception_type": type(e).__name__},
                start_time=start_time,
                end_time=datetime.now(),
            )


class Loader(PipelineStep[list[dict[str, Any]], int], ABC):
    """Base class for data loaders.

    Loaders are responsible for persisting transformed data to the
    target destination (database, file, API, etc.).
    """

    @abstractmethod
    async def load(
        self, records: list[dict[str, Any]], context: PipelineContext
    ) -> int:
        """Load the transformed data to the destination.

        Args:
            records: List of transformed records to load
            context: Pipeline context

        Returns:
            Number of records successfully loaded
        """
        pass

    async def execute(
        self, data: list[dict[str, Any]], context: PipelineContext
    ) -> StepResult[int]:
        """Execute the loading step."""
        start_time = datetime.now()
        try:
            count = await self.load(data, context)
            return StepResult(
                status=StepStatus.SUCCESS,
                data=count,
                records_processed=count,
                start_time=start_time,
                end_time=datetime.now(),
            )
        except Exception as e:
            return StepResult(
                status=StepStatus.FAILED,
                error=str(e),
                error_details={"exception_type": type(e).__name__},
                start_time=start_time,
                end_time=datetime.now(),
            )
