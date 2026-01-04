from abc import ABC, abstractmethod

class IImageProvider(ABC):
    @abstractmethod
    def fetch_image(self, niche: str, keyword: str) -> str:
        pass
