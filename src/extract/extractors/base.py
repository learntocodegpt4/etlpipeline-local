"""Base extractor class for FWC API endpoints."""

import json
from abc import abstractmethod
from datetime import datetime
from typing import Any

import structlog

from src.core.interfaces import Extractor, PipelineContext, StepResult, StepStatus
from src.extract.api_client import FWCAPIClient

logger = structlog.get_logger(__name__)


class BaseFWCExtractor(Extractor):
    """Base class for FWC API extractors.

    Provides common functionality for extracting data from FWC API
    endpoints with pagination, error handling, and raw response storage.
    """

    def __init__(
        self,
        client: FWCAPIClient | None = None,
        page_size: int = 100,
        store_raw_response: bool = True,
    ):
        super().__init__()
        self._client = client
        self.page_size = page_size
        self.store_raw_response = store_raw_response
        self._logger = logger.bind(extractor=self.__class__.__name__)

    @property
    def client(self) -> FWCAPIClient:
        """Get or create the API client."""
        if self._client is None:
            self._client = FWCAPIClient()
        return self._client

    @abstractmethod
    async def _fetch_data(
        self,
        params: dict[str, Any],
        context: PipelineContext,
    ) -> list[dict[str, Any]]:
        """Fetch data from the API endpoint.

        Must be implemented by subclasses.

        Args:
            params: Parameters for the extraction
            context: Pipeline context

        Returns:
            List of extracted records
        """
        pass

    @property
    @abstractmethod
    def endpoint_name(self) -> str:
        """Name of the endpoint for logging and metadata."""
        pass

    async def extract(
        self,
        params: dict[str, Any],
        context: PipelineContext,
    ) -> list[dict[str, Any]]:
        """Extract data from the FWC API.

        Args:
            params: Extraction parameters
            context: Pipeline context

        Returns:
            List of extracted records
        """
        self._logger.info(
            "extraction_started",
            endpoint=self.endpoint_name,
            params=params,
        )

        async with FWCAPIClient() as client:
            self._client = client
            records = await self._fetch_data(params, context)

        # Store raw response in context metadata
        if self.store_raw_response:
            context.metadata[f"raw_{self.endpoint_name}"] = json.dumps(
                records, default=str
            )

        self._logger.info(
            "extraction_completed",
            endpoint=self.endpoint_name,
            record_count=len(records),
        )

        return records

    async def execute(
        self, data: dict[str, Any], context: PipelineContext
    ) -> StepResult[list[dict[str, Any]]]:
        """Execute the extraction step with enhanced error handling."""
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
            self._logger.exception(
                "extraction_error",
                endpoint=self.endpoint_name,
                error=str(e),
            )
            return StepResult(
                status=StepStatus.FAILED,
                error=str(e),
                error_details={
                    "exception_type": type(e).__name__,
                    "endpoint": self.endpoint_name,
                },
                start_time=start_time,
                end_time=datetime.now(),
            )
