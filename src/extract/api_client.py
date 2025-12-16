"""HTTP API Client with retry logic using httpx and tenacity"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from src.config.settings import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class APIClientError(Exception):
    """Base exception for API client errors"""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(APIClientError):
    """Exception for rate limit errors"""

    pass


class AuthenticationError(APIClientError):
    """Exception for authentication errors"""

    pass


class APIClient:
    """HTTP client for FWC Modern Awards API with retry logic"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        rate_limit: int = 10,
    ):
        settings = get_settings()
        self.base_url = base_url or settings.fwc_api_base_url
        self.api_key = api_key or settings.fwc_api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit = rate_limit

        # Rate limiting
        self._request_times: List[datetime] = []
        self._lock = asyncio.Lock()

        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def headers(self) -> Dict[str, str]:
        """Get default headers for API requests"""
        return {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def __aenter__(self) -> "APIClient":
        """Async context manager entry"""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=httpx.Timeout(self.timeout),
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting"""
        async with self._lock:
            now = datetime.utcnow()
            # Remove requests older than 1 second
            self._request_times = [
                t for t in self._request_times
                if (now - t).total_seconds() < 1.0
            ]

            if len(self._request_times) >= self.rate_limit:
                # Wait until the oldest request is more than 1 second old
                oldest = self._request_times[0]
                wait_time = 1.0 - (now - oldest).total_seconds()
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

            self._request_times.append(datetime.utcnow())

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, RateLimitError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        before_sleep=before_sleep_log(logger, "WARNING"),
    )
    async def _request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request with retry logic"""
        await self._enforce_rate_limit()

        if self._client is None:
            raise RuntimeError("APIClient must be used as async context manager")

        logger.debug(
            "api_request",
            method=method,
            url=url,
            params=params,
        )

        response = await self._client.request(
            method=method,
            url=url,
            params=params,
            json=json,
        )

        if response.status_code == 429:
            raise RateLimitError("Rate limit exceeded", status_code=429)

        if response.status_code == 401:
            raise AuthenticationError("Invalid API key", status_code=401)

        if response.status_code == 403:
            raise AuthenticationError("Access forbidden", status_code=403)

        if response.status_code >= 400:
            raise APIClientError(
                f"API error: {response.text}",
                status_code=response.status_code,
            )

        return response.json()

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a GET request"""
        return await self._request("GET", url, params=params)

    async def get_awards(
        self,
        page: int = 1,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get all awards with pagination"""
        return await self.get(
            "/awards",
            params={"page": page, "limit": limit},
        )

    async def get_classifications(
        self,
        award_code: str,
        page: int = 1,
        limit: int = 100,
        operative_from: Optional[str] = None,
        operative_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get classifications for an award"""
        params: Dict[str, Any] = {"page": page, "limit": limit}
        if operative_from:
            params["operative_from"] = operative_from
        if operative_to:
            params["operative_to"] = operative_to

        return await self.get(
            f"/awards/{award_code}/classifications",
            params=params,
        )

    async def get_pay_rates(
        self,
        award_code: str,
        page: int = 1,
        limit: int = 100,
        classification_level: Optional[int] = None,
        employee_rate_type_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get pay rates for an award"""
        params: Dict[str, Any] = {"page": page, "limit": limit}
        if classification_level is not None:
            params["classification_level"] = classification_level
        if employee_rate_type_code:
            params["employee_rate_type_code"] = employee_rate_type_code

        return await self.get(
            f"/awards/{award_code}/pay-rates",
            params=params,
        )

    async def get_expense_allowances(
        self,
        award_code: str,
        page: int = 1,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get expense allowances for an award"""
        return await self.get(
            f"/awards/{award_code}/expense-allowances",
            params={"page": page, "limit": limit},
        )

    async def get_wage_allowances(
        self,
        award_code: str,
        page: int = 1,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get wage allowances for an award"""
        return await self.get(
            f"/awards/{award_code}/wage-allowances",
            params={"page": page, "limit": limit},
        )

    async def get_penalties(
        self,
        award_code: str,
        page: int = 1,
        limit: int = 100,
        penalty_fixed_id: Optional[int] = None,
        classification_level: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get penalties for an award"""
        params: Dict[str, Any] = {"page": page, "limit": limit}
        if penalty_fixed_id is not None:
            params["penalty_fixed_id"] = penalty_fixed_id
        if classification_level is not None:
            params["classification_level"] = classification_level

        return await self.get(
            f"/awards/{award_code}/penalties",
            params=params,
        )
