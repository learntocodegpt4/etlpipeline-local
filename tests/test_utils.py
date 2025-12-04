"""Tests for utility functions."""

import pytest


def test_generate_job_id():
    """Test job ID generation."""
    from src.utils.helpers import generate_job_id

    job_id = generate_job_id()
    assert job_id.startswith("job_")
    assert len(job_id) > 20  # Timestamp + unique ID


def test_generate_job_id_uniqueness():
    """Test that job IDs are unique."""
    from src.utils.helpers import generate_job_id

    ids = [generate_job_id() for _ in range(100)]
    assert len(set(ids)) == 100  # All unique


def test_chunk_list():
    """Test list chunking."""
    from src.utils.helpers import chunk_list

    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    chunks = chunk_list(data, 3)
    assert len(chunks) == 4
    assert chunks[0] == [1, 2, 3]
    assert chunks[1] == [4, 5, 6]
    assert chunks[2] == [7, 8, 9]
    assert chunks[3] == [10]


def test_chunk_list_empty():
    """Test chunking empty list."""
    from src.utils.helpers import chunk_list

    chunks = chunk_list([], 3)
    assert chunks == []


def test_safe_get():
    """Test safe dictionary access."""
    from src.utils.helpers import safe_get

    data = {"a": {"b": {"c": 123}}}

    assert safe_get(data, "a", "b", "c") == 123
    assert safe_get(data, "a", "b") == {"c": 123}
    assert safe_get(data, "x", "y", default="not found") == "not found"


def test_flatten_dict():
    """Test dictionary flattening."""
    from src.utils.helpers import flatten_dict

    nested = {
        "a": 1,
        "b": {
            "c": 2,
            "d": {
                "e": 3
            }
        }
    }

    flat = flatten_dict(nested)
    assert flat == {
        "a": 1,
        "b_c": 2,
        "b_d_e": 3
    }


def test_format_duration():
    """Test duration formatting."""
    from src.utils.helpers import format_duration

    assert format_duration(30) == "30s"
    assert format_duration(90) == "1m 30s"
    assert format_duration(3661) == "1h 1m 1s"
