"""Application settings using Pydantic Settings"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
        default="",
        description="API key for FWC API (Ocp-Apim-Subscription-Key)",
    )

    # MS SQL Configuration
    mssql_connection_string: Optional[str] = Field(
        default=None,
        description="Full MS SQL connection string",
    )
    mssql_host: str = Field(
        default="localhost",
        description="MS SQL Server host",
    )
    mssql_port: int = Field(
        default=1433,
        description="MS SQL Server port",
    )
    mssql_database: str = Field(
        default="etl_pipeline",
        description="MS SQL database name",
    )
    mssql_user: str = Field(
        default="sa",
        description="MS SQL username",
    )
    mssql_password: str = Field(
        default="",
        description="MS SQL password",
    )
    mssql_driver: str = Field(
        default="ODBC Driver 17 for SQL Server",
        description="ODBC Driver for MS SQL",
    )

    # SQLite for state management
    sqlite_database_path: str = Field(
        default="./data/state.db",
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
            return self.mssql_connection_string

        # Build connection string from individual params
        driver = self.mssql_driver.replace(" ", "+")
        return (
            f"mssql+pyodbc://{self.mssql_user}:{self.mssql_password}"
            f"@{self.mssql_host}:{self.mssql_port}/{self.mssql_database}"
            f"?driver={driver}"
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
