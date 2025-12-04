"""Bulk data loader for SQL Server."""

import json
from datetime import datetime
from typing import Any

import structlog
from sqlalchemy import text

from src.core.interfaces import Loader, PipelineContext, StepResult, StepStatus
from src.load.sql_connector import SQLConnector

logger = structlog.get_logger(__name__)


class BulkLoader(Loader):
    """Bulk loader for inserting/upserting data to SQL Server.

    Features:
    - Batch processing for performance
    - Upsert (merge) logic
    - Raw JSON storage
    - Transaction management
    """

    def __init__(
        self,
        connector: SQLConnector | None = None,
        table_name: str = "",
        key_columns: list[str] | None = None,
        batch_size: int = 1000,
        store_raw_json: bool = True,
    ):
        super().__init__()
        self.connector = connector or SQLConnector()
        self.table_name = table_name
        self.key_columns = key_columns or []
        self.batch_size = batch_size
        self.store_raw_json = store_raw_json
        self._logger = logger.bind(loader=self.__class__.__name__, table=table_name)

    async def load(
        self,
        records: list[dict[str, Any]],
        context: PipelineContext,
    ) -> int:
        """Load records to the database.

        Args:
            records: List of records to load
            context: Pipeline context

        Returns:
            Number of records loaded
        """
        if not records:
            self._logger.info("no_records_to_load")
            return 0

        self._logger.info(
            "load_started",
            record_count=len(records),
            batch_size=self.batch_size,
        )

        total_loaded = 0

        # Process in batches
        for i in range(0, len(records), self.batch_size):
            batch = records[i : i + self.batch_size]
            loaded = self._upsert_batch(batch, context)
            total_loaded += loaded

            self._logger.debug(
                "batch_processed",
                batch_number=i // self.batch_size + 1,
                batch_size=len(batch),
                loaded=loaded,
            )

        # Store raw JSON if enabled
        if self.store_raw_json:
            self._store_raw_response(records, context)

        self._logger.info(
            "load_completed",
            total_loaded=total_loaded,
        )

        return total_loaded

    def _upsert_batch(
        self,
        records: list[dict[str, Any]],
        context: PipelineContext,
    ) -> int:
        """Upsert a batch of records using MERGE.

        Args:
            records: Batch of records
            context: Pipeline context

        Returns:
            Number of records affected
        """
        if not records:
            return 0

        # Get column names from first record
        columns = list(records[0].keys())

        with self.connector.get_session() as session:
            loaded = 0
            for record in records:
                try:
                    if self.key_columns:
                        # Build upsert using MERGE
                        loaded += self._merge_record(session, record, columns)
                    else:
                        # Simple insert
                        loaded += self._insert_record(session, record, columns)
                except Exception as e:
                    self._logger.warning(
                        "record_load_error",
                        error=str(e),
                        record=record.get(self.key_columns[0] if self.key_columns else "id"),
                    )
            session.commit()
            return loaded

    def _merge_record(
        self,
        session: Any,
        record: dict[str, Any],
        columns: list[str],
    ) -> int:
        """Merge (upsert) a single record.

        Args:
            session: Database session
            record: Record to merge
            columns: Column names

        Returns:
            1 if successful
        """
        # Build the key condition
        key_condition = " AND ".join(
            f"target.{col} = source.{col}" for col in self.key_columns
        )

        # Build update set clause (exclude key columns)
        update_columns = [col for col in columns if col not in self.key_columns]
        update_set = ", ".join(f"target.{col} = source.{col}" for col in update_columns)

        # Build insert columns and values
        insert_cols = ", ".join(columns)
        insert_vals = ", ".join(f"source.{col}" for col in columns)

        # Build source values
        source_vals = ", ".join(f":{col}" for col in columns)

        merge_sql = f"""
        MERGE INTO {self.table_name} AS target
        USING (SELECT {source_vals}) AS source ({insert_cols})
        ON ({key_condition})
        WHEN MATCHED THEN
            UPDATE SET {update_set}
        WHEN NOT MATCHED THEN
            INSERT ({insert_cols})
            VALUES ({insert_vals});
        """

        # Prepare parameters, converting datetime objects to strings
        params = {}
        for col in columns:
            val = record.get(col)
            if isinstance(val, datetime):
                params[col] = val.isoformat()
            else:
                params[col] = val

        session.execute(text(merge_sql), params)
        return 1

    def _insert_record(
        self,
        session: Any,
        record: dict[str, Any],
        columns: list[str],
    ) -> int:
        """Insert a single record.

        Args:
            session: Database session
            record: Record to insert
            columns: Column names

        Returns:
            1 if successful
        """
        col_list = ", ".join(columns)
        val_list = ", ".join(f":{col}" for col in columns)

        insert_sql = f"""
        INSERT INTO {self.table_name} ({col_list})
        VALUES ({val_list})
        """

        params = {}
        for col in columns:
            val = record.get(col)
            if isinstance(val, datetime):
                params[col] = val.isoformat()
            else:
                params[col] = val

        session.execute(text(insert_sql), params)
        return 1

    def _store_raw_response(
        self,
        records: list[dict[str, Any]],
        context: PipelineContext,
    ) -> None:
        """Store raw JSON response in the database.

        Args:
            records: Records to store as JSON
            context: Pipeline context
        """
        try:
            raw_json = json.dumps(records, default=str)

            insert_sql = """
            INSERT INTO raw_api_responses (
                job_id, endpoint_name, response_json, record_count, created_at
            ) VALUES (
                :job_id, :endpoint_name, :response_json, :record_count, :created_at
            )
            """

            with self.connector.get_session() as session:
                session.execute(
                    text(insert_sql),
                    {
                        "job_id": context.job_id,
                        "endpoint_name": self.table_name,
                        "response_json": raw_json,
                        "record_count": len(records),
                        "created_at": datetime.now().isoformat(),
                    },
                )
                session.commit()

            self._logger.debug(
                "raw_response_stored",
                job_id=context.job_id,
                record_count=len(records),
            )
        except Exception as e:
            self._logger.warning("raw_response_store_failed", error=str(e))

    async def execute(
        self, data: list[dict[str, Any]], context: PipelineContext
    ) -> StepResult[int]:
        """Execute the load step with error handling."""
        start_time = datetime.now()
        try:
            count = await self.load(data, context)
            return StepResult(
                status=StepStatus.SUCCESS,
                data=count,
                records_processed=count,
                start_time=start_time,
                end_time=datetime.now(),
            )
        except Exception as e:
            self._logger.exception("load_error", error=str(e))
            return StepResult(
                status=StepStatus.FAILED,
                error=str(e),
                error_details={
                    "exception_type": type(e).__name__,
                    "table": self.table_name,
                },
                start_time=start_time,
                end_time=datetime.now(),
            )
