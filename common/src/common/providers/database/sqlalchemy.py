# common/providers/sqlalchemy/database.py
from contextlib import asynccontextmanager

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from common.app_logger import AppLogger
from common.contracts.interfaces.database import IDatabase


class SQLAlchemyDatabaseProvider(IDatabase):
    """SQLAlchemy database provider.

    Raises:
        ConnectionError: When database connection fails.
    """

    def __init__(self, db_url: str):
        self.logger = AppLogger(__name__)
        self.logger.info("Creating database engine")

        self.engine = create_async_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600,
        )

        self.session_factory = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )

        self.logger.info("Database engine created")

    @asynccontextmanager
    async def get_session(self):
        """Get a database session.

        Raises:
            ConnectionError: When database connection fails.
        """
        try:
            async with self.session_factory() as session:
                yield session
        except SQLAlchemyError as e:
            raise ConnectionError(f"Database connection error: {e}") from e

    async def close_connection(self) -> None:
        """Close database connection."""
        await self.engine.dispose()
