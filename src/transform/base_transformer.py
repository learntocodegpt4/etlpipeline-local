"""Base transformer class for data transformation"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Type

from src.core.interfaces import Transformer, PipelineContext
from src.transform.validators import DataValidator, ValidationResult
from src.utils.logging import get_logger
from src.utils.helpers import parse_datetime, safe_float, safe_int, safe_bool

logger = get_logger(__name__)


class BaseTransformer(Transformer):
    """Base class for data transformers with validation and type conversion"""

    def __init__(
        self,
        source_key: str,
        validator: Optional[DataValidator] = None,
        skip_invalid: bool = True,
    ):
        self._source_key = source_key
        self.validator = validator
        self.skip_invalid = skip_invalid

    @property
    def source_key(self) -> str:
        return self._source_key

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this transformer"""
        pass

    @abstractmethod
    def transform_record(
        self, record: Dict[str, Any], context: PipelineContext
    ) -> Optional[Dict[str, Any]]:
        """Transform a single record. Return None to skip the record."""
        pass

    async def transform(
        self, data: List[Dict[str, Any]], context: PipelineContext
    ) -> List[Dict[str, Any]]:
        """Transform all records"""
        logger.info(
            "transform_started",
            transformer=self.name,
            input_count=len(data),
        )

        transformed: List[Dict[str, Any]] = []
        validation_errors = 0
        transform_errors = 0

        for i, record in enumerate(data):
            try:
                # Validate if validator is configured
                if self.validator:
                    result = self.validator.validate(record)
                    if not result.is_valid:
                        validation_errors += 1
                        if self.skip_invalid:
                            logger.debug(
                                "record_validation_failed",
                                index=i,
                                errors=result.errors,
                            )
                            continue
                        else:
                            context.add_warning(
                                f"Record {i} validation failed: {result.errors}"
                            )

                # Transform the record
                transformed_record = self.transform_record(record, context)
                if transformed_record is not None:
                    transformed.append(transformed_record)

            except Exception as e:
                transform_errors += 1
                logger.error(
                    "record_transform_error",
                    index=i,
                    error=str(e),
                )
                if not self.skip_invalid:
                    raise

        logger.info(
            "transform_completed",
            transformer=self.name,
            input_count=len(data),
            output_count=len(transformed),
            validation_errors=validation_errors,
            transform_errors=transform_errors,
        )

        return transformed

    # Helper methods for type conversion
    @staticmethod
    def to_datetime(value: Any) -> Optional[Any]:
        """Convert value to datetime"""
        return parse_datetime(value)

    @staticmethod
    def to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
        """Convert value to float"""
        return safe_float(value, default)

    @staticmethod
    def to_int(value: Any, default: Optional[int] = None) -> Optional[int]:
        """Convert value to integer"""
        return safe_int(value, default)

    @staticmethod
    def to_bool(value: Any, default: bool = False) -> bool:
        """Convert value to boolean"""
        return safe_bool(value, default)

    @staticmethod
    def to_string(
        value: Any, default: Optional[str] = None, max_length: Optional[int] = None
    ) -> Optional[str]:
        """Convert value to string"""
        if value is None:
            return default
        result = str(value).strip()
        if max_length and len(result) > max_length:
            result = result[:max_length]
        return result
