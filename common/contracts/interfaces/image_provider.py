from abc import ABC, abstractmethod
from .base_provider_with_name import IBaseProviderWithName

class IImageProvider(ABC, IBaseProviderWithName):
    @abstractmethod
    def fetch_image(self, keyword: str) -> str:
        pass
