"""Awards transformer"""

from typing import Any, Dict, Optional

from src.core.interfaces import PipelineContext
from src.transform.base_transformer import BaseTransformer


class AwardsTransformer(BaseTransformer):
    """Transform awards data for database storage"""

    def __init__(self, source_key: str = "awards_extractor"):
        super().__init__(source_key=source_key)

    @property
    def name(self) -> str:
        return "awards_transformer"

    def transform_record(
        self, record: Dict[str, Any], context: PipelineContext
    ) -> Optional[Dict[str, Any]]:
        """Transform an award record"""
        return {
            "award_id": self.to_int(record.get("award_id")),
            "award_fixed_id": self.to_int(record.get("award_fixed_id")),
            "code": self.to_string(record.get("code"), max_length=50),
            "name": self.to_string(record.get("name"), max_length=500),
            "award_operative_from": self.to_datetime(record.get("award_operative_from")),
            "award_operative_to": self.to_datetime(record.get("award_operative_to")),
            "version_number": self.to_int(record.get("version_number")),
            "last_modified_datetime": self.to_datetime(record.get("last_modified_datetime")),
            "published_year": self.to_int(record.get("published_year")),
        }
