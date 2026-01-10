from abc import ABC, abstractmethod

class IDistributionChannel(ABC):
    @abstractmethod
    def publish(self, title: str, description: str, image_url: str, **kwargs) -> bool:
        pass
