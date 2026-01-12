from asyncio import constants
from common.app_logger import AppLogger
from common.contracts import IDatabase, IImageProvider, ITextProvider, IDistributionChannel, IMessageBroker   

class ProviderRegistry:
    def __init__(self,
            database: IDatabase | None = None,
            message_broker: IMessageBroker | None = None,
            image_providers: dict[str, IImageProvider] | None = None,
            text_providers: dict[str, ITextProvider] | None = None,
            distribution_channels: dict[str, IDistributionChannel] | None = None):

        self.database = database
        self.message_broker = message_broker
        self.image_providers = image_providers or {}
        self.text_providers = text_providers or {}
        self.channels = distribution_channels or {}

    def get_database(self) -> IDatabase:
        if self.database is None:
            raise RuntimeError("Database not available in this worker's registry")
        return self.database

    def get_message_broker(self) -> IMessageBroker:
        if self.message_broker is None:
            raise RuntimeError("Message broker not available in this worker's registry")
        return self.message_broker

    def get_image_provider(self, key: str) -> IImageProvider:
        if key not in self.image_providers:
            raise RuntimeError(f"Image provider '{key}' not available in this worker's registry")
        return self.image_providers[key]

    def get_text_provider(self, key: str) -> ITextProvider:
        if key not in self.text_providers:
            raise RuntimeError(f"Text provider '{key}' not available in this worker's registry")
        return self.text_providers[key]

    def get_channel(self, key: str) -> IDistributionChannel:
        if key not in self.channels:
            raise RuntimeError(f"Channel '{key}' not available in this worker's registry")
        return self.channels[key]

    async def shutdown(self):
        if self.message_broker:
            await self.message_broker.close()
        if self.database:
            await self.database.close()