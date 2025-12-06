"""Data validation utilities"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set


@dataclass
class ValidationResult:
    """Result of data validation"""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class FieldValidator:
    """Validator for a single field"""

    def __init__(
        self,
        field_name: str,
        required: bool = False,
        field_type: Optional[type] = None,
        allowed_values: Optional[Set[Any]] = None,
        min_value: Optional[Any] = None,
        max_value: Optional[Any] = None,
        max_length: Optional[int] = None,
        custom_validator: Optional[Callable[[Any], bool]] = None,
        custom_message: Optional[str] = None,
    ):
        self.field_name = field_name
        self.required = required
        self.field_type = field_type
        self.allowed_values = allowed_values
        self.min_value = min_value
        self.max_value = max_value
        self.max_length = max_length
        self.custom_validator = custom_validator
        self.custom_message = custom_message

    def validate(self, value: Any) -> ValidationResult:
        """Validate a field value"""
        errors: List[str] = []
        warnings: List[str] = []

        # Check required
        if value is None:
            if self.required:
                errors.append(f"Field '{self.field_name}' is required")
            return ValidationResult(is_valid=len(errors) == 0, errors=errors)

        # Check type
        if self.field_type and not isinstance(value, self.field_type):
            # Try to convert numeric types
            if self.field_type in (int, float):
                try:
                    self.field_type(value)
                except (ValueError, TypeError):
                    errors.append(
                        f"Field '{self.field_name}' must be of type {self.field_type.__name__}"
                    )

        # Check allowed values
        if self.allowed_values and value not in self.allowed_values:
            errors.append(
                f"Field '{self.field_name}' must be one of: {self.allowed_values}"
            )

        # Check min/max values
        if self.min_value is not None:
            try:
                if value < self.min_value:
                    errors.append(
                        f"Field '{self.field_name}' must be >= {self.min_value}"
                    )
            except TypeError:
                pass

        if self.max_value is not None:
            try:
                if value > self.max_value:
                    errors.append(
                        f"Field '{self.field_name}' must be <= {self.max_value}"
                    )
            except TypeError:
                pass

        # Check max length
        if self.max_length and isinstance(value, str) and len(value) > self.max_length:
            warnings.append(
                f"Field '{self.field_name}' exceeds max length {self.max_length}"
            )

        # Custom validator
        if self.custom_validator and not self.custom_validator(value):
            errors.append(
                self.custom_message or f"Field '{self.field_name}' failed custom validation"
            )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


class DataValidator:
    """Validator for data records"""

    def __init__(self, validators: Optional[List[FieldValidator]] = None):
        self.validators: Dict[str, FieldValidator] = {}
        if validators:
            for v in validators:
                self.validators[v.field_name] = v

    def add_validator(self, validator: FieldValidator) -> "DataValidator":
        """Add a field validator"""
        self.validators[validator.field_name] = validator
        return self

    def validate(self, record: Dict[str, Any]) -> ValidationResult:
        """Validate a data record"""
        all_errors: List[str] = []
        all_warnings: List[str] = []

        for field_name, validator in self.validators.items():
            value = record.get(field_name)
            result = validator.validate(value)
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)

        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
        )

    def validate_batch(
        self, records: List[Dict[str, Any]]
    ) -> Dict[int, ValidationResult]:
        """Validate multiple records"""
        results: Dict[int, ValidationResult] = {}
        for i, record in enumerate(records):
            results[i] = self.validate(record)
        return results
