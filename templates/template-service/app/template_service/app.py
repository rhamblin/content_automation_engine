import asyncio
import logging

from common.providers.database.sqlalchemy import SQLAlchemyDatabaseProvider
from common.providers.messaging.redis_broker import RedisMessageBroker
from common.settings import load_settings
from common.logging_config import configure_logging
from common.constants import ENVIRONMENT_LOCAL

from .worker import TemplateServiceWorker

from redis.asyncio import Redis

async def main():
    configure_logging()
    settings = load_settings()
    logger = logging.getLogger(__name__)

    # Initialize any needed providers in this block
    try:
        database = None
        if settings.environment == ENVIRONMENT_LOCAL:
            redis_broker = Redis(host="redis", port=6379)
            database = SQLAlchemyDatabaseProvider(settings.database_url, logger)

        # Test DB Connection
        if database:
            async with database.session() as session:
                await session.execute("SELECT 1")

    except Exception as e:
        logger.error(f"Failed to initialize Service: {e}")
        return

    # Add additional providers as needed
    registry = registry.ProviderRegistry(
        image_providers={},
        text_providers={},
        distribution_channels={},
        message_broker=RedisMessageBroker(redis_broker),
        database=database
    )

    worker = TemplateServiceWorker(registry, logger)

    try:
        await worker.work()
    finally:
        await redis_broker.close()

if __name__ == "__main__":
    asyncio.run(main())