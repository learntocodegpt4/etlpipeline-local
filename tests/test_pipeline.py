"""Tests for ETL Pipeline"""

import pytest
from datetime import datetime


class TestSettings:
    """Tests for configuration settings"""

    def test_settings_import(self):
        """Test that settings can be imported"""
        from src.config.settings import Settings, get_settings
        settings = get_settings()
        assert settings is not None
        assert settings.fwc_api_base_url == "https://api.fwc.gov.au/api/v1"

    def test_default_values(self):
        """Test default configuration values"""
        from src.config.settings import get_settings
        settings = get_settings()
        assert settings.api_port == 8000
        assert settings.mssql_port == 1433
        assert settings.default_page_size == 100


class TestAPIEndpoints:
    """Tests for API endpoint configuration"""

    def test_awards_endpoint(self):
        """Test awards endpoint URL"""
        from src.config.api_endpoints import APIEndpoints
        endpoints = APIEndpoints()
        assert endpoints.awards == "https://api.fwc.gov.au/api/v1/awards"

    def test_classifications_endpoint(self):
        """Test classifications endpoint URL"""
        from src.config.api_endpoints import APIEndpoints
        endpoints = APIEndpoints()
        url = endpoints.classifications("MA000001")
        assert url == "https://api.fwc.gov.au/api/v1/awards/MA000001/classifications"

    def test_pay_rates_endpoint(self):
        """Test pay rates endpoint URL"""
        from src.config.api_endpoints import APIEndpoints
        endpoints = APIEndpoints()
        url = endpoints.pay_rates("MA000001")
        assert url == "https://api.fwc.gov.au/api/v1/awards/MA000001/pay-rates"


class TestHelpers:
    """Tests for helper utilities"""

    def test_parse_datetime(self):
        """Test datetime parsing"""
        from src.utils.helpers import parse_datetime
        
        result = parse_datetime("2024-01-15T10:30:00")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_datetime_with_timezone(self):
        """Test datetime parsing with timezone"""
        from src.utils.helpers import parse_datetime
        
        result = parse_datetime("2024-01-15T10:30:00+00:00")
        assert result is not None

    def test_safe_float(self):
        """Test safe float conversion"""
        from src.utils.helpers import safe_float
        
        assert safe_float("3.14") == 3.14
        assert safe_float(None) is None
        assert safe_float("invalid", 0.0) == 0.0

    def test_safe_int(self):
        """Test safe integer conversion"""
        from src.utils.helpers import safe_int
        
        assert safe_int("42") == 42
        assert safe_int(None) is None
        assert safe_int("invalid", -1) == -1

    def test_chunk_list(self):
        """Test list chunking"""
        from src.utils.helpers import chunk_list
        
        data = [1, 2, 3, 4, 5]
        chunks = chunk_list(data, 2)
        assert len(chunks) == 3
        assert chunks[0] == [1, 2]
        assert chunks[1] == [3, 4]
        assert chunks[2] == [5]


class TestPipelineInterfaces:
    """Tests for pipeline interfaces"""

    def test_step_status_enum(self):
        """Test step status enumeration"""
        from src.core.interfaces import StepStatus
        
        assert StepStatus.PENDING.value == "pending"
        assert StepStatus.COMPLETED.value == "completed"
        assert StepStatus.FAILED.value == "failed"

    def test_step_result(self):
        """Test step result creation"""
        from src.core.interfaces import StepResult, StepStatus
        
        result = StepResult(
            status=StepStatus.COMPLETED,
            records_processed=100,
        )
        assert result.status == StepStatus.COMPLETED
        assert result.records_processed == 100

    def test_pipeline_context(self):
        """Test pipeline context"""
        from src.core.interfaces import PipelineContext
        
        context = PipelineContext(job_id="test-job-123")
        assert context.job_id == "test-job-123"
        assert context.data == {}
        
        context.add_error("Test error")
        assert len(context.errors) == 1
        
        context.set_metadata("key", "value")
        assert context.get_metadata("key") == "value"


class TestTransformers:
    """Tests for data transformers"""

    def test_awards_transformer(self):
        """Test awards transformer"""
        from src.transform.transformers.awards import AwardsTransformer
        from src.core.interfaces import PipelineContext
        
        transformer = AwardsTransformer()
        context = PipelineContext(job_id="test")
        
        record = {
            "award_id": 1752,
            "award_fixed_id": 1,
            "code": "MA000001",
            "name": "Black Coal Mining Industry Award 2020",
            "award_operative_from": "2010-01-01",
            "published_year": 2025,
        }
        
        result = transformer.transform_record(record, context)
        assert result is not None
        assert result["code"] == "MA000001"
        assert result["award_id"] == 1752

    def test_classifications_transformer(self):
        """Test classifications transformer"""
        from src.transform.transformers.classifications import ClassificationsTransformer
        from src.core.interfaces import PipelineContext
        
        transformer = ClassificationsTransformer()
        context = PipelineContext(job_id="test")
        
        record = {
            "classification_fixed_id": 100,
            "award_code": "MA000001",
            "classification": "Level 1",
            "classification_level": 1,
        }
        
        result = transformer.transform_record(record, context)
        assert result is not None
        assert result["classification_fixed_id"] == 100
        assert result["award_code"] == "MA000001"


class TestValidators:
    """Tests for data validators"""

    def test_field_validator(self):
        """Test field validator"""
        from src.transform.validators import FieldValidator
        
        validator = FieldValidator("name", required=True)
        
        result = validator.validate("Test Name")
        assert result.is_valid
        
        result = validator.validate(None)
        assert not result.is_valid
        assert len(result.errors) > 0

    def test_data_validator(self):
        """Test data validator"""
        from src.transform.validators import DataValidator, FieldValidator
        
        validator = DataValidator([
            FieldValidator("id", required=True),
            FieldValidator("name", required=True),
        ])
        
        valid_record = {"id": 1, "name": "Test"}
        result = validator.validate(valid_record)
        assert result.is_valid
        
        invalid_record = {"id": 1}
        result = validator.validate(invalid_record)
        assert not result.is_valid
