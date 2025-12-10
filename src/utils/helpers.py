"""Helper utilities for ETL Pipeline"""

import re
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union
import hashlib
import json


def generate_record_hash(record: Dict[str, Any], fields: List[str]) -> str:
    """Generate a hash for a record based on specified fields"""
    values = [str(record.get(field, "")) for field in sorted(fields)]
    combined = "|".join(values)
    return hashlib.md5(combined.encode()).hexdigest()


def parse_datetime(value: Any) -> Optional[datetime]:
    """Parse various datetime formats to datetime object"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, str):
        # Try ISO format first
        try:
            # Handle timezone info
            if "+" in value or value.endswith("Z"):
                value = re.sub(r"\+\d{2}:\d{2}$", "", value)
                value = value.rstrip("Z")
            return datetime.fromisoformat(value)
        except ValueError:
            pass

        # Try common formats
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y",
            "%d/%m/%Y %H:%M:%S",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue

    return None


def parse_date(value: Any) -> Optional[date]:
    """Parse various date formats to date object"""
    dt = parse_datetime(value)
    if dt:
        return dt.date()
    return None


def safe_get(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely get nested dictionary value"""
    result = data
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key, default)
        else:
            return default
    return result


def flatten_dict(
    data: Dict[str, Any],
    prefix: str = "",
    separator: str = "_",
) -> Dict[str, Any]:
    """Flatten nested dictionary"""
    items: Dict[str, Any] = {}
    for key, value in data.items():
        new_key = f"{prefix}{separator}{key}" if prefix else key
        if isinstance(value, dict):
            items.update(flatten_dict(value, new_key, separator))
        elif isinstance(value, list):
            # Convert lists to JSON string
            items[new_key] = json.dumps(value)
        else:
            items[new_key] = value
    return items


def chunk_list(data: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size"""
    return [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)]


def sanitize_string(value: Any, max_length: Optional[int] = None) -> Optional[str]:
    """Sanitize string value for database storage"""
    if value is None:
        return None
    string_value = str(value).strip()
    if max_length and len(string_value) > max_length:
        string_value = string_value[:max_length]
    return string_value


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """Safely convert value to float"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    """Safely convert value to integer"""
    if value is None:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def safe_bool(value: Any, default: bool = False) -> bool:
    """Safely convert value to boolean"""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries, later values override earlier ones"""
    result: Dict[str, Any] = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


class Timer:
    """Simple timer context manager"""

    def __init__(self) -> None:
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def __enter__(self) -> "Timer":
        self.start_time = datetime.utcnow()
        return self

    def __exit__(self, *args: Any) -> None:
        self.end_time = datetime.utcnow()

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds"""
        if self.start_time is None:
            return 0.0
        end = self.end_time or datetime.utcnow()
        return (end - self.start_time).total_seconds()
