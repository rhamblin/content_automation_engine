import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from testcontainers.postgres import PostgresContainer
from common.contracts.database.base import Base

@pytest.fixture(scope="session")
def postgres_container():
    """Start a PostgreSQL container for testing"""
    with PostgresContainer("postgres:16") as postgres:
        yield postgres

@pytest.fixture(scope="session")
def engine(postgres_container):
    """Create a test database engine connected to the container"""
    # Get connection URL from the container
    connection_url = postgres_container.get_connection_url()
    engine = create_engine(connection_url, echo=False)

    # Create all schemas that your models use
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS identity"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS niches"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS contents"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytics"))
        conn.commit()

    # Create all tables
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(engine):
    """Create a new database session for each test"""
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="session")
def async_engine(postgres_container):
    """Create an async database engine for testing async code"""
    # Get connection URL from the container
    connection_url = postgres_container.get_connection_url()

    # Convert to async URL (replace psycopg2 driver with asyncpg)
    async_url = connection_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    if not async_url.startswith("postgresql+asyncpg://"):
        async_url = connection_url.replace("postgresql://", "postgresql+asyncpg://")

    async_engine = create_async_engine(async_url, echo=False)
    yield async_engine

    # Cleanup - note: sync_close() is deprecated, but dispose() works
    async_engine.sync_engine.dispose()

@pytest.fixture(scope="function")
async def async_db_session(async_engine):
    """Create a new async database session for each test"""
    async_session_maker = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        async with session.begin():
            yield session
            await session.rollback()