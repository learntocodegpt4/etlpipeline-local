"""Pay rates extractor for FWC API"""

from typing import Any, Dict, List, Optional

from src.core.interfaces import Extractor, PipelineContext
from src.extract.api_client import APIClient
from src.extract.paginator import Paginator
from src.utils.logging import get_logger

logger = get_logger(__name__)


class PayRatesExtractor(Extractor):
    """Extract pay rates data from FWC API"""

    def __init__(
        self,
        api_client: APIClient,
        award_codes: Optional[List[str]] = None,
        page_size: int = 100,
    ):
        self.api_client = api_client
        self.award_codes = award_codes
        self.page_size = page_size

    @property
    def name(self) -> str:
        return "pay_rates_extractor"

    async def extract(self, context: PipelineContext) -> List[Dict[str, Any]]:
        """Extract pay rates from FWC API"""
        logger.info("extracting_pay_rates")

        # Get award codes from context if not provided
        award_codes = self.award_codes
        if not award_codes:
            # Try to get from extracted awards
            awards = context.data.get("awards_extractor", [])
            award_codes = [a.get("code") for a in awards if a.get("code")]

        if not award_codes:
            logger.warning("no_award_codes_for_pay_rates")
            return []

        all_pay_rates: List[Dict[str, Any]] = []

        for award_code in award_codes:
            logger.debug(
                "extracting_award_pay_rates",
                award_code=award_code,
            )

            paginator = Paginator(
                fetch_func=lambda **kw: self.api_client.get_pay_rates(award_code, **kw),
                page_size=self.page_size,
            )

            try:
                pay_rates = await paginator.fetch_all()
                # Add award_code to each record
                for pr in pay_rates:
                    pr["award_code"] = award_code
                all_pay_rates.extend(pay_rates)
            except Exception as e:
                logger.error(
                    "pay_rates_extraction_error",
                    award_code=award_code,
                    error=str(e),
                )
                context.add_warning(
                    f"Failed to extract pay rates for {award_code}: {e}"
                )

        logger.info(
            "pay_rates_extracted",
            count=len(all_pay_rates),
            awards_processed=len(award_codes),
        )

        context.set_metadata("raw_pay_rates_count", len(all_pay_rates))

        return all_pay_rates
