import pytest
import pytest_asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from testcontainers.postgres import PostgresContainer
from common.contracts.database_models.base import Base

pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def postgres_container():
    """Start a PostgreSQL container for all tests."""
    with PostgresContainer("postgres:16") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def database_url(postgres_container):
    """Get database URL from container."""
    return postgres_container.get_connection_url()


@pytest.fixture(scope="session")
def setup_database(database_url):
    """Create schemas and tables once using sync engine."""
    engine = create_engine(database_url, echo=False)

    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS identity"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS niches"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS contents"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytics"))
        conn.commit()

    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_db_session(database_url, setup_database):
    """Create isolated session per test with automatic rollback."""
    async_url = database_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    async_url = async_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(async_url, echo=False)

    async with engine.connect() as conn:
        trans = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)

        yield session

        await session.close()
        await trans.rollback()

    await engine.dispose()
