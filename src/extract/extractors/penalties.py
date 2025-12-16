"""Penalties extractor for FWC API"""

from typing import Any, Dict, List, Optional

from src.core.interfaces import Extractor, PipelineContext
from src.extract.api_client import APIClient
from src.extract.paginator import Paginator
from src.utils.logging import get_logger

logger = get_logger(__name__)


class PenaltiesExtractor(Extractor):
    """Extract penalties data from FWC API"""

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
        return "penalties_extractor"

    async def extract(self, context: PipelineContext) -> List[Dict[str, Any]]:
        """Extract penalties from FWC API"""
        logger.info("extracting_penalties")

        # Get award codes from context if not provided
        award_codes = self.award_codes
        if not award_codes:
            # Try to get from extracted awards
            awards = context.data.get("awards_extractor", [])
            award_codes = [a.get("code") for a in awards if a.get("code")]

        if not award_codes:
            logger.warning("no_award_codes_for_penalties")
            return []

        all_penalties: List[Dict[str, Any]] = []

        for award_code in award_codes:
            logger.debug(
                "extracting_award_penalties",
                award_code=award_code,
            )

            paginator = Paginator(
                fetch_func=lambda **kw: self.api_client.get_penalties(award_code, **kw),
                page_size=self.page_size,
            )

            try:
                penalties = await paginator.fetch_all()
                # Add award_code to each record
                for penalty in penalties:
                    penalty["award_code"] = award_code
                all_penalties.extend(penalties)
                
                logger.info(
                    "penalties_extracted_for_award",
                    award_code=award_code,
                    count=len(penalties),
                )
            except Exception as e:
                logger.error(
                    "penalties_extraction_error",
                    award_code=award_code,
                    error=str(e),
                )
                context.add_warning(
                    f"Failed to extract penalties for {award_code}: {e}"
                )

        logger.info(
            "penalties_extracted",
            count=len(all_penalties),
            awards_processed=len(award_codes),
        )

        context.set_metadata("raw_penalties_count", len(all_penalties))

        return all_penalties
