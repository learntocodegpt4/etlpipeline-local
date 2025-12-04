"""API endpoint definitions for the FWC Modern Awards API."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class EndpointType(str, Enum):
    """Types of API endpoints."""

    AWARDS = "awards"
    CLASSIFICATIONS = "classifications"
    PAY_RATES = "pay_rates"
    EXPENSE_ALLOWANCES = "expense_allowances"
    WAGE_ALLOWANCES = "wage_allowances"


@dataclass
class APIEndpoint:
    """Represents an API endpoint configuration."""

    name: str
    path: str
    method: str = "GET"
    description: str = ""
    requires_award_code: bool = False
    supports_pagination: bool = True

    def get_url(self, base_url: str, **kwargs: Any) -> str:
        """Generate full URL with path parameters substituted."""
        path = self.path.format(**kwargs)
        return f"{base_url}{path}"


# FWC API Endpoints
ENDPOINTS = {
    EndpointType.AWARDS: APIEndpoint(
        name="awards",
        path="/awards",
        description="Get all awards with optional filtering",
        requires_award_code=False,
        supports_pagination=True,
    ),
    EndpointType.CLASSIFICATIONS: APIEndpoint(
        name="classifications",
        path="/awards/{award_code}/classifications",
        description="Get classifications for a specific award",
        requires_award_code=True,
        supports_pagination=True,
    ),
    EndpointType.PAY_RATES: APIEndpoint(
        name="pay_rates",
        path="/awards/{award_code}/pay-rates",
        description="Get pay rates for a specific award",
        requires_award_code=True,
        supports_pagination=True,
    ),
    EndpointType.EXPENSE_ALLOWANCES: APIEndpoint(
        name="expense_allowances",
        path="/awards/{award_code}/expense-allowances",
        description="Get expense allowances for a specific award",
        requires_award_code=True,
        supports_pagination=True,
    ),
    EndpointType.WAGE_ALLOWANCES: APIEndpoint(
        name="wage_allowances",
        path="/awards/{award_code}/wage-allowances",
        description="Get wage allowances for a specific award",
        requires_award_code=True,
        supports_pagination=True,
    ),
}


def get_endpoint(endpoint_type: EndpointType) -> APIEndpoint:
    """Get endpoint configuration by type."""
    return ENDPOINTS[endpoint_type]


# HTTP Headers for FWC API
def get_api_headers(api_key: str) -> dict[str, str]:
    """Generate required headers for FWC API requests."""
    return {
        "Ocp-Apim-Subscription-Key": api_key,
        "Accept": "application/json",
        "Cache-Control": "no-cache",
    }


# Pagination defaults
DEFAULT_PAGE_SIZE = 100
DEFAULT_PAGE = 1
MAX_PAGE_SIZE = 100


def get_pagination_params(page: int = DEFAULT_PAGE, limit: int = DEFAULT_PAGE_SIZE) -> dict[str, int]:
    """Generate pagination query parameters."""
    return {
        "page": max(1, page),
        "limit": min(max(1, limit), MAX_PAGE_SIZE),
    }
