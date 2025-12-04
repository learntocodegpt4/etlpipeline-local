"""HTTP client for the FWC Modern Awards API.

Provides a robust HTTP client with retry logic, rate limiting,
and proper error handling for interacting with the FWC API.
"""

from typing import Any

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config.api_endpoints import get_api_headers
from src.config.settings import Settings

logger = structlog.get_logger(__name__)


class FWCAPIError(Exception):
    """Base exception for FWC API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: str | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class FWCAPIRateLimitError(FWCAPIError):
    """Exception raised when rate limit is exceeded."""

    pass


class FWCAPIAuthError(FWCAPIError):
    """Exception raised for authentication errors."""

    pass


class FWCAPIClient:
    """HTTP client for the FWC Modern Awards API.

    Features:
    - Automatic retry with exponential backoff
    - Connection pooling
    - Timeout handling
    - Structured logging
    - Rate limit handling
    """

    def __init__(self, settings: Settings | None = None):
        from src.config.settings import get_settings

        self.settings = settings or get_settings()
        self._client: httpx.AsyncClient | None = None
        self._logger = logger.bind(component="fwc_api_client")

    async def __aenter__(self) -> "FWCAPIClient":
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure the HTTP client is initialized."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.settings.fwc_api_base_url,
                headers=get_api_headers(self.settings.fwc_api_key),
                timeout=httpx.Timeout(self.settings.fwc_api_timeout),
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _make_request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (relative to base URL)
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            FWCAPIError: For API-specific errors
            FWCAPIRateLimitError: When rate limited
            FWCAPIAuthError: For authentication failures
        """
        client = await self._ensure_client()

        self._logger.debug(
            "api_request",
            method=method,
            path=path,
            params=params,
        )

        try:
            response = await client.request(
                method=method,
                url=path,
                params=params,
            )

            # Handle different status codes
            if response.status_code == 401:
                raise FWCAPIAuthError(
                    "Invalid or missing API key",
                    status_code=response.status_code,
                    response_body=response.text,
                )
            elif response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                raise FWCAPIRateLimitError(
                    f"Rate limit exceeded. Retry after {retry_after} seconds",
                    status_code=response.status_code,
                    response_body=response.text,
                )
            elif response.status_code >= 400:
                raise FWCAPIError(
                    f"API request failed with status {response.status_code}",
                    status_code=response.status_code,
                    response_body=response.text,
                )

            response.raise_for_status()

            self._logger.debug(
                "api_response",
                status_code=response.status_code,
                path=path,
            )

            return response.json()

        except httpx.HTTPStatusError as e:
            self._logger.error(
                "api_http_error",
                status_code=e.response.status_code,
                path=path,
                error=str(e),
            )
            raise FWCAPIError(
                str(e),
                status_code=e.response.status_code,
                response_body=e.response.text,
            ) from e

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a GET request to the API.

        Args:
            path: API path
            params: Query parameters

        Returns:
            JSON response
        """
        return await self._make_request("GET", path, params)

    async def get_awards(
        self,
        page: int = 1,
        limit: int = 100,
        **filters: Any,
    ) -> dict[str, Any]:
        """Get all awards with pagination.

        Args:
            page: Page number
            limit: Results per page
            **filters: Additional filter parameters

        Returns:
            API response with awards data
        """
        params = {"page": page, "limit": limit, **filters}
        return await self.get("/awards", params)

    async def get_classifications(
        self,
        award_code: str,
        page: int = 1,
        limit: int = 100,
        **filters: Any,
    ) -> dict[str, Any]:
        """Get classifications for an award.

        Args:
            award_code: Award code (e.g., MA000120)
            page: Page number
            limit: Results per page
            **filters: Additional filter parameters

        Returns:
            API response with classifications data
        """
        params = {"page": page, "limit": limit, **filters}
        return await self.get(f"/awards/{award_code}/classifications", params)

    async def get_pay_rates(
        self,
        award_code: str,
        page: int = 1,
        limit: int = 100,
        **filters: Any,
    ) -> dict[str, Any]:
        """Get pay rates for an award.

        Args:
            award_code: Award code
            page: Page number
            limit: Results per page
            **filters: Additional filter parameters

        Returns:
            API response with pay rates data
        """
        params = {"page": page, "limit": limit, **filters}
        return await self.get(f"/awards/{award_code}/pay-rates", params)

    async def get_expense_allowances(
        self,
        award_code: str,
        page: int = 1,
        limit: int = 100,
        **filters: Any,
    ) -> dict[str, Any]:
        """Get expense allowances for an award.

        Args:
            award_code: Award code
            page: Page number
            limit: Results per page
            **filters: Additional filter parameters

        Returns:
            API response with expense allowances data
        """
        params = {"page": page, "limit": limit, **filters}
        return await self.get(f"/awards/{award_code}/expense-allowances", params)

    async def get_wage_allowances(
        self,
        award_code: str,
        page: int = 1,
        limit: int = 100,
        **filters: Any,
    ) -> dict[str, Any]:
        """Get wage allowances for an award.

        Args:
            award_code: Award code
            page: Page number
            limit: Results per page
            **filters: Additional filter parameters

        Returns:
            API response with wage allowances data
        """
        params = {"page": page, "limit": limit, **filters}
        return await self.get(f"/awards/{award_code}/wage-allowances", params)
