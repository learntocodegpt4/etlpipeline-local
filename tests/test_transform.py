"""Tests for the transform module."""

import pytest
from datetime import datetime


class TestBaseTransformer:
    """Tests for BaseTransformer utility methods."""

    def test_convert_datetime_iso_format(self):
        """Test datetime conversion from ISO format."""
        from src.transform.base_transformer import BaseTransformer

        result = BaseTransformer.convert_datetime("2025-07-01T00:23:33+00:00")
        assert result is not None
        assert result.year == 2025
        assert result.month == 7
        assert result.day == 1

    def test_convert_datetime_date_only(self):
        """Test datetime conversion from date string."""
        from src.transform.base_transformer import BaseTransformer

        result = BaseTransformer.convert_datetime("2025-07-01")
        assert result is not None
        assert result.year == 2025
        assert result.month == 7
        assert result.day == 1

    def test_convert_datetime_none(self):
        """Test datetime conversion with None input."""
        from src.transform.base_transformer import BaseTransformer

        result = BaseTransformer.convert_datetime(None)
        assert result is None

    def test_convert_decimal(self):
        """Test decimal conversion."""
        from src.transform.base_transformer import BaseTransformer

        assert BaseTransformer.convert_decimal(1.5) == 1.5
        assert BaseTransformer.convert_decimal("2.5") == 2.5
        assert BaseTransformer.convert_decimal(None) is None

    def test_convert_int(self):
        """Test integer conversion."""
        from src.transform.base_transformer import BaseTransformer

        assert BaseTransformer.convert_int(123) == 123
        assert BaseTransformer.convert_int("456") == 456
        assert BaseTransformer.convert_int(None) is None

    def test_clean_string(self):
        """Test string cleaning."""
        from src.transform.base_transformer import BaseTransformer

        assert BaseTransformer.clean_string("  hello  ") == "hello"
        assert BaseTransformer.clean_string("") is None
        assert BaseTransformer.clean_string(None) is None


class TestDataValidator:
    """Tests for DataValidator."""

    def test_validate_required_field(self):
        """Test validation of required fields."""
        from src.transform.validators import DataValidator

        validator = DataValidator()
        validator.add_field("name", required=True)

        # Valid record
        result = validator.validate_record({"name": "test"})
        assert result.is_valid

        # Missing required field
        result = validator.validate_record({})
        assert not result.is_valid
        assert len(result.errors) == 1

    def test_validate_type(self):
        """Test type validation."""
        from src.transform.validators import DataValidator

        validator = DataValidator()
        validator.add_field("count", data_type=int)

        result = validator.validate_record({"count": 123})
        assert result.is_valid

    def test_validate_range(self):
        """Test range validation."""
        from src.transform.validators import DataValidator

        validator = DataValidator()
        validator.add_field("rate", min_value=0, max_value=100)

        # Valid
        result = validator.validate_record({"rate": 50})
        assert result.is_valid

        # Too low
        result = validator.validate_record({"rate": -1})
        assert not result.is_valid

        # Too high
        result = validator.validate_record({"rate": 101})
        assert not result.is_valid

    def test_validate_allowed_values(self):
        """Test allowed values validation."""
        from src.transform.validators import DataValidator

        validator = DataValidator()
        validator.add_field("status", allowed_values=["active", "inactive"])

        result = validator.validate_record({"status": "active"})
        assert result.is_valid

        result = validator.validate_record({"status": "unknown"})
        assert not result.is_valid
