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

def get_image_provider(key: str):
    provider_cls = _image_providers.get(key)
    return provider_cls() if provider_cls else None

def get_model_provider(key: str):
    provider_cls = _model_providers.get(key)
    return provider_cls() if provider_cls else None

def get_channel(key: str):
    channel_cls = _channels.get(key)
    return channel_cls() if channel_cls else None
