from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import common.providers as providers
from common.app_logger import AppLogger
from common.constants import ENVIRONMENT_LOCAL
from common.contracts.interfaces import IDistributionChannel, ITextProvider
from common.providers import registry
from common.providers.database.sqlalchemy import SQLAlchemyDatabaseProvider
from common.providers.messaging.redis_broker import RedisMessageBroker
from common.settings import load_settings
from redis.asyncio import Redis
from sqlalchemy import text
from tenacity import retry, stop_after_attempt, wait_exponential

logger = AppLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Startup and shutdown lifecycle for the FastAPI app."""
    settings = load_settings()

    logger.info(
        f"Starting Management API Service in {settings.app_environment} environment."
    )

    database = None
    message_broker = None
    blob_storage = None
    text_providers = {}
    distribution_channels = {}

    if settings.app_environment == ENVIRONMENT_LOCAL:
        redis_instance = Redis(host="redis", port=6379)
        message_broker = RedisMessageBroker(redis_instance)

        database = SQLAlchemyDatabaseProvider(settings.database_url)

        blob_storage = providers.LocalImageProvider()

        text_providers: dict[str, ITextProvider] = {
            providers.LocalTextProvider.PROVIDER_NAME: providers.LocalTextProvider()
        }

        distribution_channels: dict[str, IDistributionChannel] = {
            providers.LocalDistributionChannel.PROVIDER_NAME: providers.LocalDistributionChannel()
        }

    if database:
        await test_db_connection(database, logger)

    provider_registry = registry.ProviderRegistry(
        blob_storage=blob_storage,
        text_providers=text_providers,
        distribution_channels=distribution_channels,
        message_broker=message_broker,
        database=database,
    )

    application.state.registry = provider_registry

    yield

    logger.info("Shutting down Management API...")
    await provider_registry.shutdown()
    logger.info("Shutdown complete")


app = FastAPI(title="Management API", lifespan=lifespan)

# --- Exception handlers ---

@app.exception_handler(LookupError)
async def lookup_error_handler(request: Request, exc: LookupError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


# --- Routers ---

from management_api.routers import (  # noqa: E402
    channels,
    integration_profiles,
    keywords,
    niches,
    schedules,
    tenants,
    users,
)

app.include_router(tenants.router)
app.include_router(users.router)
app.include_router(channels.router)
app.include_router(niches.router)
app.include_router(keywords.router)
app.include_router(integration_profiles.router)
app.include_router(schedules.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=10))
async def test_db_connection(database, app_logger: AppLogger):
    async with database.session() as session:
        await session.execute(text("SELECT 1"))
        app_logger.info("Database connection successful")
