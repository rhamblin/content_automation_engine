from typing import Type

from .base import IImageProvider, ITextProvider, IChannel
from .image.unsplash import UnsplashImageProvider
from .text.openai import OpenAITextProvider
from .channel.pinterest import PinterestChannel


_image_providers = {
    "unsplash": UnsplashImageProvider,
}

_text_providers = {
    "openai": OpenAITextProvider,
}

_channels = {
    "pinterest": PinterestChannel,
}


def get_image_provider(key: str) -> IImageProvider:
    # Retrieve the provider class from the registry (not an instance)
    cls: Type[IImageProvider] = _image_providers[key]
    return cls() #returns an instance of the class


def get_text_provider(key: str) -> ITextProvider:
    # Retrieve the provider class from the registry (not an instance)
    cls: Type[ITextProvider] = _text_providers[key]
    return cls() #returns an instance of the class


def get_channel(key: str) -> IChannel:
    # Retrieve the provider class from the registry (not an instance)
    cls: Type[IChannel] = _channels[key]
    return cls() #returns an instance of the class
