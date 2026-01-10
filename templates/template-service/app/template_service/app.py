import asyncio
import logging
import os


from common.providers.database import SQLAlchemyDatabase
from common.settings import load_settings
from common.observability.logging_config import configure_logging
from .worker import TemplateServiceWorker
from common.providers.messaging import RedisMessageConsumer
from common.providers.messaging import RedisMessagePublisher
from redis.asyncio import Redis

async def main():
    configure_logging()
    settings = load_settings()
    logger = logging.getLogger(__name__)

    try:
       # Initialize any dependencies
       # include cache and database connections here
        redis_broker = Redis(host="redis", port=6379)

        database = SQLAlchemyDatabase(settings.database_url, logger)
        async with database.session() as session:
            await session.execute("SELECT 1")

    except Exception as e:
        logger.error(f"Failed to initialize Service: {e}")
        return

    registry = registry.ProviderRegistry(
        image_providers={},
        text_providers={},
        distribution_channels={},
        message_consumer=RedisMessageConsumer(redis_broker, logger),
        message_publisher=RedisMessagePublisher(redis_broker, logger),
        database=database
    )

    worker = TemplateServiceWorker(registry, logger)

    try:
        await worker.process_message()
    finally:
        await redis_broker.close()

if __name__ == "__main__":
    asyncio.run(main())