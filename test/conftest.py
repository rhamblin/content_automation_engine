import pytest
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from testcontainers.postgres import PostgresContainer
from common.db_core.models.base import Base

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

    # Retry connection with exponential backoff
    max_retries = 5
    retry_delay = 1
    for attempt in range(max_retries):
        try:
            # Create all schemas that your models use
            with engine.connect() as conn:
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS identity"))
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS niches"))
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS posts"))
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytics"))
                conn.commit()
            break
        except OperationalError as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise

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