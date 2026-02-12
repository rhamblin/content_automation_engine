import asyncio

import common.providers as providers
from azure.storage.blob import BlobServiceClient
from common.app_logger import AppLogger
from common.constants import ENVIRONMENT_LOCAL
from common.contracts.interfaces import IDistributionChannel, ILLMProvider
from common.providers import registry
from common.providers.database.sqlalchemy import SQLAlchemyDatabaseProvider
from common.providers.messaging.redis_broker import RedisMessageBroker
from common.settings import load_settings
from openai import AzureOpenAI
from redis.asyncio import Redis
from sqlalchemy import text
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential

from .worker import ChannelWorker


async def main(logger: AppLogger):
    settings = load_settings()

    logger.info(
        f"Starting Channel Worker Service in {settings.app_environment} environment."
    )

    try:
        database = None
        message_broker = None
        blob_storage = None
        llm_providers = {}
        distribution_channels = {}

        redis_instance = Redis(host="redis", port=6379)
        message_broker = RedisMessageBroker(redis_instance)

        database = SQLAlchemyDatabaseProvider(settings.database_url)

        blob_client = BlobServiceClient.from_connection_string(
            settings.azure_blob_storage_connection_string
        )
        blob_storage = providers.AzureBlobStorageProvider(blob_client)

        if settings.app_environment == ENVIRONMENT_LOCAL:
            llm_providers: dict[str, ILLMProvider] = {
                providers.LocalLLMProvider.PROVIDER_NAME: providers.LocalLLMProvider()
            }

            distribution_channels: dict[str, IDistributionChannel] = {
                providers.LocalDistributionChannel.PROVIDER_NAME: providers.LocalDistributionChannel()
            }

        else:
            blob_client = BlobServiceClient.from_connection_string(
                settings.azure_blob_storage_connection_string
            )
            blob_storage = providers.AzureBlobStorageProvider(blob_client)

            azure_openai_client = AzureOpenAI(
                api_version=settings.azure_foundry_api_version,
                azure_endpoint=settings.azure_foundry_endpoint,
                api_key=settings.azure_foundry_proj_default_api_key,
            )
            llm_providers: dict[str, ILLMProvider] = {
                providers.AzureFoundryLLMProvider.PROVIDER_NAME: providers.AzureFoundryLLMProvider(
                    azure_openai_client
                )
            }

            distribution_channels: dict[str, IDistributionChannel] = {
                providers.PinterestChannel.PROVIDER_NAME: providers.PinterestChannel()
            }

        if database:
            await test_db_connection(database, logger)

        provider_registry = registry.ProviderRegistry(
            blob_storage=blob_storage,
            llm_providers=llm_providers,
            distribution_channels=distribution_channels,
            message_broker=message_broker,
            database=database,
        )

        worker = ChannelWorker(provider_registry)
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
