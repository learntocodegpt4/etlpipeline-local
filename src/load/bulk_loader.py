"""Bulk loader for efficient database operations"""

from typing import Any, Dict, List, Optional, Type
import json
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.interfaces import Loader, PipelineContext
from src.load.sql_connector import SQLConnector, get_connector
from src.utils.logging import get_logger
from src.utils.helpers import chunk_list

logger = get_logger(__name__)


class BulkLoader(Loader):
    """Bulk loader for efficient database inserts with upsert support"""

    def __init__(
        self,
        source_key: str,
        table_name: str,
        key_columns: List[str],
        connector: Optional[SQLConnector] = None,
        batch_size: int = 200,
        upsert: bool = True,
    ):
        self._source_key = source_key
        self.table_name = table_name
        self.key_columns = key_columns
        self.connector = connector
        self.batch_size = batch_size
        self.upsert = upsert

    @property
    def source_key(self) -> str:
        return self._source_key

    @property
    def name(self) -> str:
        return f"{self.table_name}_loader"

    def _get_connector(self) -> SQLConnector:
        """Get SQL connector"""
        return self.connector or get_connector()

    async def load(
        self, data: List[Dict[str, Any]], context: PipelineContext
    ) -> int:
        """Load data to database with upsert logic"""
        if not data:
            logger.info("bulk_load_empty", table=self.table_name)
            return 0

        logger.info(
            "bulk_load_started",
            table=self.table_name,
            records=len(data),
            batch_size=self.batch_size,
        )

        connector = self._get_connector()
        total_loaded = 0

        # Process in batches
        batches = chunk_list(data, self.batch_size)
        for batch_num, batch in enumerate(batches, 1):
            try:
                if self.upsert:
                    loaded = self._upsert_batch(connector, batch)
                else:
                    loaded = self._insert_batch(connector, batch)

                total_loaded += loaded
                logger.debug(
                    "batch_loaded",
                    table=self.table_name,
                    batch=batch_num,
                    total_batches=len(batches),
                    records=loaded,
                )
            except Exception as e:
                logger.error(
                    "batch_load_error",
                    table=self.table_name,
                    batch=batch_num,
                    error=str(e),
                )
                context.add_error(
                    f"Failed to load batch {batch_num} to {self.table_name}: {e}"
                )

        logger.info(
            "bulk_load_completed",
            table=self.table_name,
            total_records=total_loaded,
        )

        return total_loaded

    def _insert_batch(
        self, connector: SQLConnector, batch: List[Dict[str, Any]]
    ) -> int:
        """Insert a batch of records"""
        if not batch:
            return 0

        # Get columns from first record
        columns = list(batch[0].keys())
        placeholders = ", ".join([f":{col}" for col in columns])
        columns_str = ", ".join(columns)

        sql = f"INSERT INTO {self.table_name} ({columns_str}) VALUES ({placeholders})"

        # Simple retry loop to mitigate transient connection errors
        attempts = 0
        last_exc: Optional[Exception] = None
        while attempts < 3:
            session = connector.get_session()
            try:
                for record in batch:
                    clean_record = self._clean_record(record)
                    session.execute(text(sql), clean_record)
                session.commit()
                return len(batch)
            except Exception as e:
                session.rollback()
                last_exc = e
                attempts += 1
                logger.warning(
                    "insert_retry", table=self.table_name, attempt=attempts, error=str(e)
                )
                # backoff
                try:
                    import time
                    time.sleep(min(5, 0.5 * (2 ** (attempts - 1))))
                except Exception:
                    pass
            finally:
                session.close()
        if last_exc:
            raise last_exc
        return 0

    def _upsert_batch(
        self, connector: SQLConnector, batch: List[Dict[str, Any]]
    ) -> int:
        """Upsert a batch of records (merge in SQL Server)"""
        if not batch:
            return 0

        # Get columns from first record
        columns = list(batch[0].keys())
        update_columns = [c for c in columns if c not in self.key_columns]

        # Build MERGE statement for SQL Server
        source_cols = ", ".join([f":{col} AS {col}" for col in columns])
        key_match = " AND ".join(
            [f"target.{col} = source.{col}" for col in self.key_columns]
        )
        update_set = ", ".join(
            [f"target.{col} = source.{col}" for col in update_columns]
        )
        insert_cols = ", ".join(columns)
        insert_vals = ", ".join([f"source.{col}" for col in columns])

        sql = f"""
        MERGE INTO {self.table_name} AS target
        USING (SELECT {source_cols}) AS source
        ON {key_match}
        WHEN MATCHED THEN
            UPDATE SET {update_set}
        WHEN NOT MATCHED THEN
            INSERT ({insert_cols})
            VALUES ({insert_vals});
        """

        # Retry on transient failures (e.g., TCP provider / handshake issues)
        attempts = 0
        last_exc: Optional[Exception] = None
        while attempts < 3:
            session = connector.get_session()
            try:
                for record in batch:
                    clean_record = self._clean_record(record)
                    session.execute(text(sql), clean_record)
                session.commit()
                return len(batch)
            except Exception as e:
                session.rollback()
                last_exc = e
                attempts += 1
                logger.warning(
                    "upsert_retry", table=self.table_name, attempt=attempts, error=str(e)
                )
                try:
                    import time
                    time.sleep(min(5, 0.5 * (2 ** (attempts - 1))))
                except Exception:
                    pass
            finally:
                session.close()
        if last_exc:
            raise last_exc
        return 0

    def _clean_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Clean record for database insertion"""
        clean = {}
        for key, value in record.items():
            if isinstance(value, (dict, list)):
                clean[key] = json.dumps(value)
            elif isinstance(value, datetime):
                clean[key] = value
            else:
                clean[key] = value
        return clean


class RawDataLoader(Loader):
    """Loader for raw API response data"""

    def __init__(
        self,
        source_key: str,
        data_type: str,
        connector: Optional[SQLConnector] = None,
    ):
        self._source_key = source_key
        self.data_type = data_type
        self.connector = connector

    @property
    def source_key(self) -> str:
        return self._source_key

    @property
    def name(self) -> str:
        return f"raw_{self.data_type}_loader"

    async def load(
        self, data: List[Dict[str, Any]], context: PipelineContext
    ) -> int:
        """Load raw data as JSON to raw_api_responses table"""
        if not data:
            return 0

        connector = self.connector or get_connector()

        sql = """
        INSERT INTO raw_api_responses
        (job_id, data_type, response_data, record_count, extracted_at)
        VALUES (:job_id, :data_type, :response_data, :record_count, :extracted_at)
        """

        session = connector.get_session()
        try:
            session.execute(
                text(sql),
                {
                    "job_id": context.job_id,
                    "data_type": self.data_type,
                    "response_data": json.dumps(data),
                    "record_count": len(data),
                    "extracted_at": datetime.utcnow(),
                },
            )
            session.commit()
            logger.info(
                "raw_data_saved",
                data_type=self.data_type,
                record_count=len(data),
            )
            return 1
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
