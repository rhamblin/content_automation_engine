import asyncio
import logging
import os

from openai import AzureOpenAI
from azure.storage.blob import BlobServiceClient
from common.db_core.db_async import get_db_session
from common.settings import load_settings
from common.observability.logging_config import configure_logging
from common.constants import constants
from common.providers import registry, AzureBlobStorageImageProvider, AzureFoundryTextProvider, PinterestChannel 
from redis.asyncio import Redis
from .worker import ContentGenerationWorker

async def main():
    configure_logging()
    settings = load_settings()
    logger = logging.getLogger(__name__)

    try:
       # Initialize any dependencies
       # include cache and database connections here
       pass
    except Exception as e:
        logger.error(f"Failed to initialize Service: {e}")
        return

  #  worker = ServiceWorker(    )
    # try:
    #     await worker.process_message()
    # finally:
    #     await redis_broker.close()

if __name__ == "__main__":
    asyncio.run(main())