import asyncio
import logging

from common.db_core.db_async import get_db_session
from common.observability.logging_config import configure_logging
from common.constants import constants
from common.providers import registry, PinterestChannel
from redis.asyncio import Redis
from .worker import PublicationWorker

async def main():
    configure_logging()
    logger = logging.getLogger(__name__)

    try:
        redis_broker = Redis(host="redis", port=6379)
        db_session_factory = get_db_session

        # Initialize channel providers
        pinterest_channel_provider = PinterestChannel(logger)

        provider_registry = registry.ProviderRegistry(
            image_providers={},
            text_providers={},
            distribution_channels={
                constants.CHANNEL_PINTEREST: pinterest_channel_provider,
            }
        )
    except Exception as e:
        logger.error(f"Failed to initialize Publication Worker: {e}")
        return

    worker = PublicationWorker(
        redis_broker,
        db_session_factory,
        provider_registry,
        logger
    )

    try:
        await worker.process_message()
    finally:
        await redis_broker.close()

if __name__ == "__main__":
    asyncio.run(main())
