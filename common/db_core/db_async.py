import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.exc import OperationalError, DBAPIError
from tenacity import (
      retry,
      wait_exponential,
      stop_after_attempt,
      retry_if_exception_type,
      before_sleep_log
)

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DB_URL", "")
ASYNC_DATABASE_URL = DATABASE_URL

@retry(  
        stop=stop_after_attempt(3)
        ,retry=retry_if_exception_type((OperationalError, DBAPIError, ConnectionRefusedError, OSError))
        ,wait=wait_exponential(multiplier=1, min=1, max=10)
        ,before_sleep=before_sleep_log(logger, logging.WARNING))
def get_engine():
    logger.info(f"Creating database engine")
    engine = create_async_engine(
        ASYNC_DATABASE_URL, 
        echo=True,
        pool_pre_ping=True,
        pool_recycle=3600)
    logger.info(f"Database engine created successfully")
    return engine

try:
    async_engine = get_engine()
except Exception as e:
    logger.critical(f"FATAL: Failed to create database engine after 3 attempts: {e}")
    raise  # Service should not start without DB

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

def get_db_session() -> AsyncSession:
    return AsyncSessionLocal()