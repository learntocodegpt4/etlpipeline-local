"""Expense allowances extractor for FWC API."""

from typing import Any

import structlog

from src.core.interfaces import PipelineContext
from src.extract.extractors.base import BaseFWCExtractor
from src.extract.paginator import Paginator

logger = structlog.get_logger(__name__)


class ExpenseAllowancesExtractor(BaseFWCExtractor):
    """Extractor for FWC Expense Allowances endpoint.

    Fetches expense allowances for a specific award from the
    /api/v1/awards/{award_code}/expense-allowances endpoint.
    """

    @property
    def endpoint_name(self) -> str:
        return "expense_allowances"

    async def _fetch_data(
        self,
        params: dict[str, Any],
        context: PipelineContext,
    ) -> list[dict[str, Any]]:
        """Fetch expense allowances for an award.

        Args:
            params: Must include 'award_code' parameter
            context: Pipeline context

        Returns:
            List of expense allowance records
        """
        award_code = params.get("award_code")
        if not award_code:
            raise ValueError("award_code is required for expense allowances extraction")

        async def fetch_page(page: int = 1, limit: int = 100, **kwargs: Any) -> dict[str, Any]:
            return await self.client.get_expense_allowances(
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
            "expense_allowances_extracted",
            award_code=award_code,
            total_expense_allowances=len(records),
        )

        return records
