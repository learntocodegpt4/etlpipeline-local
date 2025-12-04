"""Base transformer class for data transformation."""

from abc import abstractmethod
from datetime import datetime
from typing import Any

import structlog

from src.core.interfaces import PipelineContext, StepResult, StepStatus, Transformer

logger = structlog.get_logger(__name__)


class BaseTransformer(Transformer):
    """Base class for data transformers.

    Provides common functionality for transforming extracted data
    including validation, type conversion, and null handling.
    """

    def __init__(self, validate_input: bool = True, validate_output: bool = True):
        super().__init__()
        self.validate_input = validate_input
        self.validate_output = validate_output
        self._logger = logger.bind(transformer=self.__class__.__name__)

    @property
    @abstractmethod
    def output_schema(self) -> dict[str, type]:
        """Define the expected output schema.

        Returns:
            Dictionary mapping field names to expected types
        """
        pass

    @abstractmethod
    async def _transform_record(
        self,
        record: dict[str, Any],
        context: PipelineContext,
    ) -> dict[str, Any]:
        """Transform a single record.

        Must be implemented by subclasses.

        Args:
            record: Raw record from extraction
            context: Pipeline context

        Returns:
            Transformed record
        """
        pass

    async def transform(
        self,
        records: list[dict[str, Any]],
        context: PipelineContext,
    ) -> list[dict[str, Any]]:
        """Transform all records.

        Args:
            records: List of raw records
            context: Pipeline context

        Returns:
            List of transformed records
        """
        self._logger.info(
            "transformation_started",
            input_count=len(records),
        )

        transformed: list[dict[str, Any]] = []
        errors: list[str] = []

        for i, record in enumerate(records):
            try:
                result = await self._transform_record(record, context)
                if result:
                    transformed.append(result)
            except Exception as e:
                error_msg = f"Record {i} transformation failed: {e}"
                errors.append(error_msg)
                self._logger.warning(
                    "record_transformation_error",
                    record_index=i,
                    error=str(e),
                )

        if errors:
            context.metadata["transform_errors"] = errors

        self._logger.info(
            "transformation_completed",
            input_count=len(records),
            output_count=len(transformed),
            error_count=len(errors),
        )

        return transformed

    async def execute(
        self, data: list[dict[str, Any]], context: PipelineContext
    ) -> StepResult[list[dict[str, Any]]]:
        """Execute the transformation step with error handling."""
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
            self._logger.exception(
                "transformation_error",
                error=str(e),
            )
            return StepResult(
                status=StepStatus.FAILED,
                error=str(e),
                error_details={"exception_type": type(e).__name__},
                start_time=start_time,
                end_time=datetime.now(),
            )

    @staticmethod
    def convert_datetime(value: Any) -> datetime | None:
        """Convert various datetime formats to datetime object."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            # Try ISO format first
            for fmt in [
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d",
            ]:
                try:
                    return datetime.strptime(value.split("+")[0].split(".")[0], fmt.replace("%z", ""))
                except ValueError:
                    continue
        return None

    @staticmethod
    def convert_decimal(value: Any) -> float | None:
        """Convert value to decimal/float."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def convert_int(value: Any) -> int | None:
        """Convert value to integer."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def clean_string(value: Any) -> str | None:
        """Clean and normalize string values."""
        if value is None:
            return None
        result = str(value).strip()
        return result if result else None
