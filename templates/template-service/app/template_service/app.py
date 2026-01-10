import asyncio

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
            redis_broker = RedisMessageBroker(redis_instance)
            
            database = SQLAlchemyDatabaseProvider(settings.database_url)

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