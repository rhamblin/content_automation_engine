from abc import ABC, abstractmethod

class IImageProvider(ABC):
    @abstractmethod
    def fetch_image(self, keyword: str) -> str:
        pass
