from typing import Type

from .base import IImageProvider, ITextProvider, IChannel
from ..db_core.models import Keyword, KeywordImageMatchConfidence
from .image.unsplash import UnsplashImageProvider
from .image.azure_blob_storage import AzureBlobStorageImageProvider
from .text.azure_foundry import AzureFoundryTextProvider
from .channel.pinterest import PinterestChannel

def get_image_provider(keyword: Keyword) -> IImageProvider:
    cls: Type[IImageProvider] = UnsplashImageProvider

    if keyword.keyword_image_match_confidence == KeywordImageMatchConfidence.low:
        cls = AzureBlobStorageImageProvider

    return cls() #returns an instance of the class

def get_text_provider(key: str) -> ITextProvider:
    text_providers = {
        "azure_foundry": AzureFoundryTextProvider,
    }

    # Retrieve the provider class from the registry (not an instance)
    cls: Type[ITextProvider] = text_providers.get(key, AzureFoundryTextProvider)

    return cls() #returns an instance of the class


def get_channel(key: str) -> IChannel:
    channels = {
        "pinterest": PinterestChannel,
    }

    # Retrieve the provider class from the registry (not an instance)
    cls: Type[IChannel] = channels.get(key, PinterestChannel)

    return cls() #returns an instance of the class
