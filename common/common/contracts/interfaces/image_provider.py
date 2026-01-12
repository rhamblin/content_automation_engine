from abc import abstractmethod
from .base_provider_with_name import IBaseProviderWithName

class IImageProvider(IBaseProviderWithName):
    @abstractmethod
    def fetch_image(self, keyword: str) -> str:
        pass
