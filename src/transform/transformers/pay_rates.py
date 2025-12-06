"""Pay rates transformer"""

from typing import Any, Dict, Optional

from src.core.interfaces import PipelineContext
from src.transform.base_transformer import BaseTransformer


class PayRatesTransformer(BaseTransformer):
    """Transform pay rates data for database storage"""

    def __init__(self, source_key: str = "pay_rates_extractor"):
        super().__init__(source_key=source_key)

    @property
    def name(self) -> str:
        return "pay_rates_transformer"

    def transform_record(
        self, record: Dict[str, Any], context: PipelineContext
    ) -> Optional[Dict[str, Any]]:
        """Transform a pay rate record"""
        return {
            "classification_fixed_id": self.to_int(record.get("classification_fixed_id")),
            "award_code": self.to_string(record.get("award_code"), max_length=50),
            "base_pay_rate_id": self.to_string(record.get("base_pay_rate_id"), max_length=50),
            "base_rate_type": self.to_string(record.get("base_rate_type"), max_length=50),
            "base_rate": self.to_float(record.get("base_rate")),
            "calculated_pay_rate_id": self.to_string(record.get("calculated_pay_rate_id"), max_length=50),
            "calculated_rate_type": self.to_string(record.get("calculated_rate_type"), max_length=50),
            "calculated_rate": self.to_float(record.get("calculated_rate")),
            "parent_classification_name": self.to_string(record.get("parent_classification_name"), max_length=500),
            "classification": self.to_string(record.get("classification"), max_length=500),
            "classification_level": self.to_int(record.get("classification_level")),
            "employee_rate_type_code": self.to_string(record.get("employee_rate_type_code"), max_length=20),
            "operative_from": self.to_datetime(record.get("operative_from")),
            "operative_to": self.to_datetime(record.get("operative_to")),
            "version_number": self.to_int(record.get("version_number")),
            "last_modified_datetime": self.to_datetime(record.get("last_modified_datetime")),
            "published_year": self.to_int(record.get("published_year")),
        }
