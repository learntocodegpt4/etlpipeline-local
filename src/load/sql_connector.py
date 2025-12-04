"""SQL Server connector using SQLAlchemy"""

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from src.config.settings import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SQLConnector:
    """MS SQL Server connector with connection pooling"""

    def __init__(
        self,
        connection_string: Optional[str] = None,
        pool_size: int = 5,
        max_overflow: int = 10,
    ):
        settings = get_settings()
        self.connection_string = connection_string or settings.database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow

        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

    @property
    def engine(self) -> Engine:
        """Get or create SQLAlchemy engine"""
        if self._engine is None:
            self._engine = create_engine(
                self.connection_string,
                poolclass=QueuePool,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False,
            )
            self._session_factory = sessionmaker(bind=self._engine)
            logger.info("sql_engine_created")
        return self._engine

    @property
    def session_factory(self) -> sessionmaker:
        """Get session factory"""
        if self._session_factory is None:
            _ = self.engine  # This creates both engine and session factory
        return self._session_factory  # type: ignore

    def get_session(self) -> Session:
        """Get a new database session"""
        return self.session_factory()

    @asynccontextmanager
    async def session_context(self) -> AsyncIterator[Session]:
        """Async context manager for database sessions"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def execute_raw(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute raw SQL statement"""
        with self.engine.connect() as conn:
            result = conn.execute(text(sql), params or {})
            conn.commit()
            return result

    def execute_query(
        self, sql: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute SQL query and return results as list of dicts"""
        with self.engine.connect() as conn:
            result = conn.execute(text(sql), params or {})
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("database_connection_successful")
            return True
        except Exception as e:
            logger.error("database_connection_failed", error=str(e))
            return False

    def close(self) -> None:
        """Close database connections"""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("sql_engine_disposed")


# Global connector instance
_connector: Optional[SQLConnector] = None


def get_connector() -> SQLConnector:
    """Get global SQL connector instance"""
    global _connector
    if _connector is None:
        _connector = SQLConnector()
    return _connector
