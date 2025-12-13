"""Application settings using Pydantic Settings"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import re


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # FWC API Configuration
    fwc_api_base_url: str = Field(
        default="https://api.fwc.gov.au/api/v1",
        description="Base URL for FWC Modern Awards API",
    )
    fwc_api_key: str = Field(
        default="4669506fdbea4e7783d3dbb7b899b935",
        description="API key for FWC API (Ocp-Apim-Subscription-Key)",
    )

    # MS SQL Configuration
    mssql_connection_string: Optional[str] = Field(
        default=None,
        description="Full MS SQL connection string",
    )
    mssql_host: str = Field(
        default="202.131.115.228",
        description="MS SQL Server host",
    )
    # Accept port as string to allow env vars like 'host:port' without failing parsing.
    mssql_port: str = Field(
        default="1433",
        description="MS SQL Server port (string to tolerate host:port env values)",
    )
    mssql_database: str = Field(
        default="RosteredAIDBDev",
        description="MS SQL database name",
    )
    mssql_user: str = Field(
        default="sa",
        description="MS SQL username",
    )
    mssql_password: str = Field(
        default="Piyush@23D!gita1",
        description="MS SQL password",
    )
    mssql_driver: str = Field(
        default="ODBC Driver 17 for SQL Server",
        description="ODBC Driver for MS SQL",
    )

    # SQLite for state management
    sqlite_database_path: str = Field(
        default="./data/etl_state.db",
        description="Path to SQLite database for state management",
    )

    # API Configuration
    api_host: str = Field(
        default="0.0.0.0",
        description="API server host",
    )
    api_port: int = Field(
        default=8000,
        description="API server port",
    )
    cors_origins: str = Field(
        default="*",
        description="Comma-separated list of allowed CORS origins (use * for all in dev)",
    )

    # Scheduler
    etl_schedule_enabled: bool = Field(
        default=True,
        description="Enable/disable ETL scheduler",
    )
    etl_cron_expression: str = Field(
        default="0 2 * * *",
        description="Cron expression for ETL schedule (default: 2 AM daily)",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    log_file_path: str = Field(
        default="./logs/etl.log",
        description="Path to log file",
    )

    # API Rate Limiting
    api_rate_limit: int = Field(
        default=10,
        description="Maximum API requests per second",
    )
    api_retry_attempts: int = Field(
        default=3,
        description="Number of retry attempts for failed API requests",
    )
    api_retry_delay: float = Field(
        default=1.0,
        description="Delay between retry attempts in seconds",
    )

    # Pagination
    default_page_size: int = Field(
        default=100,
        description="Default page size for API pagination",
    )

    @property
    def database_url(self) -> str:
        """Get the database connection URL"""
        if self.mssql_connection_string:
            # If the provided full connection string appears malformed (e.g. contains
            # unescaped '@' characters in the password), avoid using it and fall
            # back to building the URL from individual params. A valid URL should
            # only contain a single '@' separating credentials and host.
            if self.mssql_connection_string.count("@") == 1:
                return self.mssql_connection_string
            else:
                # Don't raise here; log a warning to help debugging and continue
                # to build a safe connection string from individual components.
                try:
                    import warnings

                    warnings.warn(
                        "MSSQL_CONNECTION_STRING looks malformed (multiple '@' characters)."
                        " Falling back to individual MSSQL_* settings.",
                        UserWarning,
                    )
                except Exception:
                    pass
        # Build connection string from individual params using ODBC-style
        # connection and place it into SQLAlchemy's `odbc_connect` parameter.
        from urllib.parse import quote_plus
        driver = self.mssql_driver

        host_raw = (self.mssql_host or "localhost").strip()
        had_tcp = bool(re.match(r"^tcp:", host_raw, flags=re.IGNORECASE))
        host_clean = re.sub(r"^tcp:/*", "", host_raw, flags=re.IGNORECASE)

        port_candidate = None
        if "," in host_clean:
            parts = host_clean.split(",", 1)
            host_part = parts[0]
            port_candidate = parts[1]
        elif ":" in host_clean:
            parts = host_clean.rsplit(":", 1)
            host_part = parts[0]
            port_candidate = parts[1]
        else:
            host_part = host_clean

        port = str(self.mssql_port or "").strip()
        if not port.isdigit():
            if port_candidate:
                m = re.search(r"(\d{2,5})$", port_candidate)
                port = m.group(1) if m else "1433"
            else:
                port = "1433"

        server_value = f"{host_part},{port}"
        if had_tcp:
            server_value = f"tcp:{server_value}"

        odbc_conn = (
            f"DRIVER={{{driver}}};SERVER={server_value};"
            f"DATABASE={self.mssql_database};UID={self.mssql_user};PWD={self.mssql_password};"
            "TrustServerCertificate=Yes"
        )

        return f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc_conn)}"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
