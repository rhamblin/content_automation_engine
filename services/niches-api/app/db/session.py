"""
Creates a session to access the database using async SQLAlchemy.
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import os

# Replace with your own Postgres URL or use .env
DATABASE_URL = os.getenv("DB_URL")

engine = create_async_engine(
    DATABASE_URL,
)

# Session factory for dependency injection or manual session use
SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

async def get_db_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session