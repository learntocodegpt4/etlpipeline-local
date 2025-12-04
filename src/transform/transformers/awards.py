"""Awards data transformer."""

from datetime import datetime
from typing import Any

from src.core.interfaces import PipelineContext
from src.transform.base_transformer import BaseTransformer


class AwardsTransformer(BaseTransformer):
    """Transformer for award data.

    Transforms raw award data from the FWC API into
    a format suitable for database storage.
    """

    @property
    def output_schema(self) -> dict[str, type]:
        return {
            "award_id": int,
            "award_fixed_id": int,
            "code": str,
            "name": str,
            "award_operative_from": datetime,
            "award_operative_to": datetime,
            "version_number": int,
            "last_modified_datetime": datetime,
            "published_year": int,
        }

    async def _transform_record(
        self,
        record: dict[str, Any],
        context: PipelineContext,
    ) -> dict[str, Any]:
        """Transform a single award record."""
        return {
            "award_id": self.convert_int(record.get("award_id")),
            "award_fixed_id": self.convert_int(record.get("award_fixed_id")),
            "code": self.clean_string(record.get("code")),
            "name": self.clean_string(record.get("name")),
            "award_operative_from": self.convert_datetime(record.get("award_operative_from")),
            "award_operative_to": self.convert_datetime(record.get("award_operative_to")),
            "version_number": self.convert_int(record.get("version_number")),
            "last_modified_datetime": self.convert_datetime(record.get("last_modified_datetime")),
            "published_year": self.convert_int(record.get("published_year")),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
