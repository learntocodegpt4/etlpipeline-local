"""Expense allowances data transformer."""

from datetime import datetime
from typing import Any

from src.core.interfaces import PipelineContext
from src.transform.base_transformer import BaseTransformer


class ExpenseAllowancesTransformer(BaseTransformer):
    """Transformer for expense allowance data.

    Transforms raw expense allowance data from the FWC API into
    a format suitable for database storage.
    """

    @property
    def output_schema(self) -> dict[str, type]:
        return {
            "expense_allowance_fixed_id": int,
            "award_code": str,
            "clause_fixed_id": int,
            "clauses": str,
            "parent_allowance": str,
            "allowance": str,
            "is_all_purpose": bool,
            "allowance_amount": float,
            "payment_frequency": str,
            "last_adjusted_year": int,
            "cpi_quarter_last_adjusted": str,
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
        """Transform a single expense allowance record."""
        return {
            "expense_allowance_fixed_id": self.convert_int(record.get("expense_allowance_fixed_id")),
            "award_code": self.clean_string(record.get("award_code")),
            "clause_fixed_id": self.convert_int(record.get("clause_fixed_id")),
            "clauses": self.clean_string(record.get("clauses")),
            "parent_allowance": self.clean_string(record.get("parent_allowance")),
            "allowance": self.clean_string(record.get("allowance")),
            "is_all_purpose": bool(record.get("is_all_purpose", False)),
            "allowance_amount": self.convert_decimal(record.get("allowance_amount")),
            "payment_frequency": self.clean_string(record.get("payment_frequency")),
            "last_adjusted_year": self.convert_int(record.get("last_adjusted_year")),
            "cpi_quarter_last_adjusted": self.clean_string(record.get("cpi_quarter_last_adjusted")),
            "operative_from": self.convert_datetime(record.get("operative_from")),
            "operative_to": self.convert_datetime(record.get("operative_to")),
            "version_number": self.convert_int(record.get("version_number")),
            "last_modified_datetime": self.convert_datetime(record.get("last_modified_datetime")),
            "published_year": self.convert_int(record.get("published_year")),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
