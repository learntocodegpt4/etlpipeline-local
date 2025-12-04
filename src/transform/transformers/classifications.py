"""Classifications data transformer."""

from datetime import datetime
from typing import Any

from src.core.interfaces import PipelineContext
from src.transform.base_transformer import BaseTransformer


class ClassificationsTransformer(BaseTransformer):
    """Transformer for classification data.

    Transforms raw classification data from the FWC API into
    a format suitable for database storage.
    """

    @property
    def output_schema(self) -> dict[str, type]:
        return {
            "classification_fixed_id": int,
            "award_code": str,
            "classification": str,
            "classification_level": int,
            "parent_classification_name": str,
            "employee_rate_type_code": str,
            "operative_from": datetime,
            "operative_to": datetime,
            "version_number": int,
            "published_year": int,
            "last_modified_datetime": datetime,
        }

    async def _transform_record(
        self,
        record: dict[str, Any],
        context: PipelineContext,
    ) -> dict[str, Any]:
        """Transform a single classification record."""
        return {
            "classification_fixed_id": self.convert_int(record.get("classification_fixed_id")),
            "award_code": self.clean_string(record.get("award_code")),
            "classification": self.clean_string(record.get("classification")),
            "classification_level": self.convert_int(record.get("classification_level")),
            "parent_classification_name": self.clean_string(record.get("parent_classification_name")),
            "employee_rate_type_code": self.clean_string(record.get("employee_rate_type_code")),
            "operative_from": self.convert_datetime(record.get("operative_from")),
            "operative_to": self.convert_datetime(record.get("operative_to")),
            "version_number": self.convert_int(record.get("version_number")),
            "published_year": self.convert_int(record.get("published_year")),
            "last_modified_datetime": self.convert_datetime(record.get("last_modified_datetime")),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
