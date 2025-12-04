"""Configuration settings for the FWC ETL Pipeline."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # FWC API Configuration
    fwc_api_base_url: str = Field(
        default="https://api.fwc.gov.au/api/v1",
        description="Base URL for the FWC Modern Awards API",
    )
    fwc_api_key: str = Field(
        default="",
        description="API key for FWC API authentication (Ocp-Apim-Subscription-Key)",
    )
    fwc_api_timeout: int = Field(
        default=30,
        description="HTTP request timeout in seconds",
    )
    fwc_api_max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts for failed requests",
    )
    fwc_api_page_size: int = Field(
        default=100,
        description="Number of records per page for paginated requests",
    )

    # MS SQL Server Configuration
    mssql_host: str = Field(
        default="localhost",
        description="MS SQL Server hostname",
    )
    mssql_port: int = Field(
        default=1433,
        description="MS SQL Server port",
    )
    mssql_database: str = Field(
        default="fwc_awards",
        description="MS SQL Server database name",
    )
    mssql_username: str = Field(
        default="sa",
        description="MS SQL Server username",
    )
    mssql_password: str = Field(
        default="",
        description="MS SQL Server password",
    )
    mssql_driver: str = Field(
        default="ODBC Driver 18 for SQL Server",
        description="ODBC driver name for SQL Server",
    )
    mssql_trust_server_certificate: str = Field(
        default="yes",
        description="Whether to trust the server certificate",
    )

    # SQLite State Database
    sqlite_database_path: str = Field(
        default="./data/etl_state.db",
        description="Path to SQLite database for local state management",
    )

    # Scheduler Configuration
    scheduler_enabled: bool = Field(
        default=True,
        description="Whether to enable the scheduler",
    )
    scheduler_cron_expression: str = Field(
        default="0 2 * * *",
        description="Cron expression for scheduled ETL runs (default: 2 AM daily)",
    )
    scheduler_timezone: str = Field(
        default="Australia/Sydney",
        description="Timezone for scheduler",
    )

    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    log_format: Literal["json", "console"] = Field(
        default="json",
        description="Logging output format",
    )
    log_file_path: str = Field(
        default="./logs/etl.log",
        description="Path to log file",
    )
    log_rotation_size: str = Field(
        default="10MB",
        description="Log file rotation size",
    )
    log_retention_days: int = Field(
        default=30,
        description="Number of days to retain log files",
    )

    # FastAPI Configuration
    api_host: str = Field(
        default="0.0.0.0",
        description="API server host",
    )
    api_port: int = Field(
        default=8000,
        description="API server port",
    )
    api_reload: bool = Field(
        default=False,
        description="Enable hot reload for development",
    )
    api_workers: int = Field(
        default=1,
        description="Number of API worker processes",
    )

    # Environment
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )

    @field_validator("sqlite_database_path", "log_file_path")
    @classmethod
    def create_parent_directories(cls, v: str) -> str:
        """Ensure parent directories exist for file paths."""
        path = Path(v)
        path.parent.mkdir(parents=True, exist_ok=True)
        return v

    @property
    def mssql_connection_string(self) -> str:
        """Generate MS SQL Server connection string."""
        return (
            f"mssql+pyodbc://{self.mssql_username}:{self.mssql_password}"
            f"@{self.mssql_host}:{self.mssql_port}/{self.mssql_database}"
            f"?driver={self.mssql_driver.replace(' ', '+')}"
            f"&TrustServerCertificate={self.mssql_trust_server_certificate}"
        )

    @property
    def mssql_pyodbc_connection_string(self) -> str:
        """Generate pyodbc connection string for direct connections."""
        return (
            f"DRIVER={{{self.mssql_driver}}};"
            f"SERVER={self.mssql_host},{self.mssql_port};"
            f"DATABASE={self.mssql_database};"
            f"UID={self.mssql_username};"
            f"PWD={self.mssql_password};"
            f"TrustServerCertificate={self.mssql_trust_server_certificate};"
        )

    @property
    def sqlite_connection_string(self) -> str:
        """Generate SQLite connection string."""
        return f"sqlite:///{self.sqlite_database_path}"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
