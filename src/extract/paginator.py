"""Pagination handler for FWC API responses"""

from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


class Paginator:
    """Handle pagination for FWC API responses"""

    def __init__(
        self,
        fetch_func: Callable[..., Any],
        page_size: int = 100,
        max_pages: Optional[int] = None,
    ):
        """
        Initialize paginator.

        Args:
            fetch_func: Async function to fetch data (must accept page and limit params)
            page_size: Number of records per page
            max_pages: Maximum number of pages to fetch (None for all)
        """
        self.fetch_func = fetch_func
        self.page_size = page_size
        self.max_pages = max_pages

    async def fetch_all(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """Fetch all pages and return combined results"""
        all_results: List[Dict[str, Any]] = []
        page = 1

        while True:
            # Check max pages limit
            if self.max_pages and page > self.max_pages:
                logger.info(
                    "pagination_max_pages_reached",
                    max_pages=self.max_pages,
                    total_records=len(all_results),
                )
                break

            # Fetch current page
            response = await self.fetch_func(
                page=page,
                limit=self.page_size,
                **kwargs,
            )

            # Extract results from response
            results = self._extract_results(response)
            if not results:
                break

            all_results.extend(results)

            # Check if there are more pages
            meta = response.get("_meta", {})
            has_more = meta.get("has_more_results", False)

            logger.debug(
                "pagination_page_fetched",
                page=page,
                records=len(results),
                total=len(all_results),
                has_more=has_more,
            )

            if not has_more:
                break

            page += 1

        logger.info(
            "pagination_complete",
            total_pages=page,
            total_records=len(all_results),
        )

        return all_results

    async def fetch_pages(self, **kwargs: Any) -> AsyncIterator[List[Dict[str, Any]]]:
        """Yield results page by page"""
        page = 1

        while True:
            # Check max pages limit
            if self.max_pages and page > self.max_pages:
                break

            # Fetch current page
            response = await self.fetch_func(
                page=page,
                limit=self.page_size,
                **kwargs,
            )

            # Extract results from response
            results = self._extract_results(response)
            if not results:
                break

            yield results

            # Check if there are more pages
            meta = response.get("_meta", {})
            has_more = meta.get("has_more_results", False)

            if not has_more:
                break

            page += 1

    def _extract_results(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract results from API response"""
        # FWC API returns results in different keys depending on endpoint
        # Check common patterns
        if "results" in response:
            return response["results"]
        if "data" in response:
            return response["data"]

        # If response is a list, return it directly
        if isinstance(response, list):
            return response

        return []


class PaginationMeta:
    """Pagination metadata from API response"""

    def __init__(self, meta: Dict[str, Any]):
        self.current_page = meta.get("current_page", 1)
        self.page_count = meta.get("page_count", 1)
        self.limit = meta.get("limit", 100)
        self.result_count = meta.get("result_count", 0)
        self.first_row_on_page = meta.get("first_row_on_page", 1)
        self.last_row_on_page = meta.get("last_row_on_page", 0)
        self.has_more_results = meta.get("has_more_results", False)
        self.has_previous_results = meta.get("has_previous_results", False)

    def __repr__(self) -> str:
        return (
            f"PaginationMeta(page={self.current_page}/{self.page_count}, "
            f"results={self.result_count}, has_more={self.has_more_results})"
        )
