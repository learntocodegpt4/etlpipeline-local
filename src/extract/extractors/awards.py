"""Awards extractor for FWC API"""

from typing import Any, Dict, List

from src.core.interfaces import Extractor, PipelineContext
from src.extract.api_client import APIClient
from src.extract.paginator import Paginator
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AwardsExtractor(Extractor):
    """Extract awards data from FWC API"""

    def __init__(
        self,
        api_client: APIClient,
        page_size: int = 100,
    ):
        self.api_client = api_client
        self.page_size = page_size

    @property
    def name(self) -> str:
        return "awards_extractor"

    async def extract(self, context: PipelineContext) -> List[Dict[str, Any]]:
        """Extract all awards from FWC API"""
        logger.info("extracting_awards")

        paginator = Paginator(
            fetch_func=self.api_client.get_awards,
            page_size=self.page_size,
        )

        awards = await paginator.fetch_all()

        logger.info(
            "awards_extracted",
            count=len(awards),
        )

        # Store raw response in context for archival
        context.set_metadata("raw_awards_count", len(awards))

        return awards
