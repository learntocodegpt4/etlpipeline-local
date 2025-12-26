"""Penalties transformer"""

from typing import Any, Dict, Optional

from src.core.interfaces import PipelineContext
from src.transform.base_transformer import BaseTransformer


class PenaltiesTransformer(BaseTransformer):
    """Transform penalties data for database storage"""

    def __init__(self, source_key: str = "penalties_extractor"):
        super().__init__(source_key=source_key)

    @property
    def name(self) -> str:
        return "penalties_transformer"

    def transform_record(
        self, record: Dict[str, Any], context: PipelineContext
    ) -> Optional[Dict[str, Any]]:
        """Transform a penalty record to match Stg_TblPenalties schema"""
        return {
            # Required keys
            "penalty_fixed_id": self.to_int(record.get("penalty_fixed_id")),
            "award_code": self.to_string(record.get("award_code"), max_length=50),

            # Clause info
            "clause_fixed_id": self.to_int(record.get("clause_fixed_id")),
            "clause_description": self.to_string(record.get("clause_description"), max_length=2000),

            # Classification (fallback to either level or fixed id depending on source)
            "classification_level": self.to_int(
                record.get("classification_level", record.get("classification_fixed_id"))
            ),

            # Penalty description and rate
            "penalty_description": self.to_string(record.get("penalty_description"), max_length=1000),
            "rate": self.to_float(
                record.get("rate", record.get("penalty_rate"))
            ),

            # Additional attributes (optional/fallbacks)
            "employee_rate_type_code": self.to_string(record.get("employee_rate_type_code"), max_length=20),
            "penalty_calculated_value": self.to_float(record.get("penalty_calculated_value")),
            "calculated_includes_all_purpose": self.to_bool(record.get("calculated_includes_all_purpose")),
            "base_pay_rate_id": self.to_string(record.get("base_pay_rate_id"), max_length=50),

            # Dates and versioning
            "operative_from": self.to_datetime(record.get("operative_from")),
            "operative_to": self.to_datetime(record.get("operative_to")),
            "version_number": self.to_int(record.get("version_number")),
            "last_modified_datetime": self.to_datetime(record.get("last_modified_datetime")),
            "published_year": self.to_int(record.get("published_year")),
        }
