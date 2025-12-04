"""Interface definitions for ETL Pipeline components"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


class StepStatus(str, Enum):
    """Status of a pipeline step"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    """Result of a pipeline step execution"""

    status: StepStatus
    records_processed: int = 0
    records_failed: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class PipelineStep(ABC):
    """Base class for all pipeline steps"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this step"""
        pass

    @abstractmethod
    async def execute(self, context: "PipelineContext") -> StepResult:
        """Execute the pipeline step"""
        pass


class Extractor(PipelineStep):
    """Base class for data extractors"""

    @abstractmethod
    async def extract(self, context: "PipelineContext") -> List[Dict[str, Any]]:
        """Extract data from source"""
        pass

    async def execute(self, context: "PipelineContext") -> StepResult:
        """Execute extraction and return result"""
        from datetime import datetime

        start_time = datetime.utcnow()
        try:
            data = await self.extract(context)
            context.data[self.name] = data
            return StepResult(
                status=StepStatus.COMPLETED,
                records_processed=len(data),
                start_time=start_time,
                end_time=datetime.utcnow(),
            )
        except Exception as e:
            return StepResult(
                status=StepStatus.FAILED,
                start_time=start_time,
                end_time=datetime.utcnow(),
                error_message=str(e),
            )


class Transformer(PipelineStep):
    """Base class for data transformers"""

    @property
    @abstractmethod
    def source_key(self) -> str:
        """Key to read data from context"""
        pass

    @property
    def target_key(self) -> str:
        """Key to store transformed data in context"""
        return f"{self.source_key}_transformed"

    @abstractmethod
    async def transform(
        self, data: List[Dict[str, Any]], context: "PipelineContext"
    ) -> List[Dict[str, Any]]:
        """Transform the data"""
        pass

    async def execute(self, context: "PipelineContext") -> StepResult:
        """Execute transformation and return result"""
        from datetime import datetime

        start_time = datetime.utcnow()
        try:
            source_data = context.data.get(self.source_key, [])
            if not source_data:
                return StepResult(
                    status=StepStatus.SKIPPED,
                    start_time=start_time,
                    end_time=datetime.utcnow(),
                    details={"reason": f"No data found for key '{self.source_key}'"},
                )

            transformed = await self.transform(source_data, context)
            context.data[self.target_key] = transformed
            return StepResult(
                status=StepStatus.COMPLETED,
                records_processed=len(transformed),
                start_time=start_time,
                end_time=datetime.utcnow(),
            )
        except Exception as e:
            return StepResult(
                status=StepStatus.FAILED,
                start_time=start_time,
                end_time=datetime.utcnow(),
                error_message=str(e),
            )


class Loader(PipelineStep):
    """Base class for data loaders"""

    @property
    @abstractmethod
    def source_key(self) -> str:
        """Key to read data from context"""
        pass

    @abstractmethod
    async def load(
        self, data: List[Dict[str, Any]], context: "PipelineContext"
    ) -> int:
        """Load data to target. Returns number of records loaded."""
        pass

    async def execute(self, context: "PipelineContext") -> StepResult:
        """Execute loading and return result"""
        from datetime import datetime

        start_time = datetime.utcnow()
        try:
            source_data = context.data.get(self.source_key, [])
            if not source_data:
                return StepResult(
                    status=StepStatus.SKIPPED,
                    start_time=start_time,
                    end_time=datetime.utcnow(),
                    details={"reason": f"No data found for key '{self.source_key}'"},
                )

            records_loaded = await self.load(source_data, context)
            return StepResult(
                status=StepStatus.COMPLETED,
                records_processed=records_loaded,
                start_time=start_time,
                end_time=datetime.utcnow(),
            )
        except Exception as e:
            return StepResult(
                status=StepStatus.FAILED,
                start_time=start_time,
                end_time=datetime.utcnow(),
                error_message=str(e),
            )


@dataclass
class PipelineContext:
    """Context passed through pipeline steps"""

    job_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Add an error message"""
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """Add a warning message"""
        self.warnings.append(message)

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value"""
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value"""
        return self.metadata.get(key, default)
