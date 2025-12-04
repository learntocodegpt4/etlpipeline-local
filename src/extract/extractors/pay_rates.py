"""Pay rates extractor for FWC API."""

from typing import Any

import structlog

from src.core.interfaces import PipelineContext
from src.extract.extractors.base import BaseFWCExtractor
from src.extract.paginator import Paginator

logger = structlog.get_logger(__name__)


class PayRatesExtractor(BaseFWCExtractor):
    """Extractor for FWC Pay Rates endpoint.

    Fetches pay rates for a specific award from the
    /api/v1/awards/{award_code}/pay-rates endpoint.
    """

    @property
    def endpoint_name(self) -> str:
        return "pay_rates"

    async def _fetch_data(
        self,
        params: dict[str, Any],
        context: PipelineContext,
    ) -> list[dict[str, Any]]:
        """Fetch pay rates for an award.

        Args:
            params: Must include 'award_code' parameter
            context: Pipeline context

        Returns:
            List of pay rate records
        """
        award_code = params.get("award_code")
        if not award_code:
            raise ValueError("award_code is required for pay rates extraction")

        async def fetch_page(page: int = 1, limit: int = 100, **kwargs: Any) -> dict[str, Any]:
            return await self.client.get_pay_rates(
                award_code=award_code,
                page=page,
                limit=limit,
                **kwargs,
            )

        paginator = Paginator(
            fetch_page,
            page_size=self.page_size,
        )

        # Extract additional filters
        filters = {
            k: v
            for k, v in params.items()
            if k not in ["page", "limit", "award_code"]
        }

        records = await paginator.fetch_all(**filters)

        # Add award_code to each record for reference
        for record in records:
            record["award_code"] = award_code

        self._logger.info(
            "pay_rates_extracted",
            award_code=award_code,
            total_pay_rates=len(records),
        )

        return records
