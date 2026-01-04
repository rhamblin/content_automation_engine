import asyncio
import logging
import os

from openai import AzureOpenAI
from azure.storage.blob import BlobServiceClient
from common.db_core.db_async import get_db_session
from common.observability.logging_config import configure_logging
from common.constants import constants
from common.providers import registry, AzureBlobStorageImageProvider, AzureFoundryTextProvider, PinterestChannel, UnsplashImageProvider 
from redis.asyncio import Redis
from .worker import PostWorker

async def main():
    configure_logging()
    logger = logging.getLogger(__name__)

    try:
        redis_broker = Redis(host="redis", port=6379)
        db_session_factory = get_db_session

        # provider registries
        blob_client = __get_azure_blob_service_client()
        azure_openai_client = __get_azure_openai_client()

        azure_blob_storage_image__provider = AzureBlobStorageImageProvider(blob_client, logger)
        unsplash_image_provider = UnsplashImageProvider(logger)
        azure_foundry_text_provider = AzureFoundryTextProvider(azure_openai_client, logger)
        pinterest_channel_provider = PinterestChannel(logger)

        provider_registry = registry.ProviderRegistry(
            image_providers={
                constants.IMAGE_PROVIDER_AZURE_BLOB_STORAGE: azure_blob_storage_image__provider,
                constants.IMAGE_PROVIDER_UNSPLASH: unsplash_image_provider,
            },
            text_providers={
                constants.TEXT_PROVIDER_AZURE_FOUNDRY: azure_foundry_text_provider,
            },
            channels={
                constants.CHANNEL_PINTEREST: pinterest_channel_provider,
            }
        )
    except Exception as e:
        logger.error(f"Failed to initialize Post Worker: {e}")
        return
    
    worker = PostWorker(
        redis_broker,
        db_session_factory,
        provider_registry,
        logger
    )

    try:
        await worker.process_message()
    finally:
        await redis_broker.close()

def __get_azure_blob_service_client():
    connection_string_secret_path = os.getenv("AZURE_BLOB_STORAGE_CONNECTION_STRING")
    connection_string = ""

    with open(connection_string_secret_path, 'r') as f:
        connection_string = f.read().strip()

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    return blob_service_client

def __get_azure_openai_client() -> AzureOpenAI:
    endpoint = os.getenv("AZURE_FOUNDRY_ENDPOINT")

    api_key_secret_path = os.getenv('AZURE_FOUNDRY_PROJ_DEFAULT_API_KEY')
    azure_foundry_api_key = ""

    with open(api_key_secret_path, 'r') as f:
        azure_foundry_api_key = f.read().strip()

    client = AzureOpenAI(
            api_version="2024-12-01-preview",
            azure_endpoint=endpoint,
            api_key=azure_foundry_api_key,
        )
    return client

if __name__ == "__main__":
    asyncio.run(main())