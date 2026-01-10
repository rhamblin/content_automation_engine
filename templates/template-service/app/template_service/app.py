import asyncio

import common.providers as providers
from common.providers.database.sqlalchemy import SQLAlchemyDatabaseProvider
from common.providers.messaging.redis_broker import RedisMessageBroker
from common.settings import load_settings
from common.app_logger import AppLogger
from common.constants import ENVIRONMENT_LOCAL

from .worker import TemplateServiceWorker

from redis.asyncio import Redis

async def main():
    logger = AppLogger(__name__)
    settings = load_settings()

    # Initialize any needed providers in this block
    try:
        database = None
        if settings.environment == ENVIRONMENT_LOCAL:
            redis_instance = Redis(host="localhost", port=6379)
            message_broker = RedisMessageBroker(redis_instance)
            
            database = SQLAlchemyDatabaseProvider(settings.database_url)

            image_providers = {
                providers.LocalImageProvider.PROVIDER_NAME: providers.LocalImageProvider()
            }

            text_providers = {
                providers.LocalTextProvider.PROVIDER_NAME: providers.LocalTextProvider()
            }

            distribution_channels = {
                providers.LocalPinterestChannel.PROVIDER_NAME: providers.LocalPinterestChannel()
            }

        # Test DB Connection
        if database:
            async with database.session() as session:
                await session.execute("SELECT 1")

        # Add additional providers as needed
        registry = registry.ProviderRegistry(
            image_providers=image_providers,
            text_providers=text_providers,
            distribution_channels=distribution_channels,
            message_broker=message_broker,
            database=database
        )

    except Exception as e:
        logger.error(f"Failed to initialize Service: {e}")
        return

    worker = TemplateServiceWorker(registry, logger)

    try:
        await worker.work()
    finally:
        await message_broker.close()

if __name__ == "__main__":
    asyncio.run(main())