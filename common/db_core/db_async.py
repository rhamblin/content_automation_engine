import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DB_URL", "")

ASYNC_DATABASE_URL = DATABASE_URL

async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

def get_db_session() -> AsyncSession:
    return AsyncSessionLocal()