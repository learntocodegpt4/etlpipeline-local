"""Classifications transformer"""

from typing import Any, Dict, Optional

from src.core.interfaces import PipelineContext
from src.transform.base_transformer import BaseTransformer


class ClassificationsTransformer(BaseTransformer):
    """Transform classifications data for database storage"""

    def __init__(self, source_key: str = "classifications_extractor"):
        super().__init__(source_key=source_key)

    @property
    def name(self) -> str:
        return "classifications_transformer"

    def transform_record(
        self, record: Dict[str, Any], context: PipelineContext
    ) -> Optional[Dict[str, Any]]:
        """Transform a classification record"""
        return {
            "classification_fixed_id": self.to_int(record.get("classification_fixed_id")),
            "award_code": self.to_string(record.get("award_code"), max_length=50),
            "clause_fixed_id": self.to_int(record.get("clause_fixed_id")),
            "clauses": self.to_string(record.get("clauses"), max_length=200),
            "clause_description": self.to_string(record.get("clause_description"), max_length=1000),
            "parent_classification_name": self.to_string(record.get("parent_classification_name"), max_length=500),
            "classification": self.to_string(record.get("classification"), max_length=500),
            "classification_level": self.to_int(record.get("classification_level")),
            "next_down_classification_fixed_id": self.to_int(record.get("next_down_classification_fixed_id")),
            "next_up_classification_fixed_id": self.to_int(record.get("next_up_classification_fixed_id")),
            "operative_from": self.to_datetime(record.get("operative_from")),
            "operative_to": self.to_datetime(record.get("operative_to")),
            "version_number": self.to_int(record.get("version_number")),
            "last_modified_datetime": self.to_datetime(record.get("last_modified_datetime")),
            "published_year": self.to_int(record.get("published_year")),
        }
