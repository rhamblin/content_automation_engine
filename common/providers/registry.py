from common.contracts import IDatabase, IImageProvider, ITextProvider, IDistributionChannel, IMessageConsumer, IMessagePublisher   
from ..constants import constants

class ProviderRegistry:
    def __init__(self
                , image_providers: dict[str, IImageProvider]
                , text_providers: dict[str, ITextProvider]
                , distribution_channels: dict[str, IDistributionChannel]
                , message_consumer: IMessageConsumer
                , message_publisher: IMessagePublisher
                , database: IDatabase
                ):
        self.image_providers = image_providers
        self.text_providers = text_providers
        self.channels = distribution_channels
        self.message_consumer = message_consumer
        self.message_publisher = message_publisher
        self.database = database

    def get_image_provider(self) -> IImageProvider:
        provider: IImageProvider = self.image_providers.get(constants.IMAGE_PROVIDER_AZURE_BLOB_STORAGE)
        return provider 

    def get_text_provider(self) -> ITextProvider:
        provider: ITextProvider = self.text_providers.get(constants.TEXT_PROVIDER_AZURE_FOUNDRY)
        return provider 

    def get_channel(self, key: str) -> IDistributionChannel:
        default_provider = self.channels.get(constants.CHANNEL_PINTEREST)
        provider: IDistributionChannel = self.channels.get(key, default_provider)
        return provider 

    def get_message_consumer(self) -> IMessageConsumer:
        return self.message_consumer
    
    def get_message_publisher(self) -> IMessagePublisher:
        return self.message_publisher
    
    def get_database(self) -> IDatabase:
        return self.database