"""Expense allowances transformer"""

from typing import Any, Dict, Optional

from src.core.interfaces import PipelineContext
from src.transform.base_transformer import BaseTransformer


class ExpenseAllowancesTransformer(BaseTransformer):
    """Transform expense allowances data for database storage"""

    def __init__(self, source_key: str = "expense_allowances_extractor"):
        super().__init__(source_key=source_key)

    @property
    def name(self) -> str:
        return "expense_allowances_transformer"

    def transform_record(
        self, record: Dict[str, Any], context: PipelineContext
    ) -> Optional[Dict[str, Any]]:
        """Transform an expense allowance record"""
        return {
            "expense_allowance_fixed_id": self.to_int(record.get("expense_allowance_fixed_id")),
            "award_code": self.to_string(record.get("award_code"), max_length=50),
            "clause_fixed_id": self.to_int(record.get("clause_fixed_id")),
            "clauses": self.to_string(record.get("clauses"), max_length=200),
            "parent_allowance": self.to_string(record.get("parent_allowance"), max_length=500),
            "allowance": self.to_string(record.get("allowance"), max_length=500),
            "is_all_purpose": self.to_bool(record.get("is_all_purpose")),
            "allowance_amount": self.to_float(record.get("allowance_amount")),
            "payment_frequency": self.to_string(record.get("payment_frequency"), max_length=50),
            "last_adjusted_year": self.to_int(record.get("last_adjusted_year")),
            "cpi_quarter_last_adjusted": self.to_string(record.get("cpi_quarter_last_adjusted"), max_length=50),
            "operative_from": self.to_datetime(record.get("operative_from")),
            "operative_to": self.to_datetime(record.get("operative_to")),
            "version_number": self.to_int(record.get("version_number")),
            "last_modified_datetime": self.to_datetime(record.get("last_modified_datetime")),
            "published_year": self.to_int(record.get("published_year")),
        }
