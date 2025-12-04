"""Data validation utilities for the transform module."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class ValidationError(Exception):
    """Exception raised for validation errors."""

    def __init__(self, message: str, field: str | None = None, value: Any = None):
        super().__init__(message)
        self.field = field
        self.value = value


@dataclass
class ValidationRule:
    """Represents a validation rule for a field."""

    name: str
    validator: Callable[[Any], bool]
    message: str
    required: bool = False


@dataclass
class FieldValidation:
    """Validation configuration for a field."""

    field_name: str
    required: bool = False
    data_type: type | None = None
    min_value: float | int | None = None
    max_value: float | int | None = None
    min_length: int | None = None
    max_length: int | None = None
    allowed_values: list[Any] | None = None
    pattern: str | None = None
    custom_validators: list[ValidationRule] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class DataValidator:
    """Validates data records against defined rules.

    Provides comprehensive validation capabilities including:
    - Type checking
    - Required field validation
    - Range validation
    - Pattern matching
    - Custom validators
    """

    def __init__(self):
        self._field_validations: dict[str, FieldValidation] = {}
        self._logger = logger.bind(component="data_validator")

    def add_field(
        self,
        field_name: str,
        required: bool = False,
        data_type: type | None = None,
        min_value: float | int | None = None,
        max_value: float | int | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        allowed_values: list[Any] | None = None,
        pattern: str | None = None,
    ) -> "DataValidator":
        """Add a field validation rule.

        Returns self for chaining.
        """
        self._field_validations[field_name] = FieldValidation(
            field_name=field_name,
            required=required,
            data_type=data_type,
            min_value=min_value,
            max_value=max_value,
            min_length=min_length,
            max_length=max_length,
            allowed_values=allowed_values,
            pattern=pattern,
        )
        return self

    def validate_record(self, record: dict[str, Any]) -> ValidationResult:
        """Validate a single record against all field rules.

        Args:
            record: Data record to validate

        Returns:
            ValidationResult with errors and warnings
        """
        errors: list[str] = []
        warnings: list[str] = []

        for field_name, validation in self._field_validations.items():
            value = record.get(field_name)

            # Required check
            if validation.required and value is None:
                errors.append(f"Field '{field_name}' is required but missing")
                continue

            if value is None:
                continue

            # Type check
            if validation.data_type and not isinstance(value, validation.data_type):
                # Try type conversion for common cases
                try:
                    if validation.data_type is int:
                        int(value)
                    elif validation.data_type is float:
                        float(value)
                    elif validation.data_type is str:
                        str(value)
                    elif validation.data_type is datetime and not isinstance(value, (datetime, str)):
                        errors.append(
                            f"Field '{field_name}' should be datetime, got {type(value).__name__}"
                        )
                except (ValueError, TypeError):
                    errors.append(
                        f"Field '{field_name}' should be {validation.data_type.__name__}, "
                        f"got {type(value).__name__}"
                    )

            # Range checks for numeric values
            if isinstance(value, (int, float)):
                if validation.min_value is not None and value < validation.min_value:
                    errors.append(
                        f"Field '{field_name}' value {value} is less than minimum {validation.min_value}"
                    )
                if validation.max_value is not None and value > validation.max_value:
                    errors.append(
                        f"Field '{field_name}' value {value} is greater than maximum {validation.max_value}"
                    )

            # Length checks for strings
            if isinstance(value, str):
                if validation.min_length is not None and len(value) < validation.min_length:
                    errors.append(
                        f"Field '{field_name}' length {len(value)} is less than minimum {validation.min_length}"
                    )
                if validation.max_length is not None and len(value) > validation.max_length:
                    errors.append(
                        f"Field '{field_name}' length {len(value)} exceeds maximum {validation.max_length}"
                    )

            # Allowed values check
            if validation.allowed_values is not None and value not in validation.allowed_values:
                errors.append(
                    f"Field '{field_name}' value '{value}' is not in allowed values: {validation.allowed_values}"
                )

            # Pattern check
            if validation.pattern is not None and isinstance(value, str):
                import re
                if not re.match(validation.pattern, value):
                    errors.append(
                        f"Field '{field_name}' value '{value}' does not match pattern '{validation.pattern}'"
                    )

            # Custom validators
            for rule in validation.custom_validators:
                try:
                    if not rule.validator(value):
                        if rule.required:
                            errors.append(f"Field '{field_name}': {rule.message}")
                        else:
                            warnings.append(f"Field '{field_name}': {rule.message}")
                except Exception as e:
                    warnings.append(f"Validator '{rule.name}' raised exception: {e}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def validate_records(
        self,
        records: list[dict[str, Any]],
        stop_on_first_error: bool = False,
    ) -> tuple[list[dict[str, Any]], list[tuple[int, ValidationResult]]]:
        """Validate multiple records.

        Args:
            records: List of records to validate
            stop_on_first_error: Whether to stop on first validation error

        Returns:
            Tuple of (valid_records, errors_with_indices)
        """
        valid_records: list[dict[str, Any]] = []
        errors: list[tuple[int, ValidationResult]] = []

        for i, record in enumerate(records):
            result = self.validate_record(record)
            if result.is_valid:
                valid_records.append(record)
            else:
                errors.append((i, result))
                if stop_on_first_error:
                    break

        self._logger.info(
            "validation_completed",
            total_records=len(records),
            valid_records=len(valid_records),
            invalid_records=len(errors),
        )

        return valid_records, errors
