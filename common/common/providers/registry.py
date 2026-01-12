from asyncio import constants
from common.app_logger import AppLogger
from common.contracts import IDatabase, IImageProvider, ITextProvider, IDistributionChannel, IMessageBroker   

class ProviderRegistry:
    def __init__(self
                , image_providers: dict[str, IImageProvider]
                , text_providers: dict[str, ITextProvider]
                , distribution_channels: dict[str, IDistributionChannel]
                , message_broker: IMessageBroker
                , database: IDatabase
                ):
        
        if image_providers is None:
            raise ValueError("image_providers cannot be None")
        if text_providers is None:
            raise ValueError("text_providers cannot be None")
        if distribution_channels is None:
            raise ValueError("distribution_channels cannot be None")
        if message_broker is None:
            raise ValueError("message_broker cannot be None")
        if database is None:
            raise ValueError("database cannot be None")
        
        self.image_providers = image_providers
        self.text_providers = text_providers
        self.channels = distribution_channels
        self.message_broker = message_broker
        self.database = database

    def get_image_provider(self, key: str) -> IImageProvider:
        if key not in self.image_providers:
            raise KeyError(f"Image provider with key '{key}' not found.")
        
        provider: IImageProvider = self.image_providers.get(key)
        return provider 

    def get_text_provider(self, key: str) -> ITextProvider:
        if key not in self.text_providers:
            raise KeyError(f"Text provider with key '{key}' not found.")
        
        provider: ITextProvider = self.text_providers.get(key)
        return provider 

    def get_channel(self, key: str) -> IDistributionChannel:
        if key not in self.channels:
            raise KeyError(f"Distribution channel with key '{key}' not found.")
        
        provider: IDistributionChannel = self.channels.get(key)
        return provider 

    def get_message_broker(self) -> IMessageBroker:
        return self.message_broker

    def get_database(self) -> IDatabase:
        return self.database