"""Pagination handler for FWC API responses.

Handles automatic pagination to retrieve all records from paginated
API endpoints efficiently.
"""

from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class PaginationMeta:
    """Metadata from FWC API pagination response."""

    def __init__(self, meta: dict[str, Any]):
        self.current_page = meta.get("current_page", 1)
        self.page_count = meta.get("page_count", 1)
        self.limit = meta.get("limit", 100)
        self.result_count = meta.get("result_count", 0)
        self.first_row_on_page = meta.get("first_row_on_page", 1)
        self.last_row_on_page = meta.get("last_row_on_page", 0)
        self.has_more_results = meta.get("has_more_results", False)
        self.has_previous_results = meta.get("has_previous_results", False)

    @property
    def has_more(self) -> bool:
        """Check if there are more pages to fetch."""
        return self.has_more_results

    @property
    def next_page(self) -> int:
        """Get the next page number."""
        return self.current_page + 1


class Paginator:
    """Handles pagination for FWC API endpoints.

    Provides async iteration over paginated API responses,
    automatically fetching subsequent pages as needed.
    """

    def __init__(
        self,
        fetch_func: Callable[..., Coroutine[Any, Any, dict[str, Any]]],
        page_size: int = 100,
        max_pages: int | None = None,
    ):
        """Initialize the paginator.

        Args:
            fetch_func: Async function to fetch a page of data
            page_size: Number of records per page
            max_pages: Maximum number of pages to fetch (None for all)
        """
        self.fetch_func = fetch_func
        self.page_size = page_size
        self.max_pages = max_pages
        self._logger = logger.bind(component="paginator")

    async def fetch_all(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Fetch all records from the paginated endpoint.

        Args:
            **kwargs: Additional parameters to pass to fetch function

        Returns:
            List of all records from all pages
        """
        all_records: list[dict[str, Any]] = []
        pages_fetched = 0

        async for records in self.iterate(**kwargs):
            all_records.extend(records)
            pages_fetched += 1

        self._logger.info(
            "pagination_complete",
            total_records=len(all_records),
            pages_fetched=pages_fetched,
        )

        return all_records

    async def iterate(self, **kwargs: Any) -> AsyncIterator[list[dict[str, Any]]]:
        """Iterate over pages of results.

        Args:
            **kwargs: Additional parameters to pass to fetch function

        Yields:
            List of records for each page
        """
        page = 1
        has_more = True

        while has_more:
            if self.max_pages and page > self.max_pages:
                self._logger.info(
                    "max_pages_reached",
                    max_pages=self.max_pages,
                )
                break

            self._logger.debug(
                "fetching_page",
                page=page,
                page_size=self.page_size,
            )

            response = await self.fetch_func(page=page, limit=self.page_size, **kwargs)

            # Extract records and metadata
            # FWC API returns data in either 'results' or 'data' key
            records = response.get("results") or response.get("data", [])
            meta_dict = response.get("_meta", {})

            if meta_dict:
                meta = PaginationMeta(meta_dict)
                has_more = meta.has_more
            else:
                # Fallback: if no metadata, assume single page
                has_more = False

            if records:
                yield records

            self._logger.debug(
                "page_fetched",
                page=page,
                records_count=len(records),
                has_more=has_more,
            )

            page += 1

    async def fetch_page(
        self, page: int = 1, **kwargs: Any
    ) -> tuple[list[dict[str, Any]], PaginationMeta | None]:
        """Fetch a single page of results.

        Args:
            page: Page number to fetch
            **kwargs: Additional parameters

        Returns:
            Tuple of (records, pagination metadata)
        """
        response = await self.fetch_func(page=page, limit=self.page_size, **kwargs)

        records = response.get("results") or response.get("data", [])
        meta_dict = response.get("_meta")

        meta = PaginationMeta(meta_dict) if meta_dict else None

        return records, meta


async def fetch_all_paginated(
    fetch_func: Callable[..., Coroutine[Any, Any, dict[str, Any]]],
    page_size: int = 100,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Convenience function to fetch all paginated records.

    Args:
        fetch_func: Async function to fetch a page of data
        page_size: Number of records per page
        **kwargs: Additional parameters to pass to fetch function

    Returns:
        List of all records from all pages
    """
    paginator = Paginator(fetch_func, page_size=page_size)
    return await paginator.fetch_all(**kwargs)
