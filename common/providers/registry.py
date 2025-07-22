from typing import Type

from .base import IImageProvider, ITextProvider, IChannel
from .image.unsplash import UnsplashImageProvider
from .model.openai import OpenAITextProvider
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
    cls: Type[IImageProvider] = _image_providers[key]
    return cls()


def get_text_provider(key: str) -> ITextProvider:
    cls: Type[ITextProvider] = _text_providers[key]
    return cls()


def get_channel(key: str) -> IChannel:
    cls: Type[IChannel] = _channels[key]
    return cls()
