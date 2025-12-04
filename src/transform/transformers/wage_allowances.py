"""Wage allowances data transformer."""

from datetime import datetime
from typing import Any

from src.core.interfaces import PipelineContext
from src.transform.base_transformer import BaseTransformer


class WageAllowancesTransformer(BaseTransformer):
    """Transformer for wage allowance data.

    Transforms raw wage allowance data from the FWC API into
    a format suitable for database storage.
    """

    @property
    def output_schema(self) -> dict[str, type]:
        return {
            "wage_allowance_fixed_id": int,
            "award_code": str,
            "clause_fixed_id": int,
            "clauses": str,
            "parent_allowance": str,
            "allowance": str,
            "is_all_purpose": bool,
            "rate": float,
            "rate_unit": str,
            "base_pay_rate_id": str,
            "allowance_amount": float,
            "payment_frequency": str,
            "operative_from": datetime,
            "operative_to": datetime,
            "version_number": int,
            "last_modified_datetime": datetime,
            "published_year": int,
        }

    async def _transform_record(
        self,
        record: dict[str, Any],
        context: PipelineContext,
    ) -> dict[str, Any]:
        """Transform a single wage allowance record."""
        return {
            "wage_allowance_fixed_id": self.convert_int(record.get("wage_allowance_fixed_id")),
            "award_code": self.clean_string(record.get("award_code")),
            "clause_fixed_id": self.convert_int(record.get("clause_fixed_id")),
            "clauses": self.clean_string(record.get("clauses")),
            "parent_allowance": self.clean_string(record.get("parent_allowance")),
            "allowance": self.clean_string(record.get("allowance")),
            "is_all_purpose": bool(record.get("is_all_purpose", False)),
            "rate": self.convert_decimal(record.get("rate")),
            "rate_unit": self.clean_string(record.get("rate_unit")),
            "base_pay_rate_id": self.clean_string(record.get("base_pay_rate_id")),
            "allowance_amount": self.convert_decimal(record.get("allowance_amount")),
            "payment_frequency": self.clean_string(record.get("payment_frequency")),
            "operative_from": self.convert_datetime(record.get("operative_from")),
            "operative_to": self.convert_datetime(record.get("operative_to")),
            "version_number": self.convert_int(record.get("version_number")),
            "last_modified_datetime": self.convert_datetime(record.get("last_modified_datetime")),
            "published_year": self.convert_int(record.get("published_year")),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
