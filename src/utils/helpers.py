"""Utility helper functions."""

import hashlib
import json
from datetime import datetime
from typing import Any
from uuid import uuid4


def generate_job_id() -> str:
    """Generate a unique job ID."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique = uuid4().hex[:8]
    return f"job_{timestamp}_{unique}"


def hash_record(record: dict[str, Any]) -> str:
    """Generate a hash for a record for deduplication.

    Args:
        record: Record dictionary

    Returns:
        MD5 hash of the record
    """
    record_str = json.dumps(record, sort_keys=True, default=str)
    return hashlib.md5(record_str.encode()).hexdigest()


def chunk_list(lst: list[Any], chunk_size: int) -> list[list[Any]]:
    """Split a list into chunks of specified size.

    Args:
        lst: List to split
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_get(d: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely get a nested value from a dictionary.

    Args:
        d: Dictionary to search
        *keys: Keys to traverse
        default: Default value if not found

    Returns:
        Value at the nested key or default
    """
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, default)
        else:
            return default
    return d


def flatten_dict(d: dict[str, Any], parent_key: str = "", sep: str = "_") -> dict[str, Any]:
    """Flatten a nested dictionary.

    Args:
        d: Dictionary to flatten
        parent_key: Prefix for keys
        sep: Separator between keys

    Returns:
        Flattened dictionary
    """
    items: list[tuple[str, Any]] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string like "2h 30m 15s"
    """
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")

    return " ".join(parts)
