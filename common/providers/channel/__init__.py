from abc import ABC, abstractmethod

class IChannel(ABC):
    @abstractmethod
    def post(self, title: str, description: str, image_url: str, **kwargs) -> bool:
        pass
