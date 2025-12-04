"""Pipeline orchestration for ETL processes.

This module provides the Pipeline and PipelineBuilder classes that
coordinate the execution of ETL steps in a reusable and portable manner.
"""

import asyncio
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

import structlog

from src.core.interfaces import (
    Extractor,
    Loader,
    PipelineContext,
    StepStatus,
    Transformer,
)

logger = structlog.get_logger(__name__)


class Pipeline:
    """Orchestrates the execution of ETL pipeline steps.

    The Pipeline class manages the sequential execution of extractors,
    transformers, and loaders, handling errors and state management.
    """

    def __init__(
        self,
        name: str,
        extractor: Extractor,
        transformer: Transformer,
        loader: Loader,
        pre_hooks: list[Callable[[PipelineContext], None]] | None = None,
        post_hooks: list[Callable[[PipelineContext], None]] | None = None,
    ):
        self.name = name
        self.extractor = extractor
        self.transformer = transformer
        self.loader = loader
        self.pre_hooks = pre_hooks or []
        self.post_hooks = post_hooks or []
        self._logger = logger.bind(pipeline=name)

    async def run(
        self,
        params: dict[str, Any] | None = None,
        job_id: str | None = None,
    ) -> PipelineContext:
        """Run the complete ETL pipeline.

        Args:
            params: Parameters passed to the extractor
            job_id: Optional job ID (generated if not provided)

        Returns:
            PipelineContext containing results and metadata
        """
        context = PipelineContext(
            job_id=job_id or str(uuid.uuid4()),
            started_at=datetime.now(),
            parameters=params or {},
        )

        self._logger.info(
            "pipeline_started",
            job_id=context.job_id,
            parameters=context.parameters,
        )

        # Execute pre-hooks
        for hook in self.pre_hooks:
            try:
                hook(context)
            except Exception as e:
                self._logger.warning("pre_hook_failed", error=str(e))

        try:
            # Extract
            self._logger.info("extract_started", extractor=self.extractor.name)
            extract_result = await self.extractor.execute(
                context.parameters, context
            )
            context.set_step_result("extract", extract_result)

            if extract_result.status != StepStatus.SUCCESS:
                self._logger.error(
                    "extract_failed",
                    error=extract_result.error,
                )
                return context

            self._logger.info(
                "extract_completed",
                records=extract_result.records_processed,
                duration=extract_result.duration_seconds,
            )

            # Transform
            self._logger.info("transform_started", transformer=self.transformer.name)
            transform_result = await self.transformer.execute(
                extract_result.data or [], context
            )
            context.set_step_result("transform", transform_result)

            if transform_result.status != StepStatus.SUCCESS:
                self._logger.error(
                    "transform_failed",
                    error=transform_result.error,
                )
                return context

            self._logger.info(
                "transform_completed",
                records=transform_result.records_processed,
                duration=transform_result.duration_seconds,
            )

            # Load
            self._logger.info("load_started", loader=self.loader.name)
            load_result = await self.loader.execute(
                transform_result.data or [], context
            )
            context.set_step_result("load", load_result)

            if load_result.status != StepStatus.SUCCESS:
                self._logger.error(
                    "load_failed",
                    error=load_result.error,
                )
                return context

            self._logger.info(
                "load_completed",
                records=load_result.records_processed,
                duration=load_result.duration_seconds,
            )

            self._logger.info(
                "pipeline_completed",
                job_id=context.job_id,
                total_records=load_result.records_processed,
            )

        except Exception as e:
            self._logger.exception("pipeline_error", error=str(e))
            context.add_error(str(e))

        # Execute post-hooks
        for hook in self.post_hooks:
            try:
                hook(context)
            except Exception as e:
                self._logger.warning("post_hook_failed", error=str(e))

        return context


class PipelineBuilder:
    """Builder for constructing Pipeline instances.

    Provides a fluent interface for building pipelines with
    customizable components and hooks.
    """

    def __init__(self, name: str):
        self._name = name
        self._extractor: Extractor | None = None
        self._transformer: Transformer | None = None
        self._loader: Loader | None = None
        self._pre_hooks: list[Callable[[PipelineContext], None]] = []
        self._post_hooks: list[Callable[[PipelineContext], None]] = []

    def with_extractor(self, extractor: Extractor) -> "PipelineBuilder":
        """Set the extractor for the pipeline."""
        self._extractor = extractor
        return self

    def with_transformer(self, transformer: Transformer) -> "PipelineBuilder":
        """Set the transformer for the pipeline."""
        self._transformer = transformer
        return self

    def with_loader(self, loader: Loader) -> "PipelineBuilder":
        """Set the loader for the pipeline."""
        self._loader = loader
        return self

    def add_pre_hook(
        self, hook: Callable[[PipelineContext], None]
    ) -> "PipelineBuilder":
        """Add a pre-execution hook."""
        self._pre_hooks.append(hook)
        return self

    def add_post_hook(
        self, hook: Callable[[PipelineContext], None]
    ) -> "PipelineBuilder":
        """Add a post-execution hook."""
        self._post_hooks.append(hook)
        return self

    def build(self) -> Pipeline:
        """Build the pipeline instance.

        Raises:
            ValueError: If required components are not set
        """
        if not self._extractor:
            raise ValueError("Extractor is required")
        if not self._transformer:
            raise ValueError("Transformer is required")
        if not self._loader:
            raise ValueError("Loader is required")

        return Pipeline(
            name=self._name,
            extractor=self._extractor,
            transformer=self._transformer,
            loader=self._loader,
            pre_hooks=self._pre_hooks,
            post_hooks=self._post_hooks,
        )


class ParallelPipeline:
    """Executes multiple pipelines in parallel."""

    def __init__(self, pipelines: list[Pipeline]):
        self.pipelines = pipelines

    async def run(
        self,
        params_list: list[dict[str, Any]] | None = None,
    ) -> list[PipelineContext]:
        """Run all pipelines in parallel.

        Args:
            params_list: List of parameters, one per pipeline

        Returns:
            List of PipelineContext results
        """
        params_list = params_list or [{}] * len(self.pipelines)

        tasks = [
            pipeline.run(params)
            for pipeline, params in zip(self.pipelines, params_list, strict=False)
        ]

        return await asyncio.gather(*tasks)
