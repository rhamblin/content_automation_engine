from .image import IImageProvider
from .text import ITextProvider
from .channel import IChannel
from ..constants import constants

class ProviderRegistry:
    def __init__(self
                , image_providers
                , text_providers
                , channels
                ):
        self.image_providers = image_providers
        self.text_providers = text_providers
        self.channels = channels

    def get_image_provider(self) -> IImageProvider:
        provider: IImageProvider = self.image_providers.get(constants.IMAGE_PROVIDER_AZURE_BLOB_STORAGE)
        return provider 

    def get_text_provider(self) -> ITextProvider:
        provider: ITextProvider = self.text_providers.get(constants.TEXT_PROVIDER_AZURE_FOUNDRY)
        return provider 

    def get_channel(self, key: str) -> IChannel:
        default_provider = self.channels.get(constants.CHANNEL_PINTEREST)
        provider: IChannel = self.channels.get(key, default_provider)
        return provider 