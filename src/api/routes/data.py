"""Data preview API routes"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.load.sql_connector import get_connector
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Allowed tables for preview
ALLOWED_TABLES = [
    "awards",
    "classifications",
    "pay_rates",
    "expense_allowances",
    "wage_allowances",
]


class DataPreviewResponse(BaseModel):
    """Response model for data preview"""

    table: str
    total_count: int
    page: int
    page_size: int
    data: List[Dict[str, Any]]


@router.get("/data/preview/{table}", response_model=DataPreviewResponse)
async def preview_data(
    table: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    award_code: Optional[str] = None,
) -> DataPreviewResponse:
    """Preview data from a table"""
    if table not in ALLOWED_TABLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid table. Allowed: {ALLOWED_TABLES}",
        )

    connector = get_connector()
    offset = (page - 1) * page_size

    try:
        # Build query
        where_clause = ""
        params: Dict[str, Any] = {"limit": page_size, "offset": offset}

        if award_code and table != "awards":
            where_clause = "WHERE award_code = :award_code"
            params["award_code"] = award_code

        # Get total count
        count_sql = f"SELECT COUNT(*) as cnt FROM {table} {where_clause}"
        count_result = connector.execute_query(count_sql, params)
        total_count = count_result[0]["cnt"] if count_result else 0

        # Get data
        data_sql = f"""
            SELECT TOP(:limit) * FROM (
                SELECT *, ROW_NUMBER() OVER (ORDER BY id) as rn
                FROM {table}
                {where_clause}
            ) t
            WHERE rn > :offset
            ORDER BY rn
        """
        data = connector.execute_query(data_sql, params)

        # Remove row number from results
        for row in data:
            row.pop("rn", None)

        return DataPreviewResponse(
            table=table,
            total_count=total_count,
            page=page,
            page_size=page_size,
            data=data,
        )

    except Exception as e:
        logger.error("data_preview_error", table=table, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching data: {str(e)}",
        )


@router.get("/data/tables")
async def list_tables() -> Dict[str, Any]:
    """List available tables and their record counts"""
    connector = get_connector()

    tables_info = []
    for table in ALLOWED_TABLES:
        try:
            result = connector.execute_query(f"SELECT COUNT(*) as cnt FROM {table}")
            count = result[0]["cnt"] if result else 0
            tables_info.append({"table": table, "record_count": count})
        except Exception as e:
            tables_info.append({"table": table, "record_count": 0, "error": str(e)})

    return {"tables": tables_info}


@router.get("/data/awards")
async def list_awards(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
) -> Dict[str, Any]:
    """List all awards"""
    connector = get_connector()
    offset = (page - 1) * page_size

    try:
        # Get distinct awards
        sql = """
            SELECT DISTINCT code, name
            FROM awards
            ORDER BY code
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
        """
        data = connector.execute_query(sql, {"limit": page_size, "offset": offset})

        count_sql = "SELECT COUNT(DISTINCT code) as cnt FROM awards"
        count_result = connector.execute_query(count_sql)
        total = count_result[0]["cnt"] if count_result else 0

        return {
            "awards": data,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    except Exception as e:
        logger.error("list_awards_error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching awards: {str(e)}",
        )
