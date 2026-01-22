import asyncio

import common.providers as providers
from common.app_logger import AppLogger
from common.constants import ENVIRONMENT_LOCAL
from common.contracts.interfaces import IDistributionChannel, IBlobStorage, ITextProvider
from common.providers import registry
from common.providers.database.sqlalchemy import SQLAlchemyDatabaseProvider
from common.providers.messaging.redis_broker import RedisMessageBroker
from common.settings import load_settings
from redis.asyncio import Redis
from sqlalchemy import text
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential

from .worker import PublicationWorker


async def main(logger: AppLogger):
    settings = load_settings()

    logger.info(
        f"Starting Publication Worker Service in {settings.app_environment} environment."
    )

    # Initialize any needed providers in this block
    try:
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

        # Add additional providers as needed
        provider_registry = registry.ProviderRegistry(
            blob_storage=blob_storage,
            text_providers=text_providers,
            distribution_channels=distribution_channels,
            message_broker=message_broker,
            database=database,
        )

        worker = PublicationWorker(provider_registry)
        await worker.work()
    except RetryError as e:
        print(f"Underlying error: {e.last_attempt.exception()}")
    except Exception as e:
        logger.error(f"Failed to initialize Service: {e}")
        return
    finally:
        logger.info("Shutting down worker...")
        await provider_registry.shutdown()
        logger.info("Shutdown complete")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def test_db_connection(database: SQLAlchemyDatabaseProvider, logger: AppLogger):
    async with database.get_session() as session:
        await session.execute(text("SELECT 1"))
        logger.info("Database connection successful")


if __name__ == "__main__":
    logger = AppLogger(__name__)
    asyncio.run(main(logger))
