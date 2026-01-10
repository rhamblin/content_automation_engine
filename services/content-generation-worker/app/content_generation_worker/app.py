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
        redis_broker = Redis(host="redis", port=6379)
        db_session_factory = get_db_session

        # provider registries
        blob_client = BlobServiceClient.from_connection_string(settings.azure_blob_storage_connection_string)()
        azure_openai_client = AzureOpenAI(
            api_version="2024-12-01-preview",
            azure_endpoint=settings.azure_foundry_endpoint,
            api_key=settings.azure_foundry_api_key,
        )

        azure_blob_storage_image__provider = AzureBlobStorageImageProvider(blob_client, logger)
        azure_foundry_text_provider = AzureFoundryTextProvider(azure_openai_client, logger)
        pinterest_channel_provider = PinterestChannel(logger)

        provider_registry = registry.ProviderRegistry(
            image_providers={
                constants.IMAGE_PROVIDER_AZURE_BLOB_STORAGE: azure_blob_storage_image__provider,
            },
            text_providers={
                constants.TEXT_PROVIDER_AZURE_FOUNDRY: azure_foundry_text_provider,
            },
            distribution_channels={
                constants.CHANNEL_PINTEREST: pinterest_channel_provider,
            }
        )
    except Exception as e:
        logger.error(f"Failed to initialize Content Generation Worker: {e}")
        return

    worker = ContentGenerationWorker(
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