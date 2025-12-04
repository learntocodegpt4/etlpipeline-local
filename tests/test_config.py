"""Tests for the configuration module."""

import os
import pytest
from unittest.mock import patch


def test_settings_defaults():
    """Test that settings have correct defaults."""
    # Clear any existing settings cache
    from src.config.settings import Settings

    settings = Settings()

    assert settings.fwc_api_base_url == "https://api.fwc.gov.au/api/v1"
    assert settings.fwc_api_timeout == 30
    assert settings.fwc_api_max_retries == 3
    assert settings.fwc_api_page_size == 100
    assert settings.mssql_port == 1433
    assert settings.log_level == "INFO"


def test_settings_from_env():
    """Test that settings can be loaded from environment variables."""
    from src.config.settings import Settings

    with patch.dict(os.environ, {
        "FWC_API_KEY": "test_key_123",
        "MSSQL_HOST": "test-server",
        "MSSQL_DATABASE": "test_db",
    }):
        settings = Settings()
        assert settings.fwc_api_key == "test_key_123"
        assert settings.mssql_host == "test-server"
        assert settings.mssql_database == "test_db"


def test_mssql_connection_string():
    """Test SQL Server connection string generation."""
    from src.config.settings import Settings

    with patch.dict(os.environ, {
        "MSSQL_HOST": "localhost",
        "MSSQL_PORT": "1433",
        "MSSQL_DATABASE": "testdb",
        "MSSQL_USERNAME": "sa",
        "MSSQL_PASSWORD": "password",
        "MSSQL_DRIVER": "ODBC Driver 18 for SQL Server",
    }):
        settings = Settings()
        conn_str = settings.mssql_connection_string

        assert "localhost" in conn_str
        assert "testdb" in conn_str
        assert "sa" in conn_str
