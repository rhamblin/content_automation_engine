from typing import Type

from .base import IImageProvider, IModelProvider, IChannel
from .image.openai_image import OpenAIImageProvider
from .model.openai_text import OpenAIModelProvider
from .channel.pinterest import PinterestChannel

_image_providers = {
    "openai_image": OpenAIImageProvider,
}

_model_providers = {
    "openai_text": OpenAIModelProvider,
}

_channels = {
    "pinterest": PinterestChannel,
}


def get_image_provider(key: str) -> IImageProvider:
    cls: Type[IImageProvider] = _image_providers[key]
    return cls()


def get_model_provider(key: str) -> IModelProvider:
    cls: Type[IModelProvider] = _model_providers[key]
    return cls()


def get_channel(key: str) -> IChannel:
    cls: Type[IChannel] = _channels[key]
    return cls()
