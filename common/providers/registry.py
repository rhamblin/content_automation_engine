from typing import Type

from .base import IImageProvider, ITextProvider, IChannel
from .image.source_image import SourceImageProvider
from .model.openai_text import OpenAITextProvider
from .channel.pinterest import PinterestChannel


_image_providers = {
    "source_image": SourceImageProvider,
}

_text_providers = {
    "openai_text": OpenAITextProvider,
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
