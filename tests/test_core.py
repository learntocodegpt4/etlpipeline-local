"""Tests for the core pipeline module."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_pipeline_context():
    """Test PipelineContext functionality."""
    from src.core.interfaces import PipelineContext, StepResult, StepStatus

    context = PipelineContext(
        job_id="test_job_123",
        started_at=datetime.now(),
        parameters={"award_code": "MA000001"},
    )

    assert context.job_id == "test_job_123"
    assert context.parameters["award_code"] == "MA000001"
    assert not context.has_errors

    # Add error
    context.add_error("Test error")
    assert context.has_errors
    assert "Test error" in context.errors


@pytest.mark.asyncio
async def test_step_result():
    """Test StepResult functionality."""
    from src.core.interfaces import StepResult, StepStatus

    start = datetime.now()
    result = StepResult(
        status=StepStatus.SUCCESS,
        data={"count": 10},
        records_processed=10,
        start_time=start,
        end_time=datetime.now(),
    )

    assert result.status == StepStatus.SUCCESS
    assert result.data == {"count": 10}
    assert result.records_processed == 10
    assert result.duration_seconds is not None


@pytest.mark.asyncio
async def test_pipeline_builder():
    """Test PipelineBuilder."""
    from src.core.pipeline import PipelineBuilder
    from src.core.interfaces import Extractor, Transformer, Loader, PipelineContext

    # Create mock components
    class MockExtractor(Extractor):
        async def extract(self, params, context):
            return [{"id": 1}]

    class MockTransformer(Transformer):
        async def transform(self, records, context):
            return records

    class MockLoader(Loader):
        async def load(self, records, context):
            return len(records)

    # Build pipeline
    pipeline = (
        PipelineBuilder("test_pipeline")
        .with_extractor(MockExtractor())
        .with_transformer(MockTransformer())
        .with_loader(MockLoader())
        .build()
    )

    assert pipeline.name == "test_pipeline"
    assert pipeline.extractor is not None
    assert pipeline.transformer is not None
    assert pipeline.loader is not None


@pytest.mark.asyncio
async def test_pipeline_builder_missing_components():
    """Test PipelineBuilder raises error for missing components."""
    from src.core.pipeline import PipelineBuilder

    with pytest.raises(ValueError, match="Extractor is required"):
        PipelineBuilder("test").build()
