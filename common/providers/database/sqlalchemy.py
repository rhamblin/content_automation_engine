# common/providers/sqlalchemy/database.py
from common.app_logger import AppLogger
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from common.contracts.database import IDatabase

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
    async def session(self):
        async with self.session_factory() as session:
            yield session
