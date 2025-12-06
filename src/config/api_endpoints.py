"""API Endpoints configuration for FWC Modern Awards API"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class APIEndpoints:
    """FWC API endpoint configurations"""

    base_url: str = "https://api.fwc.gov.au/api/v1"

    @property
    def awards(self) -> str:
        """Get all awards endpoint"""
        return f"{self.base_url}/awards"

    def classifications(self, award_code: str) -> str:
        """Get classifications for an award"""
        return f"{self.base_url}/awards/{award_code}/classifications"

    def pay_rates(
        self,
        award_code: str,
        classification_level: Optional[str] = None,
        employee_rate_type_code: Optional[str] = None,
    ) -> str:
        """Get pay rates for an award"""
        url = f"{self.base_url}/awards/{award_code}/pay-rates"
        params = []
        if classification_level is not None:
            params.append(f"classification_level={classification_level}")
        if employee_rate_type_code is not None:
            params.append(f"employee_rate_type_code={employee_rate_type_code}")
        if params:
            url += "?" + "&".join(params)
        return url

    def expense_allowances(self, award_code: str) -> str:
        """Get expense allowances for an award"""
        return f"{self.base_url}/awards/{award_code}/expense-allowances"

    def wage_allowances(self, award_code: str) -> str:
        """Get wage allowances for an award"""
        return f"{self.base_url}/awards/{award_code}/wage-allowances"

    def classification_pay_rates(
        self, award_code: str, classification_fixed_id: int
    ) -> str:
        """Get pay rates for a specific classification"""
        return (
            f"{self.base_url}/awards/{award_code}/classifications"
            f"/{classification_fixed_id}/pay-rates"
        )


# API Response field mappings for data transformation
AWARDS_FIELDS = [
    "award_id",
    "award_fixed_id",
    "code",
    "name",
    "award_operative_from",
    "award_operative_to",
    "version_number",
    "last_modified_datetime",
    "published_year",
]

CLASSIFICATIONS_FIELDS = [
    "classification_fixed_id",
    "clause_fixed_id",
    "clauses",
    "clause_description",
    "parent_classification_name",
    "classification",
    "classification_level",
    "next_down_classification_fixed_id",
    "next_up_classification_fixed_id",
    "operative_from",
    "operative_to",
    "version_number",
    "last_modified_datetime",
    "published_year",
]

PAY_RATES_FIELDS = [
    "classification_fixed_id",
    "base_pay_rate_id",
    "base_rate_type",
    "base_rate",
    "calculated_pay_rate_id",
    "calculated_rate_type",
    "calculated_rate",
    "parent_classification_name",
    "classification",
    "classification_level",
    "employee_rate_type_code",
    "operative_from",
    "operative_to",
    "version_number",
    "published_year",
    "last_modified_datetime",
]

EXPENSE_ALLOWANCES_FIELDS = [
    "expense_allowance_fixed_id",
    "clause_fixed_id",
    "clauses",
    "parent_allowance",
    "allowance",
    "is_all_purpose",
    "allowance_amount",
    "payment_frequency",
    "last_adjusted_year",
    "cpi_quarter_last_adjusted",
    "operative_from",
    "operative_to",
    "version_number",
    "last_modified_datetime",
    "published_year",
]

WAGE_ALLOWANCES_FIELDS = [
    "wage_allowance_fixed_id",
    "clause_fixed_id",
    "clauses",
    "parent_allowance",
    "allowance",
    "is_all_purpose",
    "rate",
    "rate_unit",
    "base_pay_rate_id",
    "allowance_amount",
    "payment_frequency",
    "operative_from",
    "operative_to",
    "version_number",
    "last_modified_datetime",
    "published_year",
]
