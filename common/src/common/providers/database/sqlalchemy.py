# common/providers/sqlalchemy/database.py
from contextlib import asynccontextmanager

from common.app_logger import AppLogger
from common.contracts.interfaces.database import IDatabase
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class SQLAlchemyDatabaseProvider(IDatabase):
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
        async with self.session_factory() as session:
            yield session

    async def close_connection(self) -> None:
        await self.engine.dispose()
