"""Awards extractor for FWC API."""

from typing import Any

import structlog

from src.core.interfaces import PipelineContext
from src.extract.extractors.base import BaseFWCExtractor
from src.extract.paginator import Paginator

logger = structlog.get_logger(__name__)


class AwardsExtractor(BaseFWCExtractor):
    """Extractor for FWC Awards endpoint.

    Fetches all awards from the /api/v1/awards endpoint with
    automatic pagination.
    """

    @property
    def endpoint_name(self) -> str:
        return "awards"

    async def _fetch_data(
        self,
        params: dict[str, Any],
        context: PipelineContext,
    ) -> list[dict[str, Any]]:
        """Fetch all awards from the API.

        Args:
            params: Additional filter parameters
            context: Pipeline context

        Returns:
            List of award records
        """
        paginator = Paginator(
            self.client.get_awards,
            page_size=self.page_size,
        )

        # Extract any additional filters from params
        filters = {k: v for k, v in params.items() if k not in ["page", "limit"]}

        records = await paginator.fetch_all(**filters)

        self._logger.info(
            "awards_extracted",
            total_awards=len(records),
        )

        return records
