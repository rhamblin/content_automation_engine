from abc import ABC, abstractmethod
from .base_provider_with_name import IBaseProviderWithName

class IDistributionChannel(ABC, IBaseProviderWithName):
    @abstractmethod
    def publish(self, title: str, description: str, image_url: str, **kwargs) -> bool:
        pass
