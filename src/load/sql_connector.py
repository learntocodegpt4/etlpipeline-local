"""SQL Server connection management."""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.config.settings import Settings, get_settings

logger = structlog.get_logger(__name__)


class SQLConnector:
    """Manages SQL Server connections using SQLAlchemy.

    Provides connection pooling, session management, and
    utility methods for database operations.
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._engine: Engine | None = None
        self._session_factory: sessionmaker[Session] | None = None
        self._logger = logger.bind(component="sql_connector")

    @property
    def engine(self) -> Engine:
        """Get or create the SQLAlchemy engine with connection pooling."""
        if self._engine is None:
            self._logger.info(
                "creating_engine",
                host=self.settings.mssql_host,
                database=self.settings.mssql_database,
            )
            self._engine = create_engine(
                self.settings.mssql_connection_string,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=self.settings.debug,
            )
        return self._engine

    @property
    def session_factory(self) -> sessionmaker[Session]:
        """Get or create the session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
            )
        return self._session_factory

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup.

        Usage:
            with connector.get_session() as session:
                session.execute(query)
                session.commit()
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def execute_raw(self, sql: str, params: dict[str, Any] | None = None) -> Any:
        """Execute raw SQL and return results.

        Args:
            sql: SQL query string
            params: Query parameters

        Returns:
            Query result
        """
        with self.get_session() as session:
            result = session.execute(text(sql), params or {})
            return result.fetchall()

    def execute_scalar(self, sql: str, params: dict[str, Any] | None = None) -> Any:
        """Execute SQL and return a single scalar value.

        Args:
            sql: SQL query string
            params: Query parameters

        Returns:
            Scalar value
        """
        with self.get_session() as session:
            result = session.execute(text(sql), params or {})
            return result.scalar()

    def test_connection(self) -> bool:
        """Test the database connection.

        Returns:
            True if connection is successful
        """
        try:
            result = self.execute_scalar("SELECT 1")
            self._logger.info("connection_test_success")
            return result == 1
        except Exception as e:
            self._logger.error("connection_test_failed", error=str(e))
            return False

    def close(self) -> None:
        """Close the engine and release connections."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._logger.info("engine_closed")

    def run_migrations(self, migration_dir: str = "migrations/sql") -> None:
        """Run all SQL migration scripts.

        Args:
            migration_dir: Directory containing SQL migration files
        """
        from pathlib import Path

        migration_path = Path(migration_dir)
        if not migration_path.exists():
            self._logger.warning("migration_dir_not_found", path=migration_dir)
            return

        migration_files = sorted(migration_path.glob("*.sql"))
        self._logger.info("running_migrations", count=len(migration_files))

        with self.get_session() as session:
            for migration_file in migration_files:
                self._logger.info("running_migration", file=migration_file.name)
                sql = migration_file.read_text()
                # Split by GO statements for SQL Server
                statements = sql.split("\nGO\n")
                for statement in statements:
                    statement = statement.strip()
                    if statement:
                        try:
                            session.execute(text(statement))
                            session.commit()
                        except Exception as e:
                            self._logger.warning(
                                "migration_statement_error",
                                file=migration_file.name,
                                error=str(e),
                            )

        self._logger.info("migrations_completed")
