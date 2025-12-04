"""Data preview routes."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.load.sql_connector import SQLConnector

router = APIRouter()

# Valid tables that can be previewed
VALID_TABLES = {
    "awards",
    "classifications",
    "pay_rates",
    "expense_allowances",
    "wage_allowances",
    "etl_job_logs",
    "raw_api_responses",
}


class DataPreview(BaseModel):
    """Data preview response model."""

    table: str
    total_count: int
    page: int
    limit: int
    data: list[dict[str, Any]]


@router.get("/data/preview/{table}", response_model=DataPreview)
async def preview_table(
    table: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=1000),
) -> dict[str, Any]:
    """Preview data from a specific table.

    Args:
        table: Table name to preview
        page: Page number (1-based)
        limit: Number of records per page
    """
    if table not in VALID_TABLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid table name. Valid tables: {', '.join(sorted(VALID_TABLES))}",
        )

    connector = SQLConnector()
    offset = (page - 1) * limit

    try:
        # Get total count
        count_sql = f"SELECT COUNT(*) FROM {table}"  # noqa: S608
        total_count = connector.execute_scalar(count_sql) or 0

        # Get data with pagination
        data_sql = f"""
            SELECT * FROM {table}
            ORDER BY id
            OFFSET :offset ROWS
            FETCH NEXT :limit ROWS ONLY
        """  # noqa: S608

        rows = connector.execute_raw(
            data_sql,
            {"offset": offset, "limit": limit},
        )

        # Convert rows to dictionaries
        data = [dict(row._mapping) for row in rows]

        return {
            "table": table,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "data": data,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}") from e


@router.get("/data/tables")
async def list_tables() -> dict[str, list[str]]:
    """List available tables for preview."""
    return {"tables": sorted(VALID_TABLES)}


@router.get("/data/stats/{table}")
async def get_table_stats(table: str) -> dict[str, Any]:
    """Get statistics for a specific table.

    Args:
        table: Table name
    """
    if table not in VALID_TABLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid table name. Valid tables: {', '.join(sorted(VALID_TABLES))}",
        )

    connector = SQLConnector()

    try:
        # Get basic stats
        count_sql = f"SELECT COUNT(*) FROM {table}"  # noqa: S608
        total_count = connector.execute_scalar(count_sql) or 0

        stats: dict[str, Any] = {
            "table": table,
            "total_records": total_count,
        }

        # Try to get date range if table has created_at
        try:
            date_sql = f"""
                SELECT
                    MIN(created_at) as first_record,
                    MAX(created_at) as last_record
                FROM {table}
            """  # noqa: S608
            dates = connector.execute_raw(date_sql)
            if dates:
                row = dates[0]
                stats["first_record"] = str(row[0]) if row[0] else None
                stats["last_record"] = str(row[1]) if row[1] else None
        except Exception:
            pass  # Column might not exist

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}") from e
